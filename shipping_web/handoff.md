# Shipping Web — 작업 인수인계 문서

## 프로젝트 개요

기존 `shipping_doc_automation` Python 프로젝트(CI→PL 변환)를 웹으로 확장한 애플리케이션.
고객이 CI Excel 파일을 업로드하면 포장 결과(케이스별 reason 포함)를 웹에서 확인하고,
컨테이너 적재 시뮬레이션을 3D로 시각화할 수 있음.

**기술 스택:** FastAPI (백엔드) + Vue 3 + Vite (프론트엔드) + Three.js (3D)

---

## 구현 완료 항목

### Phase 1: 백엔드 기반 구축
- `backend/main.py` — FastAPI 앱 진입점, CORS 설정, `shipping_doc_automation` 모듈 sys.path 연동
- `backend/api/schemas.py` — Pydantic 요청/응답 모델 (UploadResponse, ContainerLoadResponse 등)
- `backend/api/routes.py` — 4개 API 엔드포인트:
  - `POST /api/upload` — CI Excel 업로드 → 파이프라인 실행 → JSON 결과
  - `GET /api/result/{result_id}` — 캐시된 결과 조회
  - `GET /api/download-pl/{result_id}` — PL Excel 다운로드
  - `POST /api/container-load/{result_id}` — 컨테이너 적재 시뮬레이션
- `backend/services/packing_service.py` — 기존 파이프라인 래핑 (parse_ci → classify → pack → validate)
  - 메모리 캐시로 result_id 기반 결과 저장
  - PL Excel 생성 기능 포함

### Phase 2: 컨테이너 적재 알고리즘
- `backend/services/container_loading_service.py` — Layer-based Greedy 알고리즘
  - 컨테이너 3종 규격: 20ft / 40ft / 40ft HC
  - 높이 내림차순 정렬 → 레이어 그룹핑(±50mm) → Shelf 2D 배치 → 적층
  - 양방향 회전(L×W, W×L) 시도
  - 부피/중량 활용률 계산
  - 각 케이스의 3D 좌표(x,y,z), 배치 치수, 회전 여부, 레이어 인덱스 출력

### Phase 3: 프론트엔드 셋업
- Vue 3 + Vite + Pinia + Axios + Three.js
- `frontend/src/api/client.js` — Axios API 클라이언트 (upload, getResult, downloadPL, loadContainer)
- `frontend/src/stores/packingStore.js` — Pinia 상태 관리 (packingResult, containerResult, loading, error)
- `frontend/src/components/FileUpload.vue` — 드래그앤드롭 파일 업로드, 로딩 스피너
- `frontend/src/components/ResultSummary.vue` — 요약 카드 (케이스 수/수량/중량/CBM/검증상태), 카테고리 배지, PL 다운로드
- `frontend/src/components/CaseTable.vue` — 케이스 테이블 (reason 강조 배경, 행 펼침 상세, 카테고리 색상 배지)

### Phase 4: 3D 시각화
- `frontend/src/utils/containerScene.js` — Three.js 씬/카메라/렌더러/OrbitControls/Raycaster 통합 클래스
- `frontend/src/components/ContainerView3D.vue` — 3D 캔버스 + 활용률 표시 + 카테고리 범례
- `frontend/src/components/CaseTooltip.vue` — 케이스 클릭 시 상세 정보 (reason 강조 표시)
- `frontend/src/components/ContainerSelector.vue` — 3종 컨테이너 라디오 선택 + 시뮬레이션 실행 버튼

### Phase 5: 통합
- `frontend/src/App.vue` — 전체 사용자 흐름 조합 (업로드→결과→컨테이너→3D)
- `frontend/src/utils/colors.js` — 카테고리별 색상 매핑 (VCB=파랑, ACB_HGS=초록, MCCB=주황 등)
- `vite.config.js` — 프록시 설정 (`/api` → `localhost:8000`)
- 에러 배너, 새 파일 분석 리셋 기능

---

## 프로젝트 파일 구조

```
shipping_web/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── packing_service.py
│   │   └── container_loading_service.py
│   └── storage/                         # 런타임 (uploads/, results/)
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api/
│       │   └── client.js
│       ├── stores/
│       │   └── packingStore.js
│       ├── components/
│       │   ├── FileUpload.vue
│       │   ├── ResultSummary.vue
│       │   ├── CaseTable.vue
│       │   ├── ContainerSelector.vue
│       │   ├── ContainerView3D.vue
│       │   └── CaseTooltip.vue
│       └── utils/
│           ├── colors.js
│           └── containerScene.js
├── README.md
└── handoff.md
```

---

## 실행 방법

```bash
# 백엔드 (터미널 1)
cd shipping_web/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 프론트엔드 (터미널 2)
cd shipping_web/frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속.

---

## 검증 결과

| 항목 | 결과 |
|------|------|
| 프론트엔드 빌드 | 성공 (vite build) |
| 백엔드 라우트 등록 | 4개 API + health 정상 |
| 샘플 파일 파이프라인 | 32 케이스, validation PASS |
| reason 필드 | 정상 출력 (예: "VCB 개별포장: 1대/케이스 규칙") |
| 컨테이너 적재 | 40ft 기준 24/32 배치, 부피 43.7%, 중량 24.3% |
| 서버 기동 | 백엔드 8000, 프론트엔드 5173 정상 |

---

## 기존 프로젝트 연동

`backend/main.py`에서 `sys.path`에 `shipping_doc_automation` 루트를 추가하여 기존 모듈 직접 import:
- `src.parser.ci_parser.parse_ci`
- `src.classifier.product_classifier.classify_document`
- `src.packing.strategy_selector.select_and_pack`
- `src.generator.pl_generator.generate_pl_excel`
- `src.validation.pl_validator.validate_pl`

---

## 향후 작업 (미구현)

- E2E 테스트 자동화 (5개 샘플 파일)
- 에러 핸들링 세밀화 (파싱 실패, 빈 파일 등)
- 결과 캐시 만료 정책 (현재 메모리 무한 보관)
- 프로덕션 배포 설정 (Docker, nginx 등)
- 스타일 미세 조정 (반응형, 모바일 대응)
