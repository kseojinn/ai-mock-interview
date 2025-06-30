# 필요한 라이브러리 임포트
import streamlit as st          # 웹 인터페이스 프레임워크
import requests                 # HTTP 요청 (Ollama API 통신)
import json                     # JSON 데이터 처리
import time                     # 시간 관련 함수
from datetime import datetime   # 날짜/시간 처리
import PyPDF2                   # PDF 파일 읽기
import io                       # 바이트 스트림 처리
import re                       # 정규표현식

# =============================================================================
# 전역 설정 상수
# =============================================================================

# Ollama 서버 API 설정
OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama 로컬 서버 주소
MODEL_NAME = "qwen2.5:7b"                   # 사용할 AI 모델명 (한국어 특화)

# =============================================================================
# PDF 처리 유틸리티 클래스
# =============================================================================

class PDFProcessor:
    """
    포트폴리오 PDF 파일 처리 클래스
    
    주요 기능:
    - PDF 텍스트 추출
    - 텍스트 전처리 및 정제
    - 핵심 정보 식별
    """
    
    @staticmethod
    def extract_text_from_pdf(pdf_file) -> str:
        """
        PDF 파일에서 텍스트 추출
        
        Args:
            pdf_file: Streamlit 업로드 파일 객체
            
        Returns:
            str: 추출된 텍스트 내용
        """
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
            text = ""
            
            # 모든 페이지에서 텍스트 추출
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            st.error(f"PDF 파일 읽기 오류: {str(e)}")
            return ""
    
    @staticmethod
    def clean_and_process_text(text: str) -> str:
        """
        추출된 텍스트 전처리 및 정제
        
        Args:
            text: 원본 텍스트
            
        Returns:
            str: 정제된 텍스트
        """
        # 불필요한 공백과 줄바꿈 정리
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        # 특수문자 정리 (기본적인 것만)
        text = re.sub(r'[^\w\s가-힣.,!?():-]', '', text)
        
        return text.strip()
    
    @staticmethod
    def extract_key_sections(text: str) -> dict:
        """
        포트폴리오에서 핵심 섹션 정보 추출
        
        Args:
            text: 정제된 텍스트
            
        Returns:
            dict: 섹션별 정보
        """
        sections = {
            "education": "",
            "experience": "",
            "skills": "",
            "projects": "",
            "certifications": "",
            "others": ""
        }
        
        # 키워드 기반 섹션 분류
        education_keywords = ["학력", "교육", "대학", "학과", "전공", "졸업"]
        experience_keywords = ["경력", "경험", "근무", "회사", "업무", "담당"]
        skills_keywords = ["기술", "스킬", "언어", "도구", "프로그래밍"]
        project_keywords = ["프로젝트", "개발", "제작", "구현", "설계"]
        cert_keywords = ["자격증", "인증", "수료", "취득"]
        
        # 간단한 키워드 매칭으로 섹션 구분
        lines = text.split('\n')
        current_section = "others"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 섹션 판별
            if any(keyword in line for keyword in education_keywords):
                current_section = "education"
            elif any(keyword in line for keyword in experience_keywords):
                current_section = "experience"
            elif any(keyword in line for keyword in skills_keywords):
                current_section = "skills"
            elif any(keyword in line for keyword in project_keywords):
                current_section = "projects"
            elif any(keyword in line for keyword in cert_keywords):
                current_section = "certifications"
            
            sections[current_section] += line + " "
        
        return sections

# =============================================================================
# 메인 면접 시스템 클래스 (포트폴리오 기능 추가)
# =============================================================================

