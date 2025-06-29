# 필요한 라이브러리 임포트
import streamlit as st          # 웹 인터페이스 프레임워크
import requests                 # HTTP 요청 (Ollama API 통신)
import json                     # JSON 데이터 처리
import time                     # 시간 관련 함수
from datetime import datetime   # 날짜/시간 처리

# =============================================================================
# 전역 설정 상수
# =============================================================================

# Ollama 서버 API 설정
OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama 로컬 서버 주소
MODEL_NAME = "qwen2.5:7b"                   # 사용할 AI 모델명 (한국어 특화)

# =============================================================================
# 메인 면접 시스템 클래스
# =============================================================================

class OllamaInterviewSystem:
    """
    Ollama 기반 AI 면접 시스템 메인 클래스
    
    주요 기능:
    - AI 모델과의 통신 관리
    - 면접 진행 상태 추적
    - 한국어 최적화 프롬프트 생성
    - 대화 히스토리 관리
    """
    
    def __init__(self):
        """
        면접 시스템 초기화
        
        초기화되는 속성:
        - conversation_history: 대화 내역 저장 리스트
        - interview_type: 현재 면접 유형 (공무원/공기업/IT/사기업)
        - question_count: 현재 질문 번호
        - max_questions: 총 질문 수 제한
        """
        self.conversation_history = []  # 면접 대화 내역 저장
        self.interview_type = None      # 현재 진행 중인 면접 유형
        self.question_count = 0         # 현재 질문 번호 (1부터 시작)
        self.max_questions = 8          # 면접 총 질문 수 (조정 가능)
        
    def check_ollama_connection(self):
        """
        Ollama 서버 연결 상태 확인
        
        Returns:
            bool: 연결 성공 시 True, 실패 시 False
        """
        try:
            # Ollama API에 간단한 GET 요청으로 연결 테스트
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200  # HTTP 200 OK면 연결 성공
        except:
            # 네트워크 오류, 타임아웃 등 모든 예외 상황에서 False 반환
            return False
    
    def get_available_models(self):
        """
        Ollama에서 사용 가능한 AI 모델 목록 조회
        
        Returns:
            list: 설치된 모델명 리스트, 오류 시 빈 리스트
        """
        try:
            # Ollama API에서 모델 목록 요청
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                # 모델명만 추출해서 리스트로 반환
                return [model["name"] for model in models]
            return []
        except:
            # API 요청 실패 시 빈 리스트 반환
            return []
    
    def call_ollama(self, prompt: str) -> str:
        """
        Ollama API를 통해 AI 모델에게 질문하고 응답 받기
        
        Args:
            prompt (str): AI에게 전달할 프롬프트 (면접 질문 생성 지시)
            
        Returns:
            str: AI가 생성한 면접관 응답 또는 오류 메시지
        """
        try:
            # 한국어 강제 지침이 포함된 프롬프트 생성
            # 이 부분이 한국어 품질의 핵심!
            korean_prompt = f"""다음 지시사항을 반드시 따르세요:
1. 오직 표준 한국어로만 답변하세요
2. 일본어, 중국어, 영어를 절대 사용하지 마세요
3. 자연스러운 한국어 존댓말로 대화하세요
4. 한국의 면접관처럼 정중하고 전문적으로 대화하세요

{prompt}

반드시 완벽한 한국어로만 답변해주세요."""

            # Ollama API에 POST 요청으로 AI 모델 호출
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": MODEL_NAME,           # 사용할 AI 모델
                    "prompt": korean_prompt,       # 한국어 최적화된 프롬프트
                    "stream": False,               # 스트리밍 비활성화 (전체 응답 한번에)
                    "options": {
                        "temperature": 0.7,        # 창의성 수준 (0.0~1.0)
                        "top_p": 0.9,             # 단어 선택 다양성
                        "max_tokens": 500         # 최대 응답 길이 제한
                    }
                },
                timeout=360  # 6분 타임아웃 (8GB RAM 고려)
            )
            
            # API 응답 처리
            if response.status_code == 200:
                # 정상 응답에서 텍스트 추출 및 공백 제거
                return response.json()["response"].strip()
            else:
                # HTTP 오류 시 사용자 친화적 메시지
                return "죄송합니다. 일시적인 오류가 발생했습니다."
                
        except requests.exceptions.Timeout:
            # 타임아웃 오류 처리 (8GB RAM에서 자주 발생 가능)
            return "응답 시간이 초과되었습니다. 다시 시도해주세요."
        except Exception as e:
            # 기타 모든 예외 상황 처리
            return f"오류가 발생했습니다: {str(e)}"
    
    def get_interview_prompt(self, interview_type: str, is_first: bool = False) -> str:
        """
        면접 유형별 최적화된 프롬프트 생성
        
        Args:
            interview_type (str): 면접 유형 ('공무원', '공기업', 'IT', '사기업')
            is_first (bool): 첫 번째 질문 여부
            
        Returns:
            str: AI 모델에게 전달할 완성된 프롬프트
        """
        
        # 각 면접 유형별 특성화된 면접관 역할 정의
        type_prompts = {
            "공무원": """당신은 한국 정부기관의 경험이 풍부한 공무원 면접관입니다.
반드시 완벽한 표준 한국어로만 답변하세요. 절대 다른 언어를 사용하지 마세요.
면접 특징: 공직가치, 봉사정신, 공정성, 청렴성을 중시합니다.
주요 질문 영역: 지원동기, 공직관, 갈등해결, 시민서비스, 정책이해도, 국민에 대한 봉사정신""",
            
            "공기업": """당신은 한국의 대표적인 공기업 인사담당 면접관입니다.
반드시 완벽한 표준 한국어로만 답변하세요. 절대 다른 언어를 사용하지 마세요.
면접 특징: 공공성과 효율성, 전문성과 혁신을 균형있게 평가합니다.
주요 질문 영역: 기업이해도, 전문성, 사회적책임, 혁신아이디어, 조직적합성, 공기업 역할""",
            
            "IT": """당신은 한국의 유명한 IT 기업 기술면접관입니다.
반드시 완벽한 표준 한국어로만 답변하세요. 절대 다른 언어를 사용하지 마세요.
면접 특징: 기술역량, 문제해결능력, 학습능력, 협업능력을 중시합니다.
주요 질문 영역: 기술경험, 프로젝트사례, 문제해결, 최신기술동향, 팀워크, 코딩실력""",
            
            "사기업": """당신은 한국의 대기업 인사담당 면접관입니다.
반드시 완벽한 표준 한국어로만 답변하세요. 절대 다른 언어를 사용하지 마세요.
면접 특징: 성과지향성, 적응력, 리더십, 회사기여도를 중시합니다.
주요 질문 영역: 지원동기, 성취경험, 목표의식, 스트레스관리, 미래계획, 회사적합성"""
        }
        
        # 공통 면접 진행 지침 (모든 면접 유형에 적용)
        base_prompt = f"""{type_prompts[interview_type]}

중요한 면접 진행 지침:
- 반드시 표준 한국어로만 대화하세요 (절대 일본어, 중국어, 영어 금지)
- 정중하고 전문적인 한국어 존댓말 사용
- 한 번에 하나의 명확한 질문만 제시
- 실무 중심의 구체적인 질문 위주
- 지원자 답변에 대한 간단하고 건설적인 피드백 제공
- 한국의 면접 문화에 맞는 자연스러운 대화

현재 면접 진행 상황: {self.question_count + 1}번째 질문 (총 {self.max_questions}개 예정)"""

        # 첫 번째 질문인 경우의 프롬프트
        if is_first:
            return f"""{base_prompt}

지금 {interview_type} 면접을 시작합니다. 
한국의 면접관답게 정중한 인사말과 함께 첫 번째 질문을 해주세요.
반드시 완벽한 한국어로만 답변하세요. 절대 외국어를 사용하지 마세요."""
        
        # 후속 질문인 경우의 프롬프트 (대화 맥락 포함)
        else:
            # 최근 대화 내역 구성 (최대 2개의 이전 대화만 포함하여 프롬프트 길이 최적화)
            recent_history = ""
            if self.conversation_history:
                recent = self.conversation_history[-2:]  # 최근 2개 대화만 선택
                for conv in recent:
                    recent_history += f"면접관: {conv['interviewer']}\n지원자: {conv['user']}\n\n"
            
            return f"""{base_prompt}

최근 대화 내용:
{recent_history}

지원자의 답변에 대해 간단한 피드백을 주고, 다음 질문을 해주세요.
반드시 완벽한 한국어로만 답변하세요. 절대 외국어를 섞지 마세요.
답변이 구체적이고 좋다면 격려하고, 부족하다면 더 자세한 설명을 정중하게 요청하세요."""
    
    def start_interview(self, interview_type: str) -> str:
        """
        새로운 면접 세션 시작
        
        Args:
            interview_type (str): 시작할 면접 유형
            
        Returns:
            str: AI 면접관의 첫 번째 인사말 및 질문
        """
        # 면접 상태 초기화
        self.interview_type = interview_type    # 면접 유형 저장
        self.conversation_history = []          # 대화 내역 초기화
        self.question_count = 0                 # 질문 번호 초기화
        
        # 첫 번째 질문을 위한 프롬프트 생성
        prompt = self.get_interview_prompt(interview_type, is_first=True)
        
        # AI 모델에게 첫 질문 요청
        response = self.call_ollama(prompt)
        
        # 질문 카운터 증가
        self.question_count = 1
        
        return response
    
    def process_answer(self, user_answer: str) -> tuple[str, bool]:
        """
        지원자 답변 처리 및 다음 질문 생성
        
        Args:
            user_answer (str): 지원자가 입력한 답변
            
        Returns:
            tuple[str, bool]: (AI 면접관 응답, 면접 종료 여부)
        """
        
        # 면접 종료 조건 확인
        if self.question_count >= self.max_questions:
            # 최대 질문 수에 도달했을 때 면접 종료 처리
            prompt = f"""면접이 모두 완료되었습니다. 
지원자의 마지막 답변: {user_answer}

한국의 면접관답게 전체적인 면접에 대한 종합 피드백을 정중하고 따뜻하게 제공해주세요.
다음 내용을 포함해주세요:
1. 전반적인 면접 태도와 인상
2. 주요 강점 2-3가지
3. 개선이 필요한 부분 1-2가지  
4. 앞으로의 발전을 위한 조언
5. 격려와 응원의 마무리 인사

반드시 완벽한 한국어로만 답변하고 격려의 말씀으로 마무리해주세요."""
            
            # 종합 평가 생성
            response = self.call_ollama(prompt)
            return response, True  # 면접 종료 플래그와 함께 반환
        
        # 현재 답변을 대화 히스토리에 추가
        if self.conversation_history:
            # 마지막 대화의 사용자 답변 부분 업데이트
            self.conversation_history[-1]['user'] = user_answer
        
        # 다음 질문을 위한 프롬프트 생성
        prompt = self.get_interview_prompt(self.interview_type)
        prompt += f"\n\n지원자의 최근 답변: {user_answer}\n\n이 답변에 대한 간단한 피드백과 함께 다음 질문을 해주세요. 반드시 한국어로만 답변하세요."
        
        # AI 모델에게 다음 질문 요청
        response = self.call_ollama(prompt)
        
        # 새로운 대화를 히스토리에 추가 (면접관 질문만 먼저 저장)
        self.conversation_history.append({
            'interviewer': response,  # AI 면접관의 응답
            'user': None             # 사용자 답변은 다음 라운드에서 저장
        })
        
        # 질문 번호 증가
        self.question_count += 1
        
        return response, False  # 면접 계속 진행

