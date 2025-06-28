# 한국어 최적화 Ollama 면접 시스템
# ollama_interview_korean.py

import streamlit as st
import requests
import json
import time
from datetime import datetime

# Ollama API 설정
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "qwen2.5:7b"  # 현재 작동하는 모델

class OllamaInterviewSystem:
    def __init__(self):
        self.conversation_history = []
        self.interview_type = None
        self.question_count = 0
        self.max_questions = 8
        
    def check_ollama_connection(self):
        """Ollama 서버 연결 확인"""
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_available_models(self):
        """사용 가능한 모델 목록 조회"""
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
            return []
        except:
            return []
    
    def call_ollama(self, prompt: str) -> str:
        """Ollama API 호출 - 한국어 최적화"""
        try:
            # 한국어 강제 프롬프트 추가
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
    
    def get_interview_prompt(self, interview_type: str, is_first: bool = False) -> str:
        """면접 유형별 프롬프트 생성 - 한국어 특화"""
        
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
        
        base_prompt = f"""{type_prompts[interview_type]}

중요한 면접 진행 지침:
- 반드시 표준 한국어로만 대화하세요 (절대 일본어, 중국어, 영어 금지)
- 정중하고 전문적인 한국어 존댓말 사용
- 한 번에 하나의 명확한 질문만 제시
- 실무 중심의 구체적인 질문 위주
- 지원자 답변에 대한 간단하고 건설적인 피드백 제공
- 한국의 면접 문화에 맞는 자연스러운 대화

현재 면접 진행 상황: {self.question_count + 1}번째 질문 (총 {self.max_questions}개 예정)"""

        if is_first:
            return f"""{base_prompt}

지금 {interview_type} 면접을 시작합니다. 
한국의 면접관답게 정중한 인사말과 함께 첫 번째 질문을 해주세요.
반드시 완벽한 한국어로만 답변하세요. 절대 외국어를 사용하지 마세요."""
        else:
            recent_history = ""
            if self.conversation_history:
                recent = self.conversation_history[-2:]  # 최근 2개 대화
                for conv in recent:
                    recent_history += f"면접관: {conv['interviewer']}\n지원자: {conv['user']}\n\n"
            
            return f"""{base_prompt}

최근 대화 내용:
{recent_history}

지원자의 답변에 대해 간단한 피드백을 주고, 다음 질문을 해주세요.
반드시 완벽한 한국어로만 답변하세요. 절대 외국어를 섞지 마세요.
답변이 구체적이고 좋다면 격려하고, 부족하다면 더 자세한 설명을 정중하게 요청하세요."""
    
    def start_interview(self, interview_type: str) -> str:
        """면접 시작"""
        self.interview_type = interview_type
        self.conversation_history = []
        self.question_count = 0
        
        prompt = self.get_interview_prompt(interview_type, is_first=True)
        response = self.call_ollama(prompt)
        self.question_count = 1
        
        return response
    
    def process_answer(self, user_answer: str) -> tuple[str, bool]:
        """답변 처리 및 다음 질문"""
        if self.question_count >= self.max_questions:
            # 면접 종료
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
            
            response = self.call_ollama(prompt)
            return response, True  # 면접 종료
        
        # 대화 히스토리에 추가
        if self.conversation_history:
            self.conversation_history[-1]['user'] = user_answer
        
        # 다음 질문 생성
        prompt = self.get_interview_prompt(self.interview_type)
        prompt += f"\n\n지원자의 최근 답변: {user_answer}\n\n이 답변에 대한 간단한 피드백과 함께 다음 질문을 해주세요. 반드시 한국어로만 답변하세요."
        
        response = self.call_ollama(prompt)
        
        # 새로운 대화 추가
        self.conversation_history.append({
            'interviewer': response,
            'user': None
        })
        
        self.question_count += 1
        return response, False  # 면접 계속