class PortfolioInterviewSystem:
    """
    포트폴리오 기반 AI 면접 시스템 메인 클래스
    
    주요 기능:
    - 포트폴리오 PDF 분석
    - 개인화된 면접 질문 생성
    - AI 모델과의 통신 관리
    - 면접 진행 상태 추적
    """
    
    def __init__(self):
        """
        면접 시스템 초기화
        """
        self.conversation_history = []  # 면접 대화 내역 저장
        self.interview_type = None      # 현재 면접 유형
        self.question_count = 0         # 현재 질문 번호
        self.max_questions = 8          # 총 질문 수 제한
        self.portfolio_content = ""     # 포트폴리오 내용
        self.portfolio_sections = {}    # 포트폴리오 섹션별 정보
        self.has_portfolio = False      # 포트폴리오 업로드 여부
        
    def check_ollama_connection(self):
        """Ollama 서버 연결 상태 확인"""
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_available_models(self):
        """사용 가능한 AI 모델 목록 조회"""
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
            return []
        except:
            return []
    
    def load_portfolio(self, pdf_file):
        """
        포트폴리오 PDF 로드 및 분석
        
        Args:
            pdf_file: Streamlit 업로드 파일 객체
            
        Returns:
            bool: 성공 여부
        """
        try:
            # PDF에서 텍스트 추출
            raw_text = PDFProcessor.extract_text_from_pdf(pdf_file)
            if not raw_text:
                return False
            
            # 텍스트 정제
            self.portfolio_content = PDFProcessor.clean_and_process_text(raw_text)
            
            # 섹션별 정보 추출
            self.portfolio_sections = PDFProcessor.extract_key_sections(self.portfolio_content)
            
            self.has_portfolio = True
            return True
            
        except Exception as e:
            st.error(f"포트폴리오 처리 중 오류 발생: {str(e)}")
            return False
    
    def call_ollama(self, prompt: str) -> str:
        """Ollama API를 통해 AI 모델 호출"""
        try:
            korean_prompt = f"""다음 지시사항을 반드시 따르세요:
1. 오직 표준 한국어로만 답변하세요
2. 일본어, 중국어, 영어를 절대 사용하지 마세요
3. 자연스러운 한국어 존댓말로 대화하세요
4. 한국의 면접관처럼 정중하고 전문적으로 대화하세요

{prompt}

반드시 완벽한 한국어로만 답변해주세요."""

            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": korean_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                },
                timeout=360
            )
            
            if response.status_code == 200:
                return response.json()["response"].strip()
            else:
                return "죄송합니다. 일시적인 오류가 발생했습니다."
                
        except requests.exceptions.Timeout:
            return "응답 시간이 초과되었습니다. 다시 시도해주세요."
        except Exception as e:
            return f"오류가 발생했습니다: {str(e)}"
    
    def get_portfolio_based_prompt(self, interview_type: str, is_first: bool = False) -> str:
        """
        포트폴리오 기반 면접 프롬프트 생성
        
        Args:
            interview_type: 면접 유형
            is_first: 첫 번째 질문 여부
            
        Returns:
            str: 완성된 프롬프트
        """
        # 기본 면접관 역할 정의
        type_prompts = {
            "공무원": """당신은 한국 정부기관의 경험이 풍부한 공무원 면접관입니다.
지원자의 포트폴리오를 검토한 후 공직가치, 봉사정신, 공정성을 중시하는 질문을 하세요.""",
            
            "공기업": """당신은 한국의 대표적인 공기업 인사담당 면접관입니다.
지원자의 포트폴리오를 바탕으로 공공성과 효율성, 전문성을 평가하는 질문을 하세요.""",
            
            "IT": """당신은 한국의 유명한 IT 기업 기술면접관입니다.
지원자의 포트폴리오에 나타난 기술경험과 프로젝트를 바탕으로 심화 질문을 하세요.""",
            
            "사기업": """당신은 한국의 대기업 인사담당 면접관입니다.
지원자의 포트폴리오를 검토하여 성과지향성과 회사기여도를 평가하는 질문을 하세요."""
        }
        
        # 포트폴리오 정보 요약
        portfolio_summary = ""
        if self.has_portfolio:
            portfolio_summary = f"""
**지원자 포트폴리오 요약:**
교육배경: {self.portfolio_sections.get('education', '정보 없음')[:200]}
경력사항: {self.portfolio_sections.get('experience', '정보 없음')[:200]}
기술/스킬: {self.portfolio_sections.get('skills', '정보 없음')[:200]}
프로젝트: {self.portfolio_sections.get('projects', '정보 없음')[:200]}
자격증: {self.portfolio_sections.get('certifications', '정보 없음')[:100]}
"""
        
        base_prompt = f"""{type_prompts[interview_type]}

{portfolio_summary}

면접 진행 지침:
- 반드시 표준 한국어로만 대화하세요
- 포트폴리오 내용을 바탕으로 구체적이고 개인화된 질문을 하세요
- 지원자의 경험과 스킬에 대해 심화 질문을 진행하세요
- 정중하고 전문적인 한국어 존댓말 사용
- 한 번에 하나의 명확한 질문만 제시

현재 면접 진행 상황: {self.question_count + 1}번째 질문 (총 {self.max_questions}개 예정)"""

        if is_first:
            return f"""{base_prompt}

지금 {interview_type} 면접을 시작합니다.
지원자의 포트폴리오를 검토했다는 인사말과 함께 포트폴리오 내용에 기반한 첫 번째 질문을 해주세요.
반드시 완벽한 한국어로만 답변하세요."""
        else:
            recent_history = ""
            if self.conversation_history:
                recent = self.conversation_history[-2:]
                for conv in recent:
                    recent_history += f"면접관: {conv['interviewer']}\n지원자: {conv['user']}\n\n"
            
            return f"""{base_prompt}

최근 대화 내용:
{recent_history}

지원자의 답변을 바탕으로 포트폴리오 내용과 연관된 심화 질문을 해주세요.
반드시 완벽한 한국어로만 답변하세요."""
    
    def start_interview(self, interview_type: str) -> str:
        """새로운 면접 세션 시작"""
        self.interview_type = interview_type
        self.conversation_history = []
        self.question_count = 0
        
        if self.has_portfolio:
            prompt = self.get_portfolio_based_prompt(interview_type, is_first=True)
        else:
            # 포트폴리오가 없는 경우 기본 면접 진행
            prompt = self.get_interview_prompt(interview_type, is_first=True)
        
        response = self.call_ollama(prompt)
        self.question_count = 1
        return response
    
    def get_interview_prompt(self, interview_type: str, is_first: bool = False) -> str:
        """기본 면접 프롬프트 (포트폴리오 없는 경우)"""
        type_prompts = {
            "공무원": """당신은 한국 정부기관의 경험이 풍부한 공무원 면접관입니다.
공직가치, 봉사정신, 공정성을 중시하는 질문을 하세요.""",
            "공기업": """당신은 한국의 대표적인 공기업 인사담당 면접관입니다.
공공성과 효율성, 전문성을 평가하는 질문을 하세요.""",
            "IT": """당신은 한국의 유명한 IT 기업 기술면접관입니다.
기술역량과 문제해결능력을 평가하는 질문을 하세요.""",
            "사기업": """당신은 한국의 대기업 인사담당 면접관입니다.
성과지향성과 회사기여도를 평가하는 질문을 하세요."""
        }
        
        base_prompt = f"""{type_prompts[interview_type]}

면접 진행 지침:
- 반드시 표준 한국어로만 대화하세요
- 정중하고 전문적인 한국어 존댓말 사용
- 한 번에 하나의 명확한 질문만 제시
- 실무 중심의 구체적인 질문 위주

현재 면접 진행 상황: {self.question_count + 1}번째 질문 (총 {self.max_questions}개 예정)"""

        if is_first:
            return f"""{base_prompt}

지금 {interview_type} 면접을 시작합니다.
정중한 인사말과 함께 첫 번째 질문을 해주세요.
반드시 완벽한 한국어로만 답변하세요."""
        else:
            recent_history = ""
            if self.conversation_history:
                recent = self.conversation_history[-2:]
                for conv in recent:
                    recent_history += f"면접관: {conv['interviewer']}\n지원자: {conv['user']}\n\n"
            
            return f"""{base_prompt}

최근 대화 내용:
{recent_history}

지원자의 답변에 대해 간단한 피드백을 주고, 다음 질문을 해주세요.
반드시 완벽한 한국어로만 답변하세요."""
    
    def process_answer(self, user_answer: str) -> tuple[str, bool]:
        """지원자 답변 처리 및 다음 질문 생성"""
        if self.question_count >= self.max_questions:
            # 면접 종료 처리
            portfolio_context = ""
            if self.has_portfolio:
                portfolio_context = "\n지원자의 포트폴리오 내용도 종합적으로 고려하여 평가해주세요."
            
            prompt = f"""면접이 모두 완료되었습니다.
지원자의 마지막 답변: {user_answer}
{portfolio_context}

한국의 면접관답게 전체적인 면접에 대한 종합 피드백을 제공해주세요.
다음 내용을 포함해주세요:
1. 전반적인 면접 태도와 인상
2. 주요 강점 2-3가지
3. 개선이 필요한 부분 1-2가지
4. 앞으로의 발전을 위한 조언
5. 격려와 응원의 마무리 인사

반드시 완벽한 한국어로만 답변하세요."""
            
            response = self.call_ollama(prompt)
            return response, True
        
        # 현재 답변을 대화 히스토리에 추가
        if self.conversation_history:
            self.conversation_history[-1]['user'] = user_answer
        
        # 다음 질문 생성
        if self.has_portfolio:
            prompt = self.get_portfolio_based_prompt(self.interview_type)
        else:
            prompt = self.get_interview_prompt(self.interview_type)
            
        prompt += f"\n\n지원자의 최근 답변: {user_answer}\n\n이 답변에 대한 간단한 피드백과 함께 다음 질문을 해주세요."
        
        response = self.call_ollama(prompt)
        
        self.conversation_history.append({
            'interviewer': response,
            'user': None
        })
        
        self.question_count += 1
        return response, False

# =============================================================================
# Streamlit 웹 인터페이스 메인 함수
# =============================================================================

def main():
    """Streamlit 기반 웹 애플리케이션 메인 함수"""
    
    st.set_page_config(
        page_title="포트폴리오 기반 AI 면접 시스템",
        page_icon="🇰🇷",
        layout="wide"
    )
    
    st.title("📁 포트폴리오 기반 AI 모의 면접 시스템")
    st.caption("🚀 한국어 특화 • 개인 맞춤형 면접")
    
    # 세션 상태 초기화
    if 'interview_system' not in st.session_state:
        st.session_state.interview_system = PortfolioInterviewSystem()
        
    if 'interview_started' not in st.session_state:
        st.session_state.interview_started = False
        
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        
    if 'interview_finished' not in st.session_state:
        st.session_state.interview_finished = False
    
    # 사이드바 구성
    with st.sidebar:
        st.title("🔧 시스템 상태")
        
        # Ollama 연결 확인
        is_connected = st.session_state.interview_system.check_ollama_connection()
        if is_connected:
            st.success("✅ Ollama 서버 연결됨")
            models = st.session_state.interview_system.get_available_models()
            if models:
                st.info(f"📦 사용 가능한 모델:\n{', '.join(models)}")
        else:
            st.error("❌ Ollama 서버에 연결할 수 없습니다")
            st.info("해결방법:\n1. 'ollama serve' 실행\n2. 페이지 새로고침")
            return
        
        # 면접 설정 (면접 시작 전에만)
        if not st.session_state.interview_started:
            st.divider()
            st.subheader("📋 면접 설정")
            
            # 포트폴리오 업로드 섹션
            st.markdown("### 📁 포트폴리오 업로드")
            uploaded_file = st.file_uploader(
                "포트폴리오 PDF를 업로드하세요:",
                type=['pdf'],
                help="PDF 형식의 이력서, 포트폴리오, 자기소개서 등을 업로드할 수 있습니다."
            )
            
            # 포트폴리오 처리
            if uploaded_file is not None:
                if not st.session_state.interview_system.has_portfolio:
                    with st.spinner("포트폴리오를 분석하고 있습니다..."):
                        success = st.session_state.interview_system.load_portfolio(uploaded_file)
                        if success:
                            st.success("✅ 포트폴리오 분석 완료!")
                            
                            # 포트폴리오 요약 표시
                            with st.expander("🔍 분석된 포트폴리오 요약"):
                                sections = st.session_state.interview_system.portfolio_sections
                                for section, content in sections.items():
                                    if content.strip():
                                        section_names = {
                                            "education": "🎓 교육배경",
                                            "experience": "💼 경력사항",
                                            "skills": "🛠️ 기술/스킬",
                                            "projects": "🚀 프로젝트",
                                            "certifications": "📜 자격증",
                                            "others": "📝 기타"
                                        }
                                        st.write(f"**{section_names.get(section, section)}:**")
                                        st.write(content[:200] + "..." if len(content) > 200 else content)
                        else:
                            st.error("❌ 포트폴리오 분석에 실패했습니다.")
                            
            elif st.session_state.interview_system.has_portfolio:
                st.success("✅ 포트폴리오 업로드됨")
                if st.button("🗑️ 포트폴리오 삭제"):
                    st.session_state.interview_system.has_portfolio = False
                    st.session_state.interview_system.portfolio_content = ""
                    st.session_state.interview_system.portfolio_sections = {}
                    st.rerun()
            
            # 면접 유형 선택
            st.markdown("### 💼 면접 유형 선택")
            interview_types = {
                "🏛️ 공무원": "공무원",
                "🏢 공기업": "공기업", 
                "💻 IT": "IT",
                "🏪 사기업": "사기업"
            }
            
            selected = st.selectbox(
                "면접 유형:",
                options=list(interview_types.keys())
            )
            st.session_state.selected_type = interview_types[selected]
            
            # 면접 모드 표시
            if st.session_state.interview_system.has_portfolio:
                st.info(f"""
**🎯 개인화 면접 모드**
- 업로드된 포트폴리오 기반 맞춤 질문
- {interview_types[selected]} 분야 특화 질문
- 총 {st.session_state.interview_system.max_questions}개 질문 예정
- 포트폴리오 내용 연관 심화 질문
                """)
            else:
                st.info(f"""
**📋 표준 면접 모드**
- {interview_types[selected]} 일반 면접 질문
- 총 {st.session_state.interview_system.max_questions}개 질문 예정
- 포트폴리오 업로드 시 개인화 면접 가능
                """)
                
        else:
            # 면접 진행 중 정보
            st.subheader("📊 면접 진행률")
            progress = st.session_state.interview_system.question_count
            max_q = st.session_state.interview_system.max_questions
            
            st.progress(progress / max_q)
            st.write(f"진행률: {progress}/{max_q}")
            st.write(f"면접 유형: {st.session_state.interview_system.interview_type}")
            
            # 포트폴리오 사용 여부 표시
            if st.session_state.interview_system.has_portfolio:
                st.success("📁 포트폴리오 기반 면접")
            else:
                st.info("📋 표준 면접")
            
            # 면접 중단 버튼
            if st.button("🛑 면접 중단", type="secondary"):
                st.session_state.interview_started = False
                st.session_state.messages = []
                st.session_state.interview_finished = False
                st.rerun()
    
    # 메인 콘텐츠
    if not st.session_state.interview_started:
        # 면접 시작 전 화면
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🎯 면접 준비 완료!")
            
            if hasattr(st.session_state, 'selected_type'):
                st.info(f"**선택된 면접:** {st.session_state.selected_type}")
                
                # 포트폴리오 업로드 상태에 따른 안내
                if st.session_state.interview_system.has_portfolio:
                    st.success("📁 **포트폴리오 기반 개인화 면접**")
                    st.markdown("""
                    **💡 개인화 면접 특징:**
- AI가 귀하의 포트폴리오를 분석했습니다
- 경력과 프로젝트에 기반한 맞춤형 질문
- 구체적인 경험에 대한 심화 질문
- 포트폴리오 내용 연관 시나리오 질문
                    """)
                else:
                    st.info("📋 **표준 면접 모드**")
                    st.markdown("""
                    **💡 표준 면접 진행 방식:**
- 선택한 분야의 일반적인 면접 질문
- 실무 중심의 전문적인 질문 제공
- 각 답변에 대한 즉시 피드백
- 한국의 면접 문화에 맞는 자연스러운 대화
                    """)
                    
                    st.warning("💡 **팁:** 포트폴리오를 업로드하면 더욱 개인화된 면접을 받을 수 있습니다!")
                
                # 면접 시작 버튼
                if st.button("🚀 면접 시작하기!", type="primary", use_container_width=True):
                    with st.spinner("AI 면접관을 준비하고 있습니다..."):
                        response = st.session_state.interview_system.start_interview(
                            st.session_state.selected_type
                        )
                        
                        st.session_state.messages = [
                            {
                                "role": "assistant",
                                "content": response,
                                "timestamp": datetime.now()
                            }
                        ]
                        
                        st.session_state.interview_started = True
                        st.session_state.interview_finished = False
                        
                    st.rerun()
    
    else:
        # 면접 진행 중 화면
        st.markdown("### 💬 면접 진행")
        
        # 대화 내역 표시
        for message in st.session_state.messages:
            if message["role"] == "assistant":
                with st.chat_message("assistant", avatar="🇰🇷"):
                    st.write(message["content"])
                    if "timestamp" in message:
                        st.caption(f"🕐 {message['timestamp'].strftime('%H:%M:%S')}")
            else:
                with st.chat_message("user", avatar="👤"):
                    st.write(message["content"])
                    if "timestamp" in message:
                        st.caption(f"🕐 {message['timestamp'].strftime('%H:%M:%S')}")
        
        # 답변 입력 폼 (면접이 끝나지 않은 경우만)
        if not st.session_state.interview_finished:
            with st.form("answer_form", clear_on_submit=True):
                user_input = st.text_area(
                    "💭 답변을 입력하세요:",
                    height=120,
                    placeholder="면접관의 질문에 구체적이고 성실하게 답변해 주세요...",
                    help="Enter를 눌러서 줄바꿈하고, 아래 버튼으로 답변을 제출하세요."
                )
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    submitted = st.form_submit_button("📤 답변 제출", type="primary")
                with col2:
                    skip = st.form_submit_button("⏭️ 건너뛰기")
                
                # 답변 제출 처리
                if submitted and user_input.strip():
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": user_input,
                        "timestamp": datetime.now()
                    })
                    
                    with st.spinner("면접관이 답변을 검토하고 있습니다..."):
                        ai_response, is_finished = st.session_state.interview_system.process_answer(user_input)
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": ai_response,
                        "timestamp": datetime.now()
                    })
                    
                    if is_finished:
                        st.session_state.interview_finished = True
                        st.balloons()
                    
                    st.rerun()
                
                elif skip:
                    skip_response, is_finished = st.session_state.interview_system.process_answer("죄송하지만 이 질문은 건너뛰겠습니다.")
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": skip_response,
                        "timestamp": datetime.now()
                    })
                    
                    if is_finished:
                        st.session_state.interview_finished = True
                    
                    st.rerun()
                
                elif submitted:
                    st.warning("답변을 입력해주세요!")
        
        else:
            # 면접 완료 후 화면
            st.success("🎉 포트폴리오 기반 면접이 완료되었습니다!")
            
            # 포트폴리오 기반 면접 완료 메시지
            if st.session_state.interview_system.has_portfolio:
                st.info("📁 업로드하신 포트폴리오를 바탕으로 개인화된 면접이 진행되었습니다.")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 새 면접 시작", type="primary"):
                    st.session_state.interview_started = False
                    st.session_state.messages = []
                    st.session_state.interview_finished = False
                    st.rerun()
            
            with col2:
                if st.session_state.messages:
                    # 면접 기록 생성
                    conversation_text = f"🇰🇷 포트폴리오 기반 AI 면접 기록\n"
                    conversation_text += f"면접 유형: {st.session_state.interview_system.interview_type}\n"
                    conversation_text += f"면접 모드: {'포트폴리오 기반' if st.session_state.interview_system.has_portfolio else '표준 모드'}\n"
                    conversation_text += f"일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    conversation_text += "=" * 50 + "\n\n"
                    
                    # 포트폴리오 요약 추가
                    if st.session_state.interview_system.has_portfolio:
                        conversation_text += "📁 포트폴리오 요약:\n"
                        sections = st.session_state.interview_system.portfolio_sections
                        for section, content in sections.items():
                            if content.strip():
                                section_names = {
                                    "education": "교육배경",
                                    "experience": "경력사항", 
                                    "skills": "기술/스킬",
                                    "projects": "프로젝트",
                                    "certifications": "자격증",
                                    "others": "기타"
                                }
                                conversation_text += f"- {section_names.get(section, section)}: {content[:100]}...\n"
                        conversation_text += "\n" + "=" * 50 + "\n\n"
                    
                    # 대화 내역 추가
                    for msg in st.session_state.messages:
                        role = "🇰🇷 면접관" if msg["role"] == "assistant" else "👤 지원자"
                        timestamp = msg.get("timestamp", datetime.now()).strftime('%H:%M:%S')
                        conversation_text += f"[{timestamp}] {role}:\n{msg['content']}\n\n"
                    
                    st.download_button(
                        label="💾 면접 기록 저장",
                        data=conversation_text,
                        file_name=f"portfolio_interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
            
            with col3:
                # 면접 통계
                total_questions = len([m for m in st.session_state.messages if m["role"] == "assistant"])
                st.metric("총 질문 수", total_questions)
                
                if st.session_state.interview_system.has_portfolio:
                    st.metric("면접 모드", "개인화")
                else:
                    st.metric("면접 모드", "표준")

# =============================================================================
# 프로그램 진입점
# =============================================================================

if __name__ == "__main__":
    """
    프로그램의 메인 실행 부분
    
    Python 스크립트가 직접 실행될 때만 main() 함수 호출
    """
    main()
