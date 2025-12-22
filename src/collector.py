import os
import OpenDartReader
import pandas as pd

class DartCollector:
    def __init__(self, api_key):
        self.dart = OpenDartReader(api_key)

    def get_annual_report_list(self, corp_name, stock_code, start_year, end_year):
        print(f"[*] {corp_name}({stock_code}) 보고서 리스트 검색 시작...")
        report_list = []
        
        for year in range(start_year, end_year + 1):
            try:
                # 1. 검색 기간을 다음 해 6월까지 더 넉넉히 잡습니다 (정정 보고서는 늦게 나올 수 있음)
                res = self.dart.list(stock_code, start=f"{year}-01-01", end=f"{year+1}-12-31", kind='A')
                
                if res is not None and not res.empty:
                    # 2. '사업보고서'라는 단어가 포함되어 있고, 해당 연도 결산 보고서인 것들만 추출
                    # 정규표현식 설명: .*(정정)?.*사업보고서.*연도\.12.*
                    # 즉, 앞에 [기재정정]이 붙든 뒤에 날짜가 붙든 '사업보고서'와 '연도.12'가 들어있으면 찾습니다.
                    pattern = rf"사업보고서 \({year}\.12\)"
                    target = res[res['report_nm'].str.contains(pattern, na=False)]
                    
                    if not target.empty:
                        # 3. 중요: 정정 보고서가 있을 경우 리스트의 가장 위에 있는 것이 최신본입니다.
                        # DART API 결과는 보통 접수일자 내림차순(최신순)으로 정렬되어 나옵니다.
                        latest_report = target.iloc[0] 
                        
                        report_list.append({
                            'year': year,
                            'corp_name': corp_name,
                            'rcept_no': latest_report['rcept_no'],
                            'report_nm': latest_report['report_nm']
                        })
                        print(f"  - {year}년: {latest_report['report_nm']} 확보 (번호: {latest_report['rcept_no']})")
                    else:
                        print(f"  - {year}년: 해당 연도 사업보고서를 찾을 수 없습니다.")
            except Exception as e:
                print(f"  - {year}년 리스트 조회 중 오류 발생: {e}")
                
        return report_list
    
    
    def save_report_html(self, corp_name, year, html_content):
        """
        내려받은 HTML 본문을 로컬 폴더에 저장합니다.
        """
        # 저장할 폴더 생성
        directory = f"raw_reports/{corp_name}"
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        # 파일명 결정 (예: 삼성전자_2023.html)
        file_path = f"{directory}/{corp_name}_{year}.html"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return file_path