import os
from dotenv import load_dotenv

load_dotenv()

# 환경 변수 및 설정
DART_API_KEY = os.getenv("DART_API_KEY")

# 분석 대상 기간
START_YEAR = 2015
END_YEAR = 2025

## 추후 자동화 진행 예정임 ##
# 시총 상위 10개 기업 (추후 자동화)
TARGET_COMPANIES = {
    "SK텔레콤": "017670",
    "SK Inc.": "034730",
    "SK하이닉스": "000660",
    "SK스퀘어": "402340",
}