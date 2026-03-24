import os
import json
import psycopg2
from psycopg2.extras import Json


def _get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")


def get_cached_result(stock_code: str, year: int) -> list[dict] | None:
    """캐시된 이사 목록 반환. 없으면 None."""
    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT directors FROM board_cache WHERE stock_code = %s AND year = %s",
                    (stock_code, year),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                directors = row[0]
                if isinstance(directors, str):
                    directors = json.loads(directors)
                return directors
    except Exception as e:
        print(f"  [!] 캐시 조회 오류 (무시하고 진행): {e}")
        return None


def save_cache_result(
    corp_name: str, stock_code: str, year: int, directors: list[dict]
) -> None:
    """이사 목록을 캐시에 저장 (UPSERT)."""
    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO board_cache (corp_name, stock_code, year, directors)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (stock_code, year)
                    DO UPDATE SET
                        corp_name = EXCLUDED.corp_name,
                        directors = EXCLUDED.directors,
                        cached_at = NOW()
                    """,
                    (corp_name, stock_code, year, Json(directors)),
                )
            conn.commit()
    except Exception as e:
        print(f"  [!] 캐시 저장 오류 (결과는 정상 처리): {e}")
