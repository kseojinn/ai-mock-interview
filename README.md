# AI Mock Interview System

한국어 특화 AI 모의 면접 시스템 - Ollama & LangChain 기반

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![Ollama](https://img.shields.io/badge/Ollama-Latest-green.svg)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 소개

AI Mock Interview는 **완전 무료**로 사용할 수 있는 한국어 특화 AI 면접 시스템입니다. Ollama를 통해 로컬에서 실행되며, 개인정보 보호와 무제한 사용이 가능합니다.

### 주요 특징

- 🇰🇷 **한국어 특화**: 완벽한 한국어 면접 진행
-  **개인정보 보호**: 모든 데이터가 로컬에서 처리
-  **4가지 면접 유형**: 공무원, 공기업, IT, 사기업
-  **실시간 피드백**: 각 답변에 대한 즉시 평가
-  **종합 평가**: 면접 완료 후 상세한 분석 제공

## 빠른 시작

### 1. 필요 조건

- Python 3.8 이상
- 8GB+ RAM (권장)

### 2. Ollama 설치

#### Windows
```bash
# 공식 사이트에서 다운로드
https://ollama.ai/download
```

#### macOS/Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 3. AI 모델 다운로드

```bash
# 한국어 특화 추천 모델 (4.4GB)
ollama pull qwen2.5:7b

# 또는 경량 모델 (2GB)
ollama pull llama3.2:latest
```

### 4. 프로젝트 설치

```bash
# 저장소 클론
git clone https://github.com/kseojinn/ai-mock-interview.git
cd ai-mock-interview

# 의존성 설치
pip install -r requirements.txt

# Ollama 서버 시작
ollama serve
```

### 5. 면접 시스템 실행

```bash
# 웹 인터페이스 실행
streamlit run ai-mock-interview.py

# 브라우저에서 자동 실행: http://localhost:8501
```

## 시스템 요구사항

| 구성 요소 | 최소 사양 | 권장 사양 |
|-----------|-----------|-----------|
| **RAM** | 8GB | 16GB+ |
| **저장공간** | 10GB | 20GB+ |
| **CPU** | 듀얼코어 | 쿼드코어+ |
| **Python** | 3.8+ | 3.10+ |

###  모델별 메모리 사용량

| 모델 | 크기 | RAM 요구량 | 품질 | 속도 |
|------|------|------------|------|------|
| `llama3.2:latest` | 2GB | 4GB | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| `qwen2.5:7b` | 4.4GB | 8GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| `qwen2.5:14b` | 9GB | 16GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 면접 유형별 특징

### 🏛️ 공무원 면접
- **중점 평가**: 공직가치, 봉사정신, 공정성
- **주요 질문**: 지원동기, 공직관, 갈등해결, 시민서비스
- **특화 기능**: 정책 이해도, 청렴성 평가

### 🏢 공기업 면접
- **중점 평가**: 공공성과 효율성의 균형
- **주요 질문**: 기업이해도, 전문성, 사회적 책임
- **특화 기능**: 혁신 아이디어, 조직 적합성

### 💻 IT 면접
- **중점 평가**: 기술역량, 문제해결능력
- **주요 질문**: 프로젝트 경험, 기술 트렌드, 팀워크
- **특화 기능**: 코딩 실력, 학습 능력 평가

### 🏪 사기업 면접
- **중점 평가**: 성과지향성, 적응력, 리더십
- **주요 질문**: 성취경험, 목표의식, 스트레스 관리
- **특화 기능**: 회사 기여도, 경력 계획

## 프로젝트 구조

```
ai-mock-interview/
├── ai-mock-interview.py      # 메인 면접 시스템
├── requirements.txt          # Python 의존성
├── README.md                # 프로젝트 문서
```

## 설정 및 커스터마이징

### 모델 변경

`ai-mock-interview.py` 파일에서 모델명 수정:

```python
# 10번째 줄
MODEL_NAME = "qwen2.5:7b"  # 원하는 모델로 변경
```

### 질문 수 조정

```python
# 16번째 줄
self.max_questions = 8  # 원하는 질문 수로 변경
```

### 타임아웃 설정

```python
# 65번째 줄
timeout=360  # 초 단위 (기본: 6분)
```

## 문제 해결

### 일반적인 문제들

#### 1. "Ollama 서버에 연결할 수 없습니다"
```bash
# 해결책: Ollama 서버 시작
ollama serve
```

#### 2. "응답 시간이 초과되었습니다"
```bash
# 해결책: 더 작은 모델 사용
ollama pull llama3.2:latest
# 또는 timeout 시간 늘리기
```

#### 3. "메모리 부족 오류"
```bash
# 해결책: 다른 프로그램 종료 후 재시작
ollama rm large_model
ollama pull smaller_model
```

#### 4. "모델을 찾을 수 없습니다"
```bash
# 해결책: 모델명 확인
ollama list
```

### 성능 최적화

#### 메모리 부족 시
1. **브라우저 탭 정리**
2. **불필요한 프로그램 종료**
3. **더 작은 모델 사용**
4. **가상 메모리 증가**

#### 속도 개선
1. **SSD 사용 권장**
2. **충분한 RAM 확보**
3. **백그라운드 앱 최소화**

## 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE) 하에 배포됩니다.

## 감사의 말

- **[Ollama](https://ollama.ai)** - 로컬 LLM 실행 플랫폼
- **[Streamlit](https://streamlit.io)** - 웹 애플리케이션 프레임워크
- **[Meta](https://github.com/facebookresearch/llama)** - Llama 모델
- **[Alibaba](https://github.com/QwenLM/Qwen)** - Qwen 모델

---

**⭐ 이 프로젝트가 도움이 되셨다면 Star를 눌러주세요!**
