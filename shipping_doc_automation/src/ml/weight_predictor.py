"""ML 기반 중량 예측기

GradientBoostingRegressor로 미등록 제품의 중량을 예측.
학습 데이터: product_db.json + PL 파싱 결과에서 추출한 (모델번호, 중량) 쌍

과적합 방지 전략:
1. log 변환: 타겟(중량)에 log 적용하여 0.14~200kg 범위를 정규화
2. 모델 단순화: n_estimators↓, max_depth↓, min_samples_leaf↑
3. 정규화: subsample으로 확률적 경사 부스팅 (Stochastic GB)
4. 피처 정리: 중복 피처 제거 (7→5개)
5. CV 기반 평가: train 성능이 아닌 CV 성능 리포트
"""
import json
import pickle
from pathlib import Path
from typing import Optional

import numpy as np

from src.ml.feature_extractor import extract_features_vector, FEATURE_NAMES
from config.settings import PRODUCT_DB_PATH, DATA_DIR

MODEL_PATH = DATA_DIR / "weight_model.pkl"


class WeightPredictor:
    """ML 기반 중량 예측기"""

    def __init__(self):
        self.model = None
        self.is_trained = False

    def train(self, training_data: list) -> dict:
        """학습 데이터로 모델 훈련 (log-transformed target)

        Args:
            training_data: list of (model_number, weight_kg)

        Returns:
            {
                'r2_train': float, 'r2_cv': float,
                'mae_train': float, 'mae_cv': float,
                'n_samples': int, 'overfit_gap': float,
            }
        """
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.model_selection import cross_val_score

        if len(training_data) < 5:
            return {
                'r2_train': 0, 'r2_cv': 0,
                'mae_train': 0, 'mae_cv': 0,
                'n_samples': len(training_data), 'overfit_gap': 0,
            }

        X = np.array([extract_features_vector(mn) for mn, _ in training_data])
        y = np.array([w for _, w in training_data])

        # 핵심: log 변환으로 타겟 스케일 정규화
        # 0.14kg~200kg → log 범위 ~-1.97 ~ 5.30 (균일한 분포)
        y_log = np.log(y + 1e-6)

        # 과적합 방지 하이퍼파라미터
        self.model = GradientBoostingRegressor(
            n_estimators=30,          # 100→30: 트리 수 대폭 축소
            max_depth=2,              # 4→2: 각 트리의 복잡도 제한
            learning_rate=0.1,        # 동일: 학습률
            min_samples_leaf=3,       # 추가: 리프 최소 샘플 3개 보장
            min_samples_split=5,      # 추가: 분할 최소 샘플 5개
            subsample=0.8,            # 추가: 80% 서브샘플링 (Stochastic GB)
            random_state=42,
        )
        self.model.fit(X, y_log)
        self.is_trained = True

        # Train 성능 (원래 스케일로 역변환)
        pred_log = self.model.predict(X)
        pred = np.exp(pred_log)
        mae_train = np.mean(np.abs(pred - y))
        r2_train = 1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)

        # Cross-Validation 성능 (일반화 성능)
        n_cv = min(5, len(training_data))
        cv_r2 = cross_val_score(self.model, X, y_log, cv=n_cv, scoring='r2')
        cv_neg_mae = cross_val_score(self.model, X, y_log, cv=n_cv,
                                      scoring='neg_mean_absolute_error')

        # CV MAE를 원래 스케일로 근사 변환
        cv_mae_log = -cv_neg_mae.mean()
        # log 공간의 MAE → 원래 공간 근사: exp(mean_log_y + mae) - exp(mean_log_y)
        mean_log_y = y_log.mean()
        mae_cv_approx = np.exp(mean_log_y + cv_mae_log) - np.exp(mean_log_y)

        overfit_gap = r2_train - cv_r2.mean()

        return {
            'r2_train': round(float(r2_train), 4),
            'r2_cv': round(float(cv_r2.mean()), 4),
            'mae_train': round(float(mae_train), 4),
            'mae_cv': round(float(mae_cv_approx), 4),
            'n_samples': len(training_data),
            'overfit_gap': round(float(overfit_gap), 4),
        }

    def predict(self, model_number: str) -> Optional[float]:
        """미등록 제품 중량 예측 (log 역변환)"""
        if not self.is_trained or self.model is None:
            return None

        features = np.array([extract_features_vector(model_number)])
        pred_log = self.model.predict(features)[0]
        prediction = np.exp(pred_log)  # log 역변환
        return max(0.01, round(float(prediction), 2))

    def save(self, path: Optional[str] = None):
        """모델 저장"""
        save_path = Path(path) if path else MODEL_PATH
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'wb') as f:
            pickle.dump(self.model, f)

    def load(self, path: Optional[str] = None) -> bool:
        """모델 로드"""
        load_path = Path(path) if path else MODEL_PATH
        if not load_path.exists():
            return False
        with open(load_path, 'rb') as f:
            self.model = pickle.load(f)
        self.is_trained = True
        return True

    @staticmethod
    def build_training_data_from_db() -> list:
        """product_db.json에서 학습 데이터 추출"""
        with open(PRODUCT_DB_PATH, 'r') as f:
            db = json.load(f)

        training_data = []
        for category, products in db.items():
            if category.startswith('_') or category == 'case_specs':
                continue
            if not isinstance(products, dict):
                continue

            for model_key, spec in products.items():
                if model_key.startswith('_') or 'DEFAULT' in model_key:
                    continue
                if isinstance(spec, dict) and 'unit_weight_kg' in spec:
                    training_data.append((model_key, spec['unit_weight_kg']))

        return training_data


def predict_gross_weight(net_weight: float, case_type: str, n_items: int = 1) -> float:
    """총중량(Gross) 예측: 순중량 + 케이스 중량

    간단한 규칙 기반:
    - WOODEN CASE: 순중량 * 1.15 ~ 1.25
    - PALLET: 순중량 + 30 (팔레트 + 랩)
    """
    if case_type == "WOODEN CASE":
        if net_weight < 50:
            return round(net_weight * 1.25, 0)
        elif net_weight < 200:
            return round(net_weight * 1.20, 0)
        else:
            return round(net_weight * 1.15, 0)
    elif case_type == "PALLET":
        return round(net_weight + 30, 0)
    else:
        return round(net_weight * 1.15, 0)
