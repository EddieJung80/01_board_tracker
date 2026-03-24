import os
import re
import warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from .schema import BoardStatus # 이전에 정의한 Pydantic 모델


# BeautifulSoup의 XML 관련 경고를 무시하도록 설정
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


class DartLLMParser:
    def __init__(self):
        # ChatOpenAI 초기화
        self.llm = ChatOpenAI(
            temperature=0,
            model_name="openai/gpt-4.1",  # OpenRouter에서 제공하는 GPT-4.1 모델
            api_key=os.getenv("OPENROUTER_API_KEY"),  # OpenRouter API 키
            base_url=os.getenv("OPENROUTER_BASE_URL"),  # OpenRouter API URL
            )

        self.parser = JsonOutputParser(pydantic_object=BoardStatus)

    def _extract_section_by_note(self, soup, aassocnote, max_chars=4000):
        """AASSOCNOTE 속성으로 DART 섹션을 찾아 최대 max_chars 글자의 텍스트를 추출합니다."""
        title_tag = soup.find(attrs={"aassocnote": aassocnote})

        if not title_tag:
            return ""

        content_parts = []
        for element in title_tag.find_all_next(string=True):
            text = element.strip()
            if text:
                content_parts.append(text)

            if len(" ".join(content_parts)) > max_chars:
                break

        return "\n".join(content_parts)

    def extract_board_section(self, html_content, corp_name="", year=""):
        """
        '1. 이사회에 관한 사항'(D-0-6-1-0)과 '2. 감사제도에 관한 사항'(D-0-6-2-0) 섹션을 합쳐 추출합니다.
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # 1. 이사회에 관한 사항 (5000글자)
        board_text = self._extract_section_by_note(soup, "D-0-6-1-0")

        # 2. 감사제도에 관한 사항 (5000글자)
        audit_text = self._extract_section_by_note(soup, "D-0-6-2-0")

        if not board_text and not audit_text:
            return soup.get_text()[:12000]

        combined = board_text
        if audit_text:
            combined += "\n\n" + audit_text

        # 검증용: 추출된 텍스트를 파일로 저장
        os.makedirs("output/debug", exist_ok=True)
        debug_path = f"output/debug/{corp_name}_{year}_combined.txt"
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(combined)

        return combined

    def parse_board_info(self, html_content, corp_name, year):
        # 특정 섹션 텍스트만 추출
        context_text = self.extract_board_section(html_content, corp_name, year)

        prompt = ChatPromptTemplate.from_template(
            "당신은 기업 지배구조 분석 전문가입니다.\n"
            "아래는 {year}년도 {corp_name}의 사업보고서 중 '이사회에 관한 사항'과 '감사제도에 관한 사항' 섹션의 내용입니다.\n"
            "이 텍스트를 분석하여 다음 두 가지를 수행하세요:\n\n"
            "1. {year}년 당시 이사회의 모든 구성원(사내이사, 사외이사 포함) 명단을 추출하세요.\n"
            "   텍스트 내에 괄호로 나열된 이름들(예: 사내이사 3인(이름1, 이름2...))을 특히 주의 깊게 확인하여 누락 없이 추출하세요.\n\n"
            "2. 각 이사가 '회계 또는 재무 전문가'로 인정되는지 판단하세요.\n"
            "   보고서에서 감사위원회 관련 내용 중 '회계 또는 재무 전문가' 요건을 충족한다고 명시된 이사는 financial_expert를 \"Y\"로 표시하세요.\n"
            "   명시되지 않은 이사는 financial_expert를 빈 문자열(\"\")로 표시하세요.\n\n"
            "반드시 아래 JSON 형식으로 답변하세요.\n"
            "{format_instructions}\n\n"
            "보고서 내용:\n{context}"
        )

        chain = prompt | self.llm | self.parser

        # # 디버깅용 프린트
        # print(context_text[:5000]) # 디버깅용: 추출된 텍스트의 앞부분 출력

        chain = prompt | self.llm | self.parser

        try:
            return chain.invoke({
                "year": year,
                "corp_name": corp_name,
                "context": context_text,
                "format_instructions": self.parser.get_format_instructions()
            })
        except Exception as e:
            print(f"  [!] LLM 파싱 오류 ({corp_name} {year}): {e}")
            return None