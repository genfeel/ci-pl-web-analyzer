# 선적서류 웹 애플리케이션 구현 계획

## Context

기존 `shipping_doc_automation` Python 프로젝트(CI→PL 변환)를 웹으로 확장.
고객이 CI Excel 파일을 업로드하면 포장 결과(케이스별 reason 포함)를 웹에서 확인하고,
컨테이너 적재 시뮬레이션을 3D로 시각화할 수 있도록 함.

**기술 스택:** FastAPI (백엔드) + Vue 3 + Vite (프론트엔드) + Three.js (3D)
**프로젝트 위치:** `/Users/genfeel/Dev/선적서류고도화_개발사항/shipping_web/` (별도 프로젝트)

---

## 프로젝트 구조

```
shipping_web/
├── backend/
│   ├── main.py                          # FastAPI 앱 진입점, CORS
│   ├── requirements.txt
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py                    # API 엔드포인트
│   │   └── schemas.py                   # Pydantic 요청/응답 모델
│   ├── services/
│   │   ├── __init__.py
│   │   ├── packing_service.py           # CI→PL 파이프라인 래핑
│   │   └── container_loading_service.py # 컨테이너 적재 알고리즘
│   └── storage/                         # 런타임 디렉토리 (uploads/, results/)
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js                      # Vue 앱 부트스트랩
│       ├── App.vue                      # 루트 컴포넌트
│       ├── api/
│       │   └── client.js               # Axios API 클라이언트
│       ├── stores/
│       │   └── packingStore.js          # Pinia 상태 관리
│       ├── components/
│       │   ├── FileUpload.vue           # 드래그앤드롭 파일 업로드
│       │   ├── ResultSummary.vue        # 요약 카드 (총 수량/중량/CBM)
│       │   ├── CaseTable.vue            # 케이스 테이블 (reason 컬럼 포함)
│       │   ├── ContainerSelector.vue    # 컨테이너 타입 선택
│       │   ├── ContainerView3D.vue      # Three.js 3D 뷰
│       │   └── CaseTooltip.vue          # 케이스 클릭 시 상세 툴팁
│       └── utils/
│           ├── colors.js                # 카테고리→색상 매핑
│           └── containerScene.js        # Three.js 씬 로직
└── README.md
```

---

## 백엔드 설계

### API 엔드포인트 (4개)

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/upload` | CI Excel 업로드 → 파이프라인 실행 → JSON 결과 반환 |
| GET | `/api/result/{result_id}` | 캐시된 결과 조회 |
| GET | `/api/download-pl/{result_id}` | PL Excel 파일 다운로드 |
| POST | `/api/container-load/{result_id}` | 컨테이너 적재 시뮬레이션 실행 |

### 기존 모듈 연동 방식

`sys.path`에 `shipping_doc_automation` 루트를 추가하여 기존 모듈 직접 import.
(기존 `cli/main.py`와 동일한 패턴)

```python
# backend/main.py에서
AUTOMATION_ROOT = Path(__file__).parent.parent.parent / "shipping_doc_automation"
sys.path.insert(0, str(AUTOMATION_ROOT))

