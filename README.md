# Board Tracker

DART 사업보고서에서 상장사 이사회 구성원을 자동으로 추출해 엑셀로 정리하는 도구입니다.

매년 이사회 멤버가 바뀌는데, 누가 새로 선임됐고 누가 빠졌는지 확인하려면 보고서를 일일이 열어봐야 한다. DART API로 반기보고서를 내려받고, LLM이 HTML 본문에서 이사회 구성원 명단을 뽑아내 엑셀 파일로 저장한다.

---

## 동작 방식

1. `config.py`에 지정된 기업 목록과 연도 범위를 읽는다
2. DART API로 해당 연도의 반기보고서를 검색한다 (정정 보고서가 있으면 최신본 우선)
3. 보고서 HTML에서 "이사회에 관한 사항" 섹션만 잘라낸다
4. LLM이 섹션 텍스트를 분석해 이사 명단을 JSON으로 반환한다
5. 전체 결과를 `output/final_board_status.xlsx`로 저장한다

---

## 프로젝트 구조

```
01_board_tracker/
├── .env                    # DART_API_KEY 등 환경변수 (git 제외)
├── config.py               # 대상 기업 목록, 분석 연도 범위
├── main.py                 # OpenRouter(GPT-4.1) 기반 실행 진입점
├── main_local_llm.py       # 로컬 Ollama(exaone3.5) 기반 실행 진입점
├── src/
│   ├── collector.py        # DART API 연동, 보고서 수집
│   ├── parser.py           # OpenRouter LLM 파서
│   ├── parser_local_llm.py # 로컬 Ollama LLM 파서
│   └── schema.py           # Pydantic 데이터 모델 (Director, BoardStatus)
├── raw_reports/            # 다운로드된 HTML 보고서 (회사별 폴더)
└── output/                 # 최종 엑셀 파일
```

---

## 사전 준비

### 1. DART API 키 발급

[DART 오픈API](https://opendart.fss.or.kr/)에서 API 키를 발급받는다.

프로젝트 루트에 `.env` 파일을 만들고 키를 입력한다:

```
DART_API_KEY=your_dart_api_key_here
```

### 2. LLM 선택

두 가지 방식 중 하나를 선택한다.

**방식 A: 로컬 Ollama (기본값)**

Ollama가 설치되어 있어야 하고, `exaone3.5:7.8b` 모델을 내려받아야 한다:

```bash
ollama pull exaone3.5:7.8b
```

실행은 `main_local_llm.py`를 사용한다.

**방식 B: OpenRouter (클라우드 GPT-4.1)**

`.env`에 OpenRouter 키를 추가한다:

```
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

실행은 `main.py`를 사용한다.

### 3. 의존성 설치

```bash
uv sync
```

또는 pip:

```bash
pip install -r requirements.txt
```

---

## 실행

### 대상 기업 설정

`config.py`에서 분석할 기업과 연도 범위를 지정한다. 현재는 SK Inc., SK텔레콤, 삼성전자만 활성화되어 있고, 나머지는 주석 처리되어 있다.

```python
START_YEAR = 2022
END_YEAR = 2025

TARGET_COMPANIES = {
    "SK Inc.": "034730",
    "SK텔레콤": "017670",
    "삼성전자": "005930",
}
```

종목코드는 DART 또는 증권사 HTS에서 확인할 수 있다.

### 실행 명령

로컬 LLM:

```bash
python main_local_llm.py
```

OpenRouter:

```bash
python main.py
```

---

## 출력 결과

`output/final_board_status.xlsx`에 아래 컬럼으로 저장된다:

| 회사명 | 연도 | 성명 | 직위 | 등기여부 | 생년월일 |
|--------|------|------|------|----------|----------|
| SK텔레콤 | 2024 | 홍길동 | 사외이사 | 등기 | 1965.03 |

---

## 주의사항

- DART API에는 일일 호출 제한이 있다. 대상 기업이 많을 경우 `time.sleep(1)`을 조정하거나 요청 수를 나눠서 실행한다.
- 사업보고서 대신 반기보고서를 기준으로 한다. 당해년도 이사회 현황이 반기보고서에 더 잘 반영되어 있기 때문이다. `collector.py` 내 `pattern` 변수를 수정하면 사업보고서로 전환할 수 있다.
- LLM 파싱이 항상 맞지는 않는다. HTML 구조가 회사마다 다르고, 특히 괄호 안에 묶인 이름들을 빠뜨리는 경우가 있다. 중요한 데이터라면 원본 보고서와 직접 대조해보는 게 낫다.