def main():
    st.set_page_config(
        page_title="AI 면접 시스템", 
        page_icon="🇰🇷",
        layout="wide"
    )
    
    st.title("AI 모의 면접 시스템")
    st.caption("🚀한국어 특화")
    
    # 세션 상태 초기화
    if 'interview_system' not in st.session_state:
        st.session_state.interview_system = OllamaInterviewSystem()
    if 'interview_started' not in st.session_state:
        st.session_state.interview_started = False
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'interview_finished' not in st.session_state:
        st.session_state.interview_finished = False
    
    # 사이드바 설정
    with st.sidebar:
        st.title("🔧 시스템 상태")
        
        # 연결 상태 확인
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
        
        # 면접 설정
        if not st.session_state.interview_started:
            st.divider()
            st.subheader("📋 면접 설정")
            
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
            st.session_state.selected_type = interview_types[selected]
            
            st.info(f"""
**{interview_types[selected]} 면접 특징:**
- 총 {st.session_state.interview_system.max_questions}개 질문 예정
- 한국어 특화 자연스러운 대화
- 실무 중심의 구체적 질문
- 답변별 즉시 피드백 제공
            """)
        else:
            # 면접 진행 상황
            st.subheader("📊 면접 진행률")
            progress = st.session_state.interview_system.question_count
            max_q = st.session_state.interview_system.max_questions
            
            st.progress(progress / max_q)
            st.write(f"진행률: {progress}/{max_q}")
            st.write(f"면접 유형: {st.session_state.interview_system.interview_type}")
            
            if st.button("🛑 면접 중단", type="secondary"):
                st.session_state.interview_started = False
                st.session_state.messages = []
                st.session_state.interview_finished = False
                st.rerun()
    
    # 메인 콘텐츠
    if not st.session_state.interview_started:
        # 시작 화면
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🎯 면접 준비 완료!")
            
            if hasattr(st.session_state, 'selected_type'):
                st.info(f"**선택된 면접:** {st.session_state.selected_type}")
                
                st.markdown("""
                **💡 면접 진행 방식:**
- AI 면접관이 완벽한 한국어로 질문합니다
- 실무 중심의 전문적인 질문을 제공합니다  
- 각 답변에 대해 즉시 한국어 피드백을 받습니다
- 한국의 면접 문화에 맞는 자연스러운 대화를 진행합니다
- 면접 완료 후 종합 평가를 한국어로 제공합니다
                """)
                
                if st.button("🚀 면접 시작하기!", type="primary", use_container_width=True):
                    with st.spinner("AI 면접관을 준비하고 있습니다..."):
                        response = st.session_state.interview_system.start_interview(
                            st.session_state.selected_type
                        )
                        st.session_state.messages = [
                            {"role": "assistant", "content": response, "timestamp": datetime.now()}
                        ]
                        st.session_state.interview_started = True
                        st.session_state.interview_finished = False
                    st.rerun()
    
    else:
        # 면접 진행 화면
        st.markdown("### 💬 면접 진행")
        
        # 대화 표시
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
        
        # 답변 입력 (면접이 끝나지 않은 경우만)
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
                
                if submitted and user_input.strip():
                    # 사용자 답변 추가
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": user_input,
                        "timestamp": datetime.now()
                    })
                    
                    # AI 응답 생성
                    with st.spinner("면접관이 답변을 검토하고 있습니다..."):
                        ai_response, is_finished = st.session_state.interview_system.process_answer(user_input)
                    
                    # AI 응답 추가
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
                    # 건너뛰기 처리
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
            # 면접 완료
            st.success("🎉 한국어 면접이 완료되었습니다!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 새 면접 시작", type="primary"):
                    st.session_state.interview_started = False
                    st.session_state.messages = []
                    st.session_state.interview_finished = False
                    st.rerun()
            
            with col2:
                # 대화 내역 다운로드
                if st.session_state.messages:
                    conversation_text = f"🇰🇷 한국어 AI 면접 기록\n"
                    conversation_text += f"면접 유형: {st.session_state.interview_system.interview_type}\n"
                    conversation_text += f"일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    conversation_text += "=" * 50 + "\n\n"
                    
                    for msg in st.session_state.messages:
                        role = "🇰🇷 면접관" if msg["role"] == "assistant" else "👤 지원자"
                        timestamp = msg.get("timestamp", datetime.now()).strftime('%H:%M:%S')
                        conversation_text += f"[{timestamp}] {role}:\n{msg['content']}\n\n"
                    
                    st.download_button(
                        label="💾 면접 기록 저장",
                        data=conversation_text,
                        file_name=f"korean_interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
            
            with col3:
                st.metric("총 질문 수", len([m for m in st.session_state.messages if m["role"] == "assistant"]))

if __name__ == "__main__":
    main()