# 이후 기존 모듈 사용
from src.parser.ci_parser import parse_ci
from src.classifier.product_classifier import classify_document
from src.packing.strategy_selector import select_and_pack
from src.generator.pl_generator import generate_pl_excel
```

### packing_service.py — 파이프라인 래핑

기존 `cli/main.py`의 generate 명령 흐름을 그대로 재사용:
1. `parse_ci(filepath)` → CIDocument
2. `classify_document(ci_doc)` → 분류된 CIDocument
3. `select_and_pack(ci_doc)` → List[PackedCase]
4. `validate_pl(ci_doc, cases)` → ValidationResult
5. 결과를 메모리 캐시에 저장 (result_id → data)
6. JSON 응답 구성 (cases 배열에 **reason 필드 포함**)

### container_loading_service.py — Layer-based Greedy 적재 알고리즘

**컨테이너 규격 (내부 치수, mm):**

| 타입 | 길이 | 폭 | 높이 | 최대 적재중량 |
|------|------|-----|------|------------|
| 20ft | 5,898 | 2,352 | 2,393 | 21,770kg |
| 40ft | 12,032 | 2,352 | 2,393 | 26,680kg |
| 40ft HC | 12,032 | 2,352 | 2,698 | 26,460kg |

**알고리즘 흐름:**

1. **정렬**: 케이스를 높이 내림차순 정렬
2. **레이어 그룹핑**: 유사 높이(±50mm) 케이스를 같은 레이어로 묶음
3. **2D 배치**: 각 레이어 내에서 바닥 면적 내림차순으로 Shelf 알고리즘 배치
   - 양방향 회전(L×W, W×L) 시도 → 더 잘 맞는 방향 선택
4. **레이어 적층**: 아래→위로 레이어를 쌓음 (높이 초과 시 미배치 처리)
5. **중량 체크**: 총 중량이 max_payload 초과 시 초과분 미배치 처리
6. **활용률 계산**: 부피 활용률(%), 중량 활용률(%)

**출력 데이터**: 각 케이스의 3D 좌표(x,y,z), 배치 치수, 회전 여부, 레이어 인덱스

### API 응답 스키마 (핵심)

```python
class PackedCaseResponse:
    case_no: int
    case_type: str          # "WOODEN CASE" / "PALLET"
    category: str           # "VCB", "ACB_HGS", ...
    reason: str             # ★ 포장 사유 (필수 표시)
    total_quantity: int
    net_weight: float
    gross_weight: float
    dimensions: [L, W, H]   # mm
    cbm: float
    items: [PackedItemResponse]

class ContainerLoadResponse:
    container_type: str
    container_dims: [L, W, H]
    placed_cases: [{case_no, position:[x,y,z], dimensions:[L,W,H], rotated, category, reason, layer_index}]
    unplaced_cases: [case_no]
    volume_utilization_pct: float
    weight_utilization_pct: float
```

---

## 프론트엔드 설계

### 사용자 흐름

```
1. 파일 업로드 (드래그앤드롭)
       ↓
2. 분석 결과 대시보드
   ├─ 요약 카드 (케이스 수, 수량, 중량, CBM, 검증 결과)
   ├─ 케이스 테이블 (reason 컬럼 강조 표시)
   └─ PL 엑셀 다운로드 버튼
       ↓
3. 컨테이너 선택 (20ft / 40ft / 40ft HC)
       ↓
4. 3D 적재 시각화
   ├─ Three.js 인터랙티브 뷰 (회전/줌/팬)
   ├─ 카테고리별 색상 범례
   ├─ 활용률 표시 (부피%, 중량%)
   └─ 케이스 클릭 → 상세 툴팁 (reason 포함)
