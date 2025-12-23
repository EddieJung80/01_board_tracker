import os
import re
import warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
# from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama 
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from .schema import BoardStatus # 이전에 정의한 Pydantic 모델


# BeautifulSoup의 XML 관련 경고를 무시하도록 설정
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


class DartLLMParser_local:
    def __init__(self):
        # ChatOpenAI 초기화
        # self.llm = ChatOpenAI(
        #     temperature=0,
        #     model_name="openai/gpt-4.1",  # OpenRouter에서 제공하는 GPT-4.1 모델
        #     api_key=os.getenv("OPENROUTER_API_KEY"),  # OpenRouter API 키
        #     base_url=os.getenv("OPENROUTER_BASE_URL"),  # OpenRouter API URL
        #     )
        
        self.llm = ChatOllama(
            model="exaone3.5:7.8b", 
            temperature=0,
            format="json" # Ollama에게 JSON 출력을 강제하는 옵션
        )



        self.parser = JsonOutputParser(pydantic_object=BoardStatus)

    def extract_board_section(self, html_content):
        """
        '1. 이사회에 관한 사항' 섹션을 찾아 그 아래 텍스트를 추출합니다.
        """
        # 여기서 lxml 파서를 사용해도 위에서 필터링했기 때문에 경고가 뜨지 않습니다.
        soup = BeautifulSoup(html_content, 'lxml')
        
        target_section = None
        # TITLE 태그나 SPAN 태그 중 핵심 키워드 포함된 것 찾기
        titles = soup.find_all(['title', 'span', 'p', 'b'])
        for title in titles:
            text = title.get_text(strip=True)
            # '1. 이사회에 관한 사항' 또는 '이사회 구성 개요' 매칭
            if "1. 이사회에 관한 사항" in text or "이사회 구성 개요" in text:
                target_section = title
                break
        
        if not target_section:
            # 섹션을 못 찾을 경우, 전체 텍스트의 앞부분을 반환 (최소한의 데이터 확보)
            return soup.get_text()[:12000]

        # 해당 위치부터 텍스트 수집 (다음 대단원 전까지)
        content_parts = []
        # find_all_next를 사용하여 target_section 이후의 모든 텍스트 요소를 가져옴
        for element in target_section.find_all_next(string=True):
            text = element.strip()
            if text:
                content_parts.append(text)
            
            # 다음 섹션 번호(예: 2. 감사제도)가 보이면 중단 (정규표현식)
            if re.match(r"^[2-9]\.\s", text): 
                break
            
            # 너무 길어지면 토큰 제한을 위해 중단
            if len(" ".join(content_parts)) > 10000:
                break
                
        return "\n".join(content_parts)

    def parse_board_info(self, html_content, corp_name, year):
        # 특정 섹션 텍스트만 추출
        context_text = self.extract_board_section(html_content)
        
        prompt = ChatPromptTemplate.from_template(
            "당신은 기업 지배구조 분석 전문가입니다.\n"
            "아래는 {year}년도 {corp_name}의 사업보고서 중 '이사회에 관한 사항' 섹션의 내용입니다.\n"
            "이 텍스트를 분석하여 {year}년 당시 이사회의 모든 구성원(사내이사, 사외이사 포함) 명단을 추출하세요.\n"
            "텍스트 내에 괄호로 나열된 이름들(예: 사내이사 3인(이름1, 이름2...))을 특히 주의 깊게 확인하여 누락 없이 추출하세요.\n"
            "반드시 아래 JSON 형식으로 답변하세요.\n"
            "{format_instructions}\n\n"
            "보고서 내용:\n{context}"
        )
        
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