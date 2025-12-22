import os
import time
from dotenv import load_dotenv
from config import DART_API_KEY, TARGET_COMPANIES, START_YEAR, END_YEAR
from src.collector import DartCollector

# .env 로드
load_dotenv()

def save_all_reports():
    # 1. 초기화 및 저장 폴더 생성
    if not DART_API_KEY:
        print("[!] API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        return

    collector = DartCollector(DART_API_KEY)
    base_dir = "raw_reports"
    
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    print(f"🚀 사업보고서 다운로드 시작 ({START_YEAR}년 ~ {END_YEAR}년)")
    print(f"📂 저장 경로: {os.path.abspath(base_dir)}\n")

    # 2. 기업별 루프
    for corp_name, stock_code in TARGET_COMPANIES.items():
        print(f"[*] {corp_name} ({stock_code}) 처리 중...")
        
        # 해당 기업 폴더 생성
        corp_dir = os.path.join(base_dir, corp_name)
        if not os.path.exists(corp_dir):
            os.makedirs(corp_dir)

        # 3. 연도별 사업보고서 리스트 확보
        # 이전에 만든 collector의 get_annual_report_list 함수를 활용합니다.
        reports = collector.get_annual_report_list(corp_name, stock_code, START_YEAR, END_YEAR)
        
        if not reports:
            print(f"  - [!] 수집 가능한 보고서가 없습니다.")
            continue

        # 4. 보고서 본문 다운로드 및 저장
        for report in reports:
            year = report['year']
            rcept_no = report['rcept_no']
            file_path = os.path.join(corp_dir, f"{corp_name}_{year}.html")

            # 이미 파일이 있다면 건너뜁니다 (중복 다운로드 방지)
            if os.path.exists(file_path):
                print(f"  - {year}년: 이미 존재함 (Pass)")
                continue

            try:
                # DART에서 HTML 본문 가져오기
                html_content = collector.dart.document(rcept_no)
                
                # 파일 쓰기
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                print(f"  - {year}년: 저장 완료 ({rcept_no})")
                
                # API 부하 방지를 위한 짧은 휴식
                time.sleep(0.5)

            except Exception as e:
                print(f"  - {year}년: 저장 실패 ({e})")

    print("\n" + "="*50)
    print("✅ 모든 보고서 다운로드 작업이 완료되었습니다.")
    print("="*50)

if __name__ == "__main__":
    save_all_reports()