from pydantic import BaseModel, Field
from typing import List

class Director(BaseModel):
    name: str = Field(description="이사의 성명")
    position: str = Field(description="직위 (예: 사내이사, 사외이사, 대표이사 등)")

class BoardStatus(BaseModel):
    corp_name: str = Field(description="회사명")
    year: str = Field(description="해당 사업보고서의 연도")
    directors: List[Director] = Field(description="이사회 구성원 리스트")