```

### 주요 컴포넌트

**FileUpload.vue** — `.xls/.xlsx` 드래그앤드롭 업로드, 로딩 스피너

**ResultSummary.vue** — 요약 카드 그리드:
- 총 케이스 수 / 총 수량 / 순중량 / 총중량 / CBM / 검증상태
- 카테고리별 요약 (색상 배지)
- PL 다운로드 버튼

**CaseTable.vue** — 케이스별 상세 테이블:

| Case | Type | Category | Items | Qty | N.W | G.W | Dims | CBM | **Reason** |
|------|------|----------|-------|-----|-----|-----|------|-----|-----------|

- **Reason 컬럼**: 넓은 폭, 좌측 정렬, 강조 배경색
- 행 펼침 시 해당 케이스 내 품목 상세 표시
- 카테고리별 색상 배지 (3D 뷰와 동일 색상)

**ContainerSelector.vue** — 3종 컨테이너 라디오 버튼 + "적재 시뮬레이션" 버튼

**ContainerView3D.vue + containerScene.js** — Three.js 3D 시각화:
- 컨테이너 와이어프레임 + 반투명 바닥
- 카테고리별 색상 코딩된 박스 (VCB=파랑, ACB=초록, MCCB=주황 등)
- OrbitControls (마우스 회전/줌/팬)
- Raycaster 클릭 이벤트 → CaseTooltip 표시

**CaseTooltip.vue** — 클릭된 케이스 상세:
- Case No, Type, Category (색상 배지)
- 품목 리스트, 중량, 치수
- **★ Reason (강조 표시)**

### 카테고리별 색상

| Category | 색상 | Hex |
|----------|------|-----|
| VCB | 파랑 | #2196F3 |
| ACB_HGS | 초록 | #4CAF50 |
| ACB_LARGE | 틸 | #009688 |
| MCCB | 주황 | #FF9800 |
| MC | 보라 | #9C27B0 |
| RELAY | 빨강 | #F44336 |
| SPARE | 갈색 | #795548 |

### 상태 관리 (Pinia)

```javascript
// packingStore.js
state: {
  packingResult,      // 업로드 결과 (cases + validation)
  containerResult,    // 컨테이너 적재 결과
  loading, error,
  selectedContainerType
}
actions: {
  uploadFile(file),    // POST /api/upload
  loadContainer(type), // POST /api/container-load/{id}
  downloadPL()         // GET /api/download-pl/{id}
}
```

---

## 구현 순서

### Phase 1: 백엔드 기반 구축
1. `shipping_web/backend/` 디렉토리 구조 생성
2. `main.py` — FastAPI 앱 + CORS + sys.path 설정
3. `services/packing_service.py` — 기존 파이프라인 래핑
4. `api/schemas.py` — Pydantic 모델 정의
5. `api/routes.py` — upload, result, download-pl 엔드포인트
6. 샘플 CI 파일로 API 테스트

### Phase 2: 컨테이너 적재 알고리즘
7. `services/container_loading_service.py` — Layer-based Greedy 구현
8. `api/routes.py`에 container-load 엔드포인트 추가
9. 알고리즘 검증 테스트

### Phase 3: 프론트엔드 셋업
10. Vue 3 + Vite 프로젝트 초기화 (`frontend/`)
11. 의존성 설치 (vue, pinia, axios, three)
12. `vite.config.js` 프록시 설정
13. Pinia 스토어 구현
14. `FileUpload.vue`, `ResultSummary.vue`, `CaseTable.vue` 구현

### Phase 4: 3D 시각화
15. `containerScene.js` — Three.js 씬/카메라/렌더러/컨트롤
16. `ContainerView3D.vue` — 캔버스 호스팅 + 범례 + 활용률
17. `CaseTooltip.vue` — 클릭 상세정보
18. `ContainerSelector.vue` — 타입 선택 UI
19. `App.vue`에서 전체 조합

### Phase 5: 통합 테스트
20. 5개 샘플 파일로 E2E 테스트
21. 에러 핸들링 및 로딩 상태 처리
22. 스타일 정리

---

## 검증 방법

1. **백엔드 단독**: `uvicorn backend.main:app --reload --port 8000` 후 curl/httpie로 API 테스트
2. **프론트엔드 단독**: `cd frontend && npm run dev` 후 브라우저 확인
3. **E2E**: 샘플 CI 파일 업로드 → 결과 확인 → reason 표시 확인 → PL 다운로드 → 컨테이너 3D 확인
4. **참조 파일**: `shipping_doc_automation/data/samples/` 내 5개 샘플 파일 사용

---

## 핵심 참조 파일 (기존 프로젝트)

- `src/models/data_models.py` — PackedCase, CIDocument, PLDocument 데이터 모델
- `cli/main.py` — generate 명령 (파이프라인 흐름 참조, L44~L117)
- `src/packing/strategy_selector.py` — 포장 오케스트레이터
- `config/packing_constraints.py` — 케이스/팔레트 치수, 중량 제한
- `src/generator/pl_generator.py` — PL 엑셀 생성기
- `src/validation/pl_validator.py` — CI↔PL 검증
