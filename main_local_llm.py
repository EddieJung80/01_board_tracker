import os
import time
import pandas as pd
from config import DART_API_KEY, TARGET_COMPANIES, START_YEAR, END_YEAR
from src.collector import DartCollector
from src.parser_local_llm import DartLLMParser_local

def main():
    # 1. 초기 설정 체크
    if not DART_API_KEY:
        print("[!] API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        return

    # 2. 수집기 및 파서 초기화
    collector = DartCollector(DART_API_KEY)
    parser = DartLLMParser_local()
    all_rows = [] # 엑셀에 들어갈 최종 행 리스트
    
    for corp_name, stock_code in TARGET_COMPANIES.items():
            reports = collector.get_annual_report_list(corp_name, stock_code, START_YEAR, END_YEAR)
            
            for report in reports:
                        year = report['year']
                        # DART에서 원본 HTML 가져오기
                        html_content = collector.dart.document(report['rcept_no'])
                        
                        # LLM 파서 작동
                        print(f"[*] {corp_name} {year}년 이사회 분석 중...")
                        parsed_result = parser.parse_board_info(html_content, corp_name, year)
                        
                        if parsed_result and 'directors' in parsed_result:
                            for d in parsed_result['directors']:
                                all_rows.append({
                                    '회사명': corp_name,
                                    '연도': year,
                                    '성명': d.get('name'),
                                    '직위': d.get('position'),
                                    '등기여부': d.get('is_registered', '등기'),
                                    '생년월일': d.get('birth_date', '-')
                                })
                            print(f"  - {len(parsed_result['directors'])}명 추출 성공")
                
            time.sleep(1) # API 속도 제한 및 비용 고려


    # 최종 엑셀 저장
    df = pd.DataFrame(all_rows)
    df.to_excel("output/final_board_status.xlsx", index=False)
    print(f"결과 저장 완료: output/final_board_status.xlsx")

if __name__ == "__main__":
    main()