# =============================================================================
# Streamlit 웹 인터페이스 메인 함수
# =============================================================================

def main():
    """
    Streamlit 기반 웹 애플리케이션 메인 함수
    
    웹 인터페이스 구성:
    1. 페이지 설정 및 제목
    2. 세션 상태 관리
    3. 사이드바 (시스템 상태, 면접 설정)
    4. 메인 콘텐츠 (면접 진행)
    """
    
    # Streamlit 페이지 기본 설정
    st.set_page_config(
        page_title="AI 면접 시스템",    # 브라우저 탭 제목
        page_icon="🇰🇷",              # 브라우저 탭 아이콘
        layout="wide"                  # 와이드 레이아웃 사용
    )
    
    # 페이지 헤더
    st.title("AI 모의 면접 시스템")     # 메인 제목
    st.caption("🚀한국어 특화")        # 부제목
    
    # =============================================================================
    # Streamlit 세션 상태 초기화
    # =============================================================================
    # 웹 페이지 새로고침 시에도 데이터 유지를 위한 세션 상태 관리
    
    if 'interview_system' not in st.session_state:
        # 면접 시스템 인스턴스 생성 (페이지당 한 번만)
        st.session_state.interview_system = OllamaInterviewSystem()
        
    if 'interview_started' not in st.session_state:
        # 면접 진행 상태 플래그
        st.session_state.interview_started = False
        
    if 'messages' not in st.session_state:
        # 화면에 표시할 대화 메시지 리스트
        st.session_state.messages = []
        
    if 'interview_finished' not in st.session_state:
        # 면접 완료 상태 플래그
        st.session_state.interview_finished = False
    
    # =============================================================================
    # 사이드바 구성
    # =============================================================================
    with st.sidebar:
        st.title("🔧 시스템 상태")
        
        # Ollama 서버 연결 상태 확인 및 표시
        is_connected = st.session_state.interview_system.check_ollama_connection()
        if is_connected:
            st.success("✅ Ollama 서버 연결됨")
            
            # 사용 가능한 AI 모델 목록 표시
            models = st.session_state.interview_system.get_available_models()
            if models:
                st.info(f"📦 사용 가능한 모델:\n{', '.join(models)}")
        else:
            # 연결 실패 시 오류 메시지 및 해결 방법 제시
            st.error("❌ Ollama 서버에 연결할 수 없습니다")
            st.info("해결방법:\n1. 'ollama serve' 실행\n2. 페이지 새로고침")
            return  # 연결되지 않으면 앱 종료
        
        # 면접 설정 섹션 (면접 시작 전에만 표시)
        if not st.session_state.interview_started:
            st.divider()  # 구분선
            st.subheader("📋 면접 설정")
            
            # 면접 유형 선택 드롭다운
            interview_types = {
                "🏛️ 공무원": "공무원",
                "🏢 공기업": "공기업", 
                "💻 IT": "IT",
                "🏪 사기업": "사기업"
            }
            
            selected = st.selectbox(
                "면접 유형 선택:",
                options=list(interview_types.keys())
            )
            # 선택된 면접 유형을 세션에 저장
            st.session_state.selected_type = interview_types[selected]
            
            # 선택된 면접 유형의 특징 정보 표시
            st.info(f"""
**{interview_types[selected]} 면접 특징:**
- 총 {st.session_state.interview_system.max_questions}개 질문 예정
- 한국어 특화 자연스러운 대화
- 실무 중심의 구체적 질문
- 답변별 즉시 피드백 제공
            """)
        else:
            # 면접 진행 중일 때 진행률 표시
            st.subheader("📊 면접 진행률")
            progress = st.session_state.interview_system.question_count
            max_q = st.session_state.interview_system.max_questions
            
            # 진행률 바 표시
            st.progress(progress / max_q)
            st.write(f"진행률: {progress}/{max_q}")
            st.write(f"면접 유형: {st.session_state.interview_system.interview_type}")
            
            # 면접 중단 버튼
            if st.button("🛑 면접 중단", type="secondary"):
                # 모든 면접 상태 초기화
                st.session_state.interview_started = False
                st.session_state.messages = []
                st.session_state.interview_finished = False
                st.rerun()  # 페이지 새로고침
    
    # =============================================================================
    # 메인 콘텐츠 영역
    # =============================================================================
    
    if not st.session_state.interview_started:
        # =============================================================================
        # 면접 시작 전 화면
        # =============================================================================
        col1, col2, col3 = st.columns([1, 2, 1])  # 3컬럼 레이아웃 (중앙 집중)
        with col2:
            st.markdown("### 🎯 면접 준비 완료!")
            
            # 선택된 면접 유형이 있는 경우에만 표시
            if hasattr(st.session_state, 'selected_type'):
                st.info(f"**선택된 면접:** {st.session_state.selected_type}")
                
                # 면접 진행 방식 안내
                st.markdown("""
                **💡 면접 진행 방식:**
- AI 면접관이 완벽한 한국어로 질문합니다
- 실무 중심의 전문적인 질문을 제공합니다  
- 각 답변에 대해 즉시 한국어 피드백을 받습니다
- 한국의 면접 문화에 맞는 자연스러운 대화를 진행합니다
- 면접 완료 후 종합 평가를 한국어로 제공합니다
                """)
                
                # 면접 시작 버튼
                if st.button("🚀 면접 시작하기!", type="primary", use_container_width=True):
                    # 로딩 메시지와 함께 면접 시작
                    with st.spinner("AI 면접관을 준비하고 있습니다..."):
                        # 선택된 유형으로 면접 시작
                        response = st.session_state.interview_system.start_interview(
                            st.session_state.selected_type
                        )
                        
                        # 첫 번째 메시지를 화면 표시용 리스트에 추가
                        st.session_state.messages = [
                            {
                                "role": "assistant",       # AI 면접관 역할
                                "content": response,        # 면접관의 첫 인사말
                                "timestamp": datetime.now() # 시간 기록
                            }
                        ]
                        
                        # 면접 상태 변경
                        st.session_state.interview_started = True
                        st.session_state.interview_finished = False
                        
                    st.rerun()  # 페이지 새로고침하여 면접 화면으로 전환
    
    else:
        # =============================================================================
        # 면접 진행 중 화면
        # =============================================================================
        st.markdown("### 💬 면접 진행")
        
        # 대화 내역 표시 (챗봇 스타일)
        for message in st.session_state.messages:
            if message["role"] == "assistant":
                # AI 면접관 메시지 (왼쪽, 한국 국기 아바타)
                with st.chat_message("assistant", avatar="🇰🇷"):
                    st.write(message["content"])
                    # 시간 정보가 있으면 표시
                    if "timestamp" in message:
                        st.caption(f"🕐 {message['timestamp'].strftime('%H:%M:%S')}")
            else:
                # 사용자 메시지 (오른쪽, 사람 아바타)
                with st.chat_message("user", avatar="👤"):
                    st.write(message["content"])
                    if "timestamp" in message:
                        st.caption(f"🕐 {message['timestamp'].strftime('%H:%M:%S')}")
        
        # =============================================================================
        # 답변 입력 폼 (면접이 끝나지 않은 경우만)
        # =============================================================================
        if not st.session_state.interview_finished:
            with st.form("answer_form", clear_on_submit=True):  # 제출 후 자동 클리어
                # 답변 입력 텍스트 박스
                user_input = st.text_area(
                    "💭 답변을 입력하세요:",
                    height=120,                                    # 높이 설정
                    placeholder="면접관의 질문에 구체적이고 성실하게 답변해 주세요...",  # 힌트 텍스트
                    help="Enter를 눌러서 줄바꿈하고, 아래 버튼으로 답변을 제출하세요."    # 도움말
                )
                
                # 버튼 레이아웃 (4:1 비율)
                col1, col2 = st.columns([4, 1])
                with col1:
                    submitted = st.form_submit_button("📤 답변 제출", type="primary")
                with col2:
                    skip = st.form_submit_button("⏭️ 건너뛰기")
                
                # 답변 제출 버튼 클릭 시 처리
                if submitted and user_input.strip():
                    # 사용자 답변을 화면 표시용 메시지 리스트에 추가
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": user_input,
                        "timestamp": datetime.now()
                    })
                    
                    # AI 응답 생성 (로딩 표시와 함께)
                    with st.spinner("면접관이 답변을 검토하고 있습니다..."):
                        ai_response, is_finished = st.session_state.interview_system.process_answer(user_input)
                    
                    # AI 응답을 화면 표시용 메시지 리스트에 추가
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": ai_response,
                        "timestamp": datetime.now()
                    })
                    
                    # 면접 종료 여부 확인
                    if is_finished:
                        st.session_state.interview_finished = True
                        st.balloons()  # 축하 애니메이션 표시
                    
                    st.rerun()  # 페이지 새로고침하여 새 메시지 표시
                
                # 건너뛰기 버튼 클릭 시 처리
                elif skip:
                    # 건너뛰기 메시지로 답변 처리
                    skip_response, is_finished = st.session_state.interview_system.process_answer("죄송하지만 이 질문은 건너뛰겠습니다.")
                    
                    # AI 응답만 추가 (사용자 입력은 추가하지 않음)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": skip_response,
                        "timestamp": datetime.now()
                    })
                    
                    # 면접 종료 여부 확인
                    if is_finished:
                        st.session_state.interview_finished = True
                    
                    st.rerun()
                
                # 빈 답변 제출 시 경고
                elif submitted:
                    st.warning("답변을 입력해주세요!")
        
        else:
            # =============================================================================
            # 면접 완료 후 화면
            # =============================================================================
            st.success("🎉 한국어 면접이 완료되었습니다!")
            
            # 3개 컬럼으로 버튼 배치
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # 새 면접 시작 버튼
                if st.button("🔄 새 면접 시작", type="primary"):
                    # 모든 상태 초기화하여 새 면접 준비
                    st.session_state.interview_started = False
                    st.session_state.messages = []
                    st.session_state.interview_finished = False
                    st.rerun()
            
            with col2:
                # 대화 내역 다운로드 기능
                if st.session_state.messages:
                    # 면접 기록을 텍스트 파일 형태로 생성
                    conversation_text = f"🇰🇷 한국어 AI 면접 기록\n"
                    conversation_text += f"면접 유형: {st.session_state.interview_system.interview_type}\n"
                    conversation_text += f"일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    conversation_text += "=" * 50 + "\n\n"
                    
                    # 모든 대화 내역을 텍스트로 변환
                    for msg in st.session_state.messages:
                        role = "🇰🇷 면접관" if msg["role"] == "assistant" else "👤 지원자"
                        timestamp = msg.get("timestamp", datetime.now()).strftime('%H:%M:%S')
                        conversation_text += f"[{timestamp}] {role}:\n{msg['content']}\n\n"
                    
                    # 다운로드 버튼 생성
                    st.download_button(
                        label="💾 면접 기록 저장",
                        data=conversation_text,                                                    # 다운로드할 데이터
                        file_name=f"korean_interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",  # 파일명 (날짜시간 포함)
                        mime="text/plain"                                                          # 파일 형식
                    )
            
            with col3:
                # 면접 통계 정보 표시
                total_questions = len([m for m in st.session_state.messages if m["role"] == "assistant"])
                st.metric("총 질문 수", total_questions)

# =============================================================================
# 프로그램 진입점
# =============================================================================

if __name__ == "__main__":
    """
    프로그램의 메인 실행 부분
    
    Python 스크립트가 직접 실행될 때만 main() 함수 호출
    (다른 모듈에서 import할 때는 실행되지 않음)
    """
    main()
