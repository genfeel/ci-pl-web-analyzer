# CI→PL 선적서류 웹 분석기

CI(Commercial Invoice) Excel 파일을 업로드하면 포장 결과를 분석하고,
컨테이너 적재 시뮬레이션을 3D로 시각화하는 웹 애플리케이션입니다.

---

## 목차

1. [사전 준비 (필수 프로그램 설치)](#1-사전-준비-필수-프로그램-설치)
2. [프로젝트 클론](#2-프로젝트-클론)
3. [shipping_doc_automation 설치](#3-shipping_doc_automation-설치-ci→pl-변환-엔진)
4. [shipping_web 백엔드 설치](#4-shipping_web-백엔드-설치)
5. [shipping_web 프론트엔드 설치](#5-shipping_web-프론트엔드-설치)
6. [서버 실행하기](#6-서버-실행하기)
7. [정상 작동 확인하기](#7-정상-작동-확인하기)
8. [사용 방법 (화면 가이드)](#8-사용-방법-화면-가이드)
9. [프로젝트 구조](#9-프로젝트-구조)
10. [자주 발생하는 문제 (FAQ)](#10-자주-발생하는-문제-faq)
11. [개발 참고 사항](#11-개발-참고-사항)

---

## 1. 사전 준비 (필수 프로그램 설치)

아래 프로그램들이 설치되어 있어야 합니다. 터미널(맥) 또는 명령 프롬프트(윈도우)에서 버전을 확인하세요.

### 1-1. Python 3.10 이상

```bash
python3 --version
# 출력 예: Python 3.11.9
```

**설치 안 되어 있다면:**
- macOS: `brew install python@3.11`
- Windows: https://www.python.org/downloads/ 에서 다운로드 (설치 시 "Add to PATH" 반드시 체크)

### 1-2. Node.js 18 이상 + npm

```bash
node --version
# 출력 예: v24.13.1

npm --version
# 출력 예: 11.8.0
```

**설치 안 되어 있다면:**
- macOS: `brew install node`
- Windows: https://nodejs.org/ 에서 LTS 버전 다운로드

### 1-3. Git

```bash
git --version
# 출력 예: git version 2.43.0
```

**설치 안 되어 있다면:**
- macOS: `brew install git`
- Windows: https://git-scm.com/downloads 에서 다운로드

---

## 2. 프로젝트 클론

```bash
# 원하는 작업 폴더로 이동
cd ~/Dev

# GitHub에서 프로젝트 클론
git clone https://github.com/genfeel/ci-pl-web-analyzer.git

# 프로젝트 폴더로 이동
cd ci-pl-web-analyzer
```

클론 후 폴더 구조가 아래와 같은지 확인하세요:

```
ci-pl-web-analyzer/
├── shipping_doc_automation/    ← CI→PL 변환 엔진 (Python)
├── shipping_web/               ← 웹 애플리케이션
│   ├── backend/                ← FastAPI 백엔드
│   └── frontend/               ← Vue 3 프론트엔드
└── .gitignore
```

---

## 3. shipping_doc_automation 설치 (CI→PL 변환 엔진)

이 프로젝트는 웹 백엔드가 내부적으로 사용하는 핵심 엔진입니다.
먼저 이 프로젝트의 Python 의존성을 설치해야 합니다.

### 3-1. 가상환경 생성 (권장)

프로젝트 루트(`ci-pl-web-analyzer/`)에서 실행합니다:

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
# macOS / Linux:
source venv/bin/activate

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Windows (cmd):
.\venv\Scripts\activate.bat
```

활성화되면 터미널 프롬프트 앞에 `(venv)`가 표시됩니다:
```
(venv) ~/Dev/ci-pl-web-analyzer $
```

> **중요:** 이후 모든 `pip install` 및 서버 실행 명령은 반드시 가상환경이 활성화된 상태에서 실행하세요.

### 3-2. 의존성 설치

```bash
pip install -r shipping_doc_automation/requirements.txt
```

**설치되는 주요 패키지:**

| 패키지 | 용도 |
|--------|------|
| `openpyxl` | .xlsx 엑셀 파일 읽기/쓰기 |
| `xlrd` | .xls (구형) 엑셀 파일 읽기 |
| `pandas` | 데이터 처리 |
| `scikit-learn` | ML 기반 중량 예측 |
| `click` | CLI 명령어 처리 |
| `pytest` | 테스트 |

### 3-3. 설치 확인

```bash
cd shipping_doc_automation
python3 -m cli.main --version
# 출력: 0.1.0
```

### 3-4. 샘플 파일로 CLI 테스트 (선택)

```bash
# shipping_doc_automation/ 폴더 안에서 실행
python3 -m cli.main generate "data/samples/25020325-CIPL_샘플.xls" -v
```

아래와 비슷한 출력이 나오면 정상입니다:
```
📄 CI 파일 파싱: 25020325-CIPL_샘플.xls
   품목 수: 45
   총 수량: 1479
📦 포장 전략 실행 중...
   케이스 수: 32
   총 순중량: 6998.80 kg
   총 총중량: 8038.80 kg
✅ 검증 중...
=== 검증 결과: PASS ===
📝 PL 엑셀 생성: output/25020325-CIPL_샘플_PL.xlsx
   ✓ 생성 완료
```

테스트 후 프로젝트 루트로 돌아갑니다:
```bash
cd ..
```

---

## 4. shipping_web 백엔드 설치

### 4-1. 의존성 설치

```bash
pip install -r shipping_web/backend/requirements.txt
```

**설치되는 주요 패키지:**

| 패키지 | 용도 |
|--------|------|
| `fastapi` | 웹 API 프레임워크 |
| `uvicorn` | ASGI 서버 (FastAPI 실행기) |
| `python-multipart` | 파일 업로드 처리 |

> 참고: `openpyxl`, `xlrd`는 3단계에서 이미 설치되었으므로 중복 설치되지 않습니다.

### 4-2. 설치 확인

```bash
python3 -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
# 출력 예: FastAPI 0.135.1

python3 -c "import uvicorn; print(f'Uvicorn {uvicorn.__version__}')"
# 출력 예: Uvicorn 0.41.0
```

---

## 5. shipping_web 프론트엔드 설치

### 5-1. 의존성 설치

```bash
cd shipping_web/frontend
npm install
```

성공하면 아래와 같은 메시지가 출력됩니다:
```
added 57 packages, and audited 58 packages in 7s
```

**설치되는 주요 패키지:**

| 패키지 | 용도 |
|--------|------|
| `vue` (3.4+) | UI 프레임워크 |
| `pinia` | Vue 상태 관리 |
| `axios` | HTTP API 클라이언트 |
| `three` | 3D 시각화 (Three.js) |
| `vite` | 개발 서버 + 빌드 도구 |

### 5-2. 설치 확인 (빌드 테스트)

```bash
npm run build
```

성공하면 아래와 같은 메시지가 출력됩니다:
```
vite v5.4.21 building for production...
✓ 95 modules transformed.
✓ built in 998ms
```

프로젝트 루트로 돌아갑니다:
```bash
cd ../..
```

---

## 6. 서버 실행하기

**터미널 2개**를 열어야 합니다. 하나는 백엔드, 하나는 프론트엔드용입니다.

### 6-1. 터미널 1: 백엔드 서버 실행

```bash
# 프로젝트 루트에서 시작
cd ci-pl-web-analyzer

# 가상환경 활성화 (이미 활성화되어 있으면 건너뛰기)
source venv/bin/activate   # macOS/Linux
# .\venv\Scripts\Activate.ps1   # Windows

# 백엔드 서버 실행
cd shipping_web/backend
uvicorn main:app --reload --port 8000
```

아래 메시지가 나오면 정상입니다:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Application startup complete.
```

> `--reload` 옵션: 코드 수정 시 서버가 자동으로 재시작됩니다 (개발 편의용).

### 6-2. 터미널 2: 프론트엔드 서버 실행

**새 터미널 창을 열고** 실행합니다:

```bash
cd ci-pl-web-analyzer/shipping_web/frontend
npm run dev
```

아래 메시지가 나오면 정상입니다:
```
  VITE v5.4.21  ready in 251 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### 6-3. 서버 종료하기

각 터미널에서 `Ctrl + C`를 누르면 서버가 종료됩니다.

---

## 7. 정상 작동 확인하기

두 서버가 모두 실행 중인 상태에서 아래 항목을 확인하세요.

### 7-1. 백엔드 헬스체크

브라우저에서 아래 주소를 엽니다:

```
http://localhost:8000/health
```

`{"status":"ok"}` 이 표시되면 백엔드 정상입니다.

### 7-2. API 문서 확인 (Swagger UI)

```
http://localhost:8000/docs
```

4개의 API 엔드포인트가 목록에 표시됩니다:
- `POST /api/upload`
- `GET /api/result/{result_id}`
- `GET /api/download-pl/{result_id}`
- `POST /api/container-load/{result_id}`

### 7-3. 프론트엔드 확인

```
http://localhost:5173
```

"Shipping Document Analyzer" 제목과 파일 업로드 영역이 표시되면 정상입니다.

### 7-4. E2E 테스트 (샘플 파일 업로드)

1. `http://localhost:5173` 접속
2. `shipping_doc_automation/data/samples/` 폴더의 샘플 파일을 드래그앤드롭
3. 분석 결과가 카드 + 테이블로 표시되는지 확인
4. "PL Excel 다운로드" 버튼 클릭 → `.xlsx` 파일 다운로드 확인
5. 컨테이너 타입 선택 후 "적재 시뮬레이션 실행" 클릭 → 3D 뷰 표시 확인

**사용 가능한 샘플 파일 (5개):**

| 파일명 | 설명 |
|--------|------|
| `25020325-CIPL_샘플.xls` | 단일 주문 (xls 형식) |
| `25021809-CIPL_샘플.xls` | 단일 주문 (xls 형식) |
| `25021818-1-CIPL_샘플.xlsx` | 단일 주문 (xlsx 형식) |
| `25022120-CIPL_샘플.xlsx` | 단일 주문 (xlsx 형식) |
| `25022297-1 25021874 25023500-CIPL_샘플.xlsx` | 합적(3건) 주문 |

---

## 8. 사용 방법 (화면 가이드)

### Step 1. 파일 업로드

- CI Excel 파일(.xls 또는 .xlsx)을 드래그앤드롭하거나 "파일 선택" 버튼으로 업로드
- 업로드 후 자동으로 분석이 시작됩니다 (로딩 스피너 표시)

### Step 2. 분석 결과 확인

분석이 완료되면 다음 정보가 표시됩니다:

- **요약 카드**: 총 케이스 수, 총 수량, 순중량, 총중량, CBM, 검증 상태(PASS/FAIL)
- **카테고리 배지**: 품목 카테고리별 색상 표시 (VCB=파랑, ACB=초록, MCCB=주황 등)
- **케이스 테이블**: 각 케이스의 상세 정보. **Reason 컬럼**에 포장 사유가 표시됩니다
  - 행을 클릭하면 해당 케이스에 포함된 품목 상세가 펼쳐집니다
- **PL Excel 다운로드**: 버튼을 클릭하면 PL 엑셀 파일이 다운로드됩니다

### Step 3. 컨테이너 적재 시뮬레이션

- 컨테이너 타입을 선택합니다 (20ft / 40ft / 40ft HC)
- "적재 시뮬레이션 실행" 버튼을 클릭합니다

### Step 4. 3D 시각화

- 컨테이너와 적재된 케이스가 3D로 표시됩니다
- **마우스 조작**: 왼쪽 드래그=회전, 스크롤=줌, 오른쪽 드래그=이동
- **케이스 클릭**: 해당 케이스의 상세 정보 툴팁이 표시됩니다 (Reason 포함)
- 상단에 부피/중량 활용률이 표시됩니다
- 하단에 카테고리별 색상 범례가 표시됩니다

### 새 파일 분석

- 우측 상단 "새 파일 분석" 버튼을 클릭하면 초기 화면으로 돌아갑니다

---

## 9. 프로젝트 구조

### 전체 구조

```
ci-pl-web-analyzer/
│
├── shipping_doc_automation/          ← CI→PL 변환 엔진 (Python CLI)
│   ├── cli/main.py                   # CLI 진입점 (generate/validate/compare)
│   ├── config/
│   │   ├── settings.py               # 전역 설정 (경로, 컬럼 매핑)
│   │   └── packing_constraints.py    # 포장 규칙 (케이스 치수, 중량 제한)
│   ├── src/
│   │   ├── parser/ci_parser.py       # CI 엑셀 파서
│   │   ├── classifier/product_classifier.py  # 제품 카테고리 분류기
│   │   ├── packing/
│   │   │   ├── strategy_selector.py  # 포장 전략 라우터
│   │   │   ├── vcb_packer.py         # VCB 포장기
│   │   │   ├── acb_packer.py         # ACB 포장기
│   │   │   └── mixed_pallet_packer.py # 혼합 팔레트 포장기
│   │   ├── generator/pl_generator.py # PL 엑셀 생성기
│   │   ├── validation/pl_validator.py # CI↔PL 검증기
│   │   └── models/data_models.py     # 데이터 모델 (CIDocument, PackedCase 등)
│   ├── data/
│   │   ├── samples/                  # CI 샘플 파일 5개
│   │   └── product_db.json           # 제품 DB (중량 정보)
│   ├── tests/                        # pytest 테스트
│   └── requirements.txt
│
├── shipping_web/                     ← 웹 애플리케이션
│   ├── backend/                      # FastAPI 백엔드 (Python)
│   │   ├── main.py                   # 앱 진입점 + CORS
│   │   ├── api/
│   │   │   ├── routes.py             # API 엔드포인트 4개
│   │   │   └── schemas.py            # Pydantic 요청/응답 모델
│   │   ├── services/
│   │   │   ├── packing_service.py    # CI→PL 파이프라인 래핑
│   │   │   └── container_loading_service.py  # 컨테이너 적재 알고리즘
│   │   ├── storage/                  # 런타임 파일 저장 (uploads/, results/)
│   │   └── requirements.txt
│   │
│   └── frontend/                     # Vue 3 프론트엔드
│       ├── index.html
│       ├── package.json
│       ├── vite.config.js            # Vite 설정 + API 프록시
│       └── src/
│           ├── main.js               # Vue 앱 부트스트랩
│           ├── App.vue               # 루트 컴포넌트 (전체 흐름)
│           ├── api/client.js         # Axios API 클라이언트
│           ├── stores/packingStore.js # Pinia 상태 관리
│           ├── components/
│           │   ├── FileUpload.vue     # 파일 업로드
│           │   ├── ResultSummary.vue  # 요약 카드
│           │   ├── CaseTable.vue      # 케이스 테이블
│           │   ├── ContainerSelector.vue  # 컨테이너 선택
│           │   ├── ContainerView3D.vue    # 3D 시각화
│           │   └── CaseTooltip.vue    # 케이스 클릭 툴팁
│           └── utils/
│               ├── colors.js          # 카테고리별 색상
│               └── containerScene.js  # Three.js 씬 관리
│
├── .gitignore
└── venv/                             # Python 가상환경 (git 제외)
```

### 데이터 흐름

```
[사용자: CI Excel 업로드]
        │
        ▼
[프론트엔드 (Vue 3)]  ──POST /api/upload──▶  [백엔드 (FastAPI)]
                                                     │
                                              ┌──────┴──────┐
                                              ▼             ▼
                                     [packing_service]  [container_loading_service]
                                              │             │
                                    ┌─────────┴─────────┐   │
                                    ▼                   ▼   ▼
                             [shipping_doc_automation]     [3D 좌표 계산]
                             CI 파싱 → 분류 → 포장 → 검증
                                    │
                                    ▼
                            [JSON 결과 반환]
                                    │
        ◀───────────────────────────┘
        │
        ▼
[프론트엔드: 결과 렌더링]
  ├── 요약 카드
  ├── 케이스 테이블 (Reason 포함)
  ├── PL Excel 다운로드
  └── 3D 컨테이너 시각화 (Three.js)
```

---

## 10. 자주 발생하는 문제 (FAQ)

### Q1. `pip install` 시 권한 오류가 발생합니다

```
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied
```

**해결:** 가상환경을 활성화했는지 확인하세요. `(venv)`가 프롬프트에 표시되어야 합니다.
```bash
source venv/bin/activate   # macOS/Linux
```

### Q2. 백엔드 실행 시 `ModuleNotFoundError: No module named 'src'`

**원인:** `shipping_doc_automation` 의존성이 설치되지 않았거나, 실행 위치가 잘못되었습니다.

**해결:**
```bash
# 반드시 shipping_web/backend/ 폴더에서 실행
cd shipping_web/backend
uvicorn main:app --reload --port 8000
```

### Q3. 프론트엔드 `npm run dev` 시 오류 발생

**해결:** `node_modules`를 삭제 후 재설치합니다.
```bash
cd shipping_web/frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Q4. 파일 업로드 시 "파이프라인 실행 오류" 에러

**가능한 원인들:**
1. CI 시트가 없는 엑셀 파일을 업로드한 경우 → CI 시트가 포함된 파일을 사용하세요
2. 파일이 손상된 경우 → 샘플 파일로 먼저 테스트하세요
3. 백엔드 서버가 꺼져있는 경우 → 터미널 1에서 서버가 실행 중인지 확인

### Q5. 3D 시각화가 보이지 않습니다

**가능한 원인:**
1. 컨테이너 시뮬레이션을 실행하지 않은 경우 → 컨테이너 타입 선택 후 "적재 시뮬레이션 실행" 클릭
2. WebGL을 지원하지 않는 브라우저 → Chrome 또는 Edge 최신 버전을 사용하세요

### Q6. `http://localhost:5173` 접속 시 API 요청이 실패합니다

**원인:** 백엔드 서버(포트 8000)가 실행되지 않은 상태입니다.

**해결:** 터미널 1에서 백엔드 서버가 정상 실행 중인지 확인하세요.
프론트엔드의 `vite.config.js`가 `/api` 요청을 `localhost:8000`으로 프록시합니다.

### Q7. Windows에서 한글 경로 오류가 발생합니다

**해결:** 프로젝트를 한글이 없는 경로에 클론하세요.
```bash
# 권장
cd C:\Dev
git clone https://github.com/genfeel/ci-pl-web-analyzer.git
```

### Q8. 가상환경을 매번 활성화해야 하나요?

네, 새 터미널을 열 때마다 활성화해야 합니다. IDE(VSCode 등)에서 Python 인터프리터를 `venv`로 설정하면 터미널에서 자동 활성화됩니다.

**VSCode 설정:**
1. `Cmd + Shift + P` (맥) 또는 `Ctrl + Shift + P` (윈도우)
2. "Python: Select Interpreter" 입력
3. `./venv/bin/python` 선택

---

## 11. 개발 참고 사항

### API 엔드포인트 요약

| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/api/upload` | CI Excel 업로드 → 파이프라인 실행 → JSON 결과 |
| `GET` | `/api/result/{result_id}` | 캐시된 결과 재조회 |
| `GET` | `/api/download-pl/{result_id}` | PL Excel 파일 다운로드 |
| `POST` | `/api/container-load/{result_id}` | 컨테이너 적재 시뮬레이션 |
| `GET` | `/health` | 서버 상태 확인 |

Swagger UI(`http://localhost:8000/docs`)에서 모든 API를 직접 테스트해볼 수 있습니다.

### 카테고리별 색상 코드

3D 시각화와 테이블에서 동일한 색상을 사용합니다.

| 카테고리 | 설명 | 색상 | Hex |
|----------|------|------|-----|
| VCB | 진공차단기 | 파랑 | `#2196F3` |
| ACB_HGS | 기중차단기(표준) | 초록 | `#4CAF50` |
| ACB_LARGE | 기중차단기(대형) | 틸 | `#009688` |
| MCCB | 배선용차단기 | 주황 | `#FF9800` |
| MC | 전자접촉기 | 보라 | `#9C27B0` |
| RELAY | 열동형과전류계전기 | 빨강 | `#F44336` |
| SPARE | 예비품 | 갈색 | `#795548` |

### 주요 포트

| 서비스 | 포트 | URL |
|--------|------|-----|
| 백엔드 (FastAPI) | 8000 | `http://localhost:8000` |
| 프론트엔드 (Vite) | 5173 | `http://localhost:5173` |
| API 문서 (Swagger) | 8000 | `http://localhost:8000/docs` |

### 테스트 실행 (shipping_doc_automation)

```bash
cd shipping_doc_automation
python3 -m pytest tests/ -v
```

### 프론트엔드 프로덕션 빌드

```bash
cd shipping_web/frontend
npm run build
# dist/ 폴더에 빌드 결과물이 생성됩니다
```
