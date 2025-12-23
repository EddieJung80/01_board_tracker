import os
from pykrx import stock
import datetime

def get_top_market_cap_dict(corp_no=10):
    """
    KOSPI 시장 기준 시가총액 상위 N개 기업의 {이름: 종목코드} 딕셔너리를 반환합니다.
    """
    # 1. 최근 영업일 구하기 (주말/공휴일 대응)
    # 현재 날짜 기준 가장 가까운 영업일의 데이터를 가져옵니다.
    now = datetime.datetime.now()
    # 안전하게 어제 날짜부터 검색 (오늘 장 중에는 데이터가 없을 수 있음)
    search_date = (now - datetime.timedelta(days=1)).strftime("%Y%m%d")
    
    print(f"[*] {search_date} 시가총액 기준 상위 {corp_no}개 기업 추출 중...")
    
    try:
        # 2. KOSPI 시장 시가총액 데이터 가져오기
        df = stock.get_market_cap(search_date, market="KOSPI")
        
        # 데이터가 비어있다면 (주말/휴장일) 더 과거 날짜로 한 번 더 시도
        if df.empty:
            search_date = (now - datetime.timedelta(days=3)).strftime("%Y%m%d")
            df = stock.get_market_cap(search_date, market="KOSPI")

        # 3. 시가총액 순 정렬 및 N개 추출
        top_df = df.sort_values(by="시가총액", ascending=False).head(corp_no)
        
        corp_dict = {}
        for ticker in top_df.index:
            name = stock.get_market_ticker_name(ticker)
            corp_dict[name] = ticker
            
        return corp_dict
    except Exception as e:
        print(f"[!] 시총 데이터 확보 중 에러 발생: {e}")
        return {}

# 설정: 추출하고 싶은 기업 수
corp_no = 200

if __name__ == "__main__":
    result = get_top_market_cap_dict(corp_no)
    
    if result:
        print("\n--- 복사해서 config.py에 넣으세요 ---")
        print("TARGET_COMPANIES = {")
        for name, code in result.items():
            print(f'    "{name}": "{code}",')
        print("}")
    else:
        print("[!] 리스트를 생성하지 못했습니다.")