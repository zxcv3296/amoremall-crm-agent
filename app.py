# -*- coding: utf-8 -*-
# app.py
"""
AMORE Voice Agent - 피그마 디자인 완벽 구현
"""

import streamlit as st
import sys
import os
import base64

# 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.personas import personas, brand_tones, PURPOSE_OPTIONS
from core.rag_engine import ProductRAG
from core.message_generator import MessageGenerator
from ml.persona_classifier_hybrid import HybridPersonaClassifier
from core.churn_calculator import get_churn_details, get_dormancy_status, check_purpose_eligibility
from core.customer_analytics import get_full_customer_analysis, get_quick_summary, classify_customer_type, get_shopping_persona, get_message_priority

# 폰트 로드 함수
def load_font_as_base64(font_path):
    try:
        with open(font_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

# 폰트 경로
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pont", "Arita Dotum KR")
FONT_MEDIUM = os.path.join(FONT_DIR, "AritaDotumKR-Medium.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "AritaDotumKR-Bold.ttf")
FONT_SEMIBOLD = os.path.join(FONT_DIR, "AritaDotumKR-SemiBold.ttf")

# 페이지 설정
st.set_page_config(
    page_title="AMORE Voice Agent",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 폰트 base64 로드
font_medium_b64 = load_font_as_base64(FONT_MEDIUM)
font_bold_b64 = load_font_as_base64(FONT_BOLD)
font_semibold_b64 = load_font_as_base64(FONT_SEMIBOLD)

# 폰트 face 정의
font_face_css = ""
if font_medium_b64:
    font_face_css += f"""
    @font-face {{
        font-family: 'Arita Dotum';
        src: url(data:font/truetype;charset=utf-8;base64,{font_medium_b64}) format('truetype');
        font-weight: 500;
    }}
    """
if font_bold_b64:
    font_face_css += f"""
    @font-face {{
        font-family: 'Arita Dotum';
        src: url(data:font/truetype;charset=utf-8;base64,{font_bold_b64}) format('truetype');
        font-weight: 700;
    }}
    """
if font_semibold_b64:
    font_face_css += f"""
    @font-face {{
        font-family: 'Arita Dotum';
        src: url(data:font/truetype;charset=utf-8;base64,{font_semibold_b64}) format('truetype');
        font-weight: 600;
    }}
    """

# ============ 피그마 디자인 CSS (색상: #3074FF, #F1F1F1, #AAAAAA) ============
st.markdown(f"""
<style>
    {font_face_css}

    /* 전체 폰트 적용 */
    html, body, [class*="css"], .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, span, div {{
        font-family: 'Arita Dotum', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }}

    /* 메인 배경 - 흰색 */
    .main {{
        background: #FFFFFF;
        padding-top: 0 !important;
    }}

    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }}

    /* 사이드바 - 피그마 스타일 */
    [data-testid="stSidebar"] {{
        background: #FFFFFF;
        border-right: 1px solid #E5E7EB;
        width: 260px !important;
    }}

    [data-testid="stSidebar"] > div:first-child {{
        padding: 1rem 1rem;
    }}

    /* 사이드바 헤더 */
    .sidebar-title {{
        font-size: 0.9rem;
        font-weight: 600;
        color: #111827;
        margin-bottom: 0.75rem;
        margin-top: 0.5rem;
    }}

    .sidebar-label {{
        font-size: 0.8rem;
        font-weight: 500;
        color: #374151;
        margin-bottom: 0.3rem;
        margin-top: 0.75rem;
    }}

    /* 셀렉트박스 스타일 */
    .stSelectbox > div > div {{
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        font-size: 0.85rem;
    }}

    /* 연결 상태 - 피그마 체크박스 스타일 */
    .connection-box {{
        background: #EBF3FF;
        border: 1px solid #3074FF;
        border-radius: 6px;
        padding: 0.5rem 0.75rem;
        margin: 0.5rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    .connection-box .check {{
        width: 16px;
        height: 16px;
        background: #3074FF;
        border-radius: 3px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 0.7rem;
    }}

    .connection-box .text {{
        color: #3074FF;
        font-size: 0.8rem;
        font-weight: 500;
    }}

    /* AI 추천 카드 - 피그마 파란 배경 */
    .ai-recommend-card {{
        background: #3074FF;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        color: white;
    }}

    .ai-recommend-card .label {{
        font-size: 0.75rem;
        opacity: 0.9;
        margin-bottom: 0.25rem;
    }}

    .ai-recommend-card .value {{
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }}

    .ai-recommend-card .confidence {{
        font-size: 0.8rem;
    }}

    /* 추천 이유 버튼 */
    .reason-btn {{
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 0.5rem 0.75rem;
        font-size: 0.8rem;
        color: #374151;
        width: 100%;
        cursor: pointer;
        margin-top: 0.5rem;
    }}

    /* 성능 평가 섹션 */
    .eval-section {{
        margin-top: 1rem;
        padding-top: 0.75rem;
        border-top: 1px solid #E5E7EB;
    }}

    .eval-title {{
        font-size: 0.85rem;
        font-weight: 600;
        color: #111827;
        margin-bottom: 0.5rem;
    }}

    .eval-item {{
        background: #F1F1F1;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 0.4rem 0.6rem;
        margin-bottom: 0.4rem;
    }}

    .eval-item .label {{
        font-size: 0.7rem;
        color: #AAAAAA;
    }}

    .eval-item .value {{
        font-size: 0.8rem;
        color: #059669;
        font-weight: 500;
    }}

    /* 버튼 스타일 - 피그마 둥근 버튼 */
    .stButton > button {{
        background: #3074FF !important;
        color: white !important;
        border: none !important;
        border-radius: 20px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }}

    .stButton > button:hover {{
        background: #2060E0 !important;
    }}

    /* 저장 섹션 */
    .save-section {{
        margin-top: 1rem;
        padding-top: 0.75rem;
        border-top: 1px solid #E5E7EB;
    }}

    .save-title {{
        font-size: 0.85rem;
        font-weight: 600;
        color: #111827;
        margin-bottom: 0.5rem;
    }}

    /* ===== 메인 영역 ===== */

    /* 타이틀 - 피그마 파란색 #3074FF */
    .main-title {{
        color: #3074FF;
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 1.25rem;
        margin-top: 0;
    }}

    /* 섹션 타이틀 */
    .section-title {{
        font-size: 0.95rem;
        font-weight: 600;
        color: #111827;
        margin-bottom: 0.6rem;
    }}

    /* 고객 정보 카드 - 피그마 회색 배경 + 그림자 (블러10, 스프레드5, 불투명도15%) */
    .customer-card {{
        background: #F1F1F1;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px 3px rgba(0,0,0,0.12);
    }}

    .customer-name {{
        font-size: 1rem;
        font-weight: 600;
        color: #111827;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    .customer-name .badge {{
        background: #3074FF;
        color: white;
        font-size: 0.65rem;
        padding: 0.1rem 0.35rem;
        border-radius: 3px;
        font-weight: 600;
    }}

    .customer-info-item {{
        font-size: 0.85rem;
        color: #374151;
        margin-bottom: 0.3rem;
        line-height: 1.5;
    }}

    .customer-info-item::before {{
        content: "• ";
        color: #AAAAAA;
    }}

    /* 발신 목적 / 고객 페르소나 카드 - 피그마 + 그림자 (블러10, 스프레드5, 불투명도15%) */
    .card-row {{
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }}

    .info-card {{
        flex: 1;
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        box-shadow: 0 2px 10px 3px rgba(0,0,0,0.12);
    }}

    .info-card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }}

    .info-card-title {{
        font-size: 0.9rem;
        font-weight: 600;
        color: #111827;
    }}

    .info-card-link {{
        font-size: 0.7rem;
        color: #AAAAAA;
    }}

    .info-card-subtitle {{
        font-size: 0.85rem;
        font-weight: 600;
        color: #111827;
        margin-bottom: 0.4rem;
    }}

    .info-card-list {{
        font-size: 0.8rem;
        color: #AAAAAA;
        line-height: 1.6;
    }}

    .info-card-list-item {{
        margin-bottom: 0.2rem;
    }}

    .info-card-list-item::before {{
        content: "• ";
        color: #AAAAAA;
    }}

    /* 추천 상품 - 피그마 3열 + 그림자 (블러10, 스프레드5, 불투명도15%) */
    .products-row {{
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }}

    .product-card {{
        flex: 1;
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 0.75rem;
        box-shadow: 0 2px 10px 3px rgba(0,0,0,0.12);
    }}

    .product-name {{
        font-size: 0.8rem;
        color: #111827;
        font-weight: 500;
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }}

    .product-discount {{
        color: #EF4444;
        font-size: 0.85rem;
        font-weight: 700;
    }}

    .product-original {{
        color: #AAAAAA;
        font-size: 0.75rem;
        text-decoration: line-through;
        margin-left: 0.3rem;
    }}

    .product-price {{
        color: #111827;
        font-size: 0.9rem;
        font-weight: 700;
    }}

    /* 생성된 메시지 - 피그마 + 그림자 (블러10, 스프레드5, 불투명도15%) */
    .message-box {{
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 10px 3px rgba(0,0,0,0.12);
    }}

    .message-title-row {{
        background: #F1F1F1;
        border-radius: 6px;
        padding: 0.6rem 0.75rem;
        margin-bottom: 0.75rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .message-title-text {{
        font-size: 0.9rem;
        color: #111827;
    }}

    .message-char-count {{
        font-size: 0.75rem;
        color: #059669;
    }}

    .message-body {{
        font-size: 0.85rem;
        color: #374151;
        line-height: 1.8;
        padding: 0.5rem;
        white-space: pre-wrap;
    }}

    .message-body-footer {{
        display: flex;
        justify-content: flex-end;
        margin-top: 0.5rem;
    }}

    /* Expander 아이콘 숨기기 */
    [data-testid="stExpander"] [data-testid="stExpanderToggleIcon"] {{
        display: none !important;
    }}

    [data-testid="stExpander"] summary::before {{
        content: "▸ " !important;
        font-size: 0.8rem;
        color: #AAAAAA;
    }}

    [data-testid="stExpander"] details[open] summary::before {{
        content: "▾ " !important;
    }}

    /* 사이드바 collapse 버튼 숨기기 */
    [data-testid="collapsedControl"],
    button[kind="headerNoPadding"] {{
        display: none !important;
    }}

    /* 스크롤바 */
    ::-webkit-scrollbar {{
        width: 6px;
    }}

    ::-webkit-scrollbar-track {{
        background: #F1F1F1;
    }}

    ::-webkit-scrollbar-thumb {{
        background: #AAAAAA;
        border-radius: 3px;
    }}
</style>
""", unsafe_allow_html=True)

# API 키 자동 로드
def get_api_key(key_name="HF_API_KEY"):
    try:
        return st.secrets[key_name]
    except:
        return None

# 모델 옵션 (message_generator.py SUPPORTED_MODELS와 일치해야 함)
MODEL_OPTIONS = {
    "Qwen/Qwen2.5-7B-Instruct": "Qwen 2.5 7B (HuggingFace API, 무료)",
    "exaone3.5:7.8b": "EXAONE 3.5 7.8B (Ollama, 한국어 특화)",
    "qwen2.5:7b": "Qwen 2.5 7B (Ollama, 로컬)",
    "gpt-4o-mini": "GPT-4o-mini (₩0.33/건)",
    "gpt-4o": "GPT-4o (₩5.5/건)",
}

# 세션 상태 초기화
if 'api_key' not in st.session_state:
    st.session_state.api_key = get_api_key("HF_API_KEY") or ""
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = get_api_key("OPENAI_API_KEY") or ""
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = "exaone3.5:7.8b"
if 'message_history' not in st.session_state:
    st.session_state.message_history = []
if 'ai_purpose_recommendation' not in st.session_state:
    st.session_state.ai_purpose_recommendation = None
if 'last_persona_id' not in st.session_state:
    st.session_state.last_persona_id = None
if 'persona_classifier' not in st.session_state:
    st.session_state.persona_classifier = HybridPersonaClassifier()
if 'ml_persona_prediction' not in st.session_state:
    st.session_state.ml_persona_prediction = None

# ============ 사이드바 - 피그마 스타일 ============
with st.sidebar:
    st.markdown('<p class="sidebar-title">설정</p>', unsafe_allow_html=True)

    # LLM 모델
    st.markdown('<p class="sidebar-label">LLM 모델</p>', unsafe_allow_html=True)
    # 세션의 모델이 목록에 없으면 첫 번째 모델로 초기화
    model_keys = list(MODEL_OPTIONS.keys())
    if st.session_state.selected_model not in model_keys:
        st.session_state.selected_model = model_keys[0]
    selected_model = st.selectbox(
        "모델",
        model_keys,
        format_func=lambda x: MODEL_OPTIONS[x],
        index=model_keys.index(st.session_state.selected_model),
        label_visibility="collapsed"
    )
    st.session_state.selected_model = selected_model

    # 연결 상태 - 피그마 체크박스 스타일
    model_name = MODEL_OPTIONS[selected_model]
    st.markdown(f'''
    <div class="connection-box">
        <div class="check">✓</div>
        <span class="text">{model_name} 연결됨</span>
    </div>
    ''', unsafe_allow_html=True)

    # 모델별 비용/품질 비교
    with st.expander("모델별 비용/품질 비교"):
        st.markdown("""
        **GPT-4o-mini** - ₩0.33/건 (추천)
        **Qwen 2.5 7B** - 무료
        """)

    # GPT 모델 선택 시 API 키 입력란 표시
    if selected_model.startswith("gpt"):
        st.markdown('<p class="sidebar-label">OpenAI API Key</p>', unsafe_allow_html=True)
        openai_key_input = st.text_input(
            "OpenAI API Key",
            value=st.session_state.openai_api_key,
            type="password",
            label_visibility="collapsed",
            placeholder="sk-..."
        )
        st.session_state.openai_api_key = openai_key_input
        if not openai_key_input:
            st.warning("⚠️ GPT 모델 사용을 위해 API 키를 입력하세요")

    # HuggingFace API 모델 선택 시 API 키 입력란 표시
    if selected_model.startswith("Qwen/"):
        st.markdown('<p class="sidebar-label">HuggingFace API Key</p>', unsafe_allow_html=True)
        hf_key_input = st.text_input(
            "HuggingFace API Key",
            value=st.session_state.api_key,
            type="password",
            label_visibility="collapsed",
            placeholder="hf_..."
        )
        st.session_state.api_key = hf_key_input
        if not hf_key_input:
            st.warning("⚠️ HuggingFace 모델 사용을 위해 API 키를 입력하세요")

    st.markdown("<br>", unsafe_allow_html=True)

    # 메시지 미리보기
    st.markdown('<p class="sidebar-label">메시지 미리보기</p>', unsafe_allow_html=True)

    # 고객 ID
    st.markdown('<p style="font-size:0.75rem; color:#6B7280; margin-bottom:0.2rem;">고객 ID</p>', unsafe_allow_html=True)
    persona_options = [f"{p['display_name']} - {p['skin_type']}" for p in personas]
    selected_idx = st.selectbox(
        "고객",
        range(len(persona_options)),
        format_func=lambda i: persona_options[i],
        label_visibility="collapsed"
    )
    selected_persona = personas[selected_idx]

    st.markdown("<br>", unsafe_allow_html=True)

    # AI 발신 목적 추천
    st.markdown('<p class="sidebar-label">AI 발신 목적 추천</p>', unsafe_allow_html=True)

    # AI 추천 자동 실행 (customer_analytics 기반)
    if st.session_state.last_persona_id != selected_persona['id']:
        st.session_state.last_persona_id = selected_persona['id']
        try:
            st.session_state.ai_purpose_recommendation = get_message_priority(selected_persona)
        except:
            st.session_state.ai_purpose_recommendation = None

        # ML 페르소나 예측
        try:
            ml_input = {
                "age": selected_persona.get('age', 30),
                "skin_type": selected_persona.get('skin_type', '복합성'),
                "primary_brand": selected_persona.get('brand', {}).get('primary_brand', ''),
                "loyalty": selected_persona.get('brand', {}).get('loyalty', '중'),
                "diversity": selected_persona.get('brand', {}).get('diversity', 0.5),
                "discount_sensitivity": selected_persona.get('promotion', {}).get('discount_sensitivity', '중간'),
                "full_price_ratio": selected_persona.get('promotion', {}).get('full_price_ratio', 0.5),
                "coupon_usage_rate": selected_persona.get('promotion', {}).get('coupon_usage_rate', 0.5),
                "visit_frequency": selected_persona.get('activity', {}).get('visit_frequency', '중'),
                "total_count": selected_persona.get('purchase', {}).get('total_count', 0),
                "avg_amount": selected_persona.get('purchase', {}).get('avg_amount', 30000),
                "membership_tier": selected_persona.get('membership', {}).get('tier', 'M')[0] if selected_persona.get('membership', {}).get('tier') else 'M'
            }
            st.session_state.ml_persona_prediction = st.session_state.persona_classifier.predict(ml_input)
        except:
            st.session_state.ml_persona_prediction = None

    if st.session_state.ai_purpose_recommendation is None:
        try:
            st.session_state.ai_purpose_recommendation = get_message_priority(selected_persona)
        except:
            pass

    # AI 추천 카드 - 피그마 파란 배경
    ai_rec = st.session_state.ai_purpose_recommendation
    if ai_rec:
        purpose_name = ai_rec.get('priority_name', '참여유도')
        confidence = 0.85  # 규칙 기반 고정 신뢰도
        st.markdown(f'''
        <div class="ai-recommend-card">
            <div class="label">AI 추천</div>
            <div class="value">{purpose_name}</div>
            <div class="confidence">신뢰도: {confidence*100:.0f}%</div>
        </div>
        ''', unsafe_allow_html=True)

        # 추천 이유 버튼
        with st.expander("추천 이유"):
            st.write(ai_rec.get('reason', '고객 행동 데이터 기반 추천'))

    st.markdown("<br>", unsafe_allow_html=True)

    # 추천 상품 수
    st.markdown('<p class="sidebar-label">추천 상품 수</p>', unsafe_allow_html=True)
    num_products = st.slider("상품 수", 1, 5, 3, label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    # AI 메시지 생성 버튼
    generate_btn = st.button("AI 메시지 생성", use_container_width=True, type="primary")

    # 다시 생성하기
    st.button("다시 생성하기", use_container_width=True)

    # 추천 모델 성능 평가
    st.markdown('<div class="eval-section">', unsafe_allow_html=True)
    st.markdown('<p class="eval-title">추천 모델 성능 평가</p>', unsafe_allow_html=True)

    st.markdown('''
    <div class="eval-item">
        <div class="label">발신 목적 자동 분류</div>
        <div class="value">✓ 정확도 00.0%</div>
    </div>
    <div class="eval-item">
        <div class="label">페르소나 자동 분류</div>
        <div class="value">✓ 정확도 00.0%</div>
    </div>
    <div class="eval-item">
        <div class="label">추천 상품 자동 선정</div>
        <div class="value">✓ 정확도 00.0%</div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 결과 저장
    st.markdown('<div class="save-section">', unsafe_allow_html=True)
    st.markdown('<p class="save-title">결과 저장</p>', unsafe_allow_html=True)
    st.selectbox("파일 형식", ["CSV", "JSON", "TXT"], label_visibility="collapsed")
    st.button("메시지 내보내기", use_container_width=True, type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

# ============ RAG/Generator 초기화 ============
if 'rag' not in st.session_state:
    with st.spinner("RAG 초기화 중..."):
        try:
            st.session_state.rag = ProductRAG()
        except Exception as e:
            st.error(f"RAG 초기화 실패: {str(e)}")

def get_generator():
    current_model = st.session_state.get('selected_model', 'qwen2.5:7b')
    hf_key = st.session_state.get('api_key', '')
    openai_key = st.session_state.get('openai_api_key', '')
    return MessageGenerator(
        api_key=hf_key if hf_key else None,
        openai_api_key=openai_key if openai_key else None,
        model=current_model,
        temperature=0.7
    )

try:
    generator = get_generator()
except Exception as e:
    st.error(f"Generator 초기화 실패: {str(e)}")
    generator = None

# ============ 메인 영역 - 피그마 레이아웃 ============

# 타이틀
st.markdown('<h1 class="main-title">AMORE Voice Agent</h1>', unsafe_allow_html=True)

# 고객 정보 섹션
st.markdown('<p class="section-title">고객 정보</p>', unsafe_allow_html=True)

# 고객 정보 카드 - 피그마 스타일
customer_name = selected_persona['display_name']
skin_type = selected_persona['skin_type']
concerns = ', '.join(selected_persona['concerns'])
interests = ', '.join(selected_persona.get('interests', ['스킨케어']))

# 관심 브랜드/카테고리 (피그마 예시)
interest_brands = "오설록, 롱테이크, 퍼퓸우드, 메이크온, 한율"
interest_categories = "향수 > 향수, 메이크업 > 페이스, 스킨케어 > 클렌징"

st.markdown(f'''
<div class="customer-card">
    <div class="customer-name">
        {customer_name} <span class="badge">M</span>
    </div>
    <div class="customer-info-item">피부 타입 : {skin_type}</div>
    <div class="customer-info-item">피부 고민 : {concerns}</div>
    <div class="customer-info-item">관심 브랜드 : {interest_brands}</div>
    <div class="customer-info-item">관심 카테고리 : {interest_categories}</div>
    <div class="customer-info-item">선호 프로모션 : 쿠폰</div>
</div>
''', unsafe_allow_html=True)

# 발신 목적 (AI 추천) + 고객 페르소나 - 2열 (순수 HTML - 한 줄로 작성)
purpose_name = ai_rec.get('priority_name', '전환 유도') if ai_rec else '전환 유도'
ml_pred = st.session_state.ml_persona_prediction
persona_type = ml_pred.get('persona', '합리적 큐레이터') if ml_pred else '합리적 큐레이터'

card_style = "flex: 1; background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; padding: 0.75rem 1rem; box-shadow: 0 2px 10px 3px rgba(0,0,0,0.12);"
header_style = "display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;"
title_style = "font-size: 0.9rem; font-weight: 600; color: #111827;"
link_style = "font-size: 0.7rem; color: #AAAAAA;"
subtitle_style = "font-size: 0.85rem; font-weight: 600; color: #111827; margin-bottom: 0.4rem;"
list_style = "font-size: 0.8rem; color: #AAAAAA; line-height: 1.6;"
item_style = "margin-bottom: 0.2rem;"

purpose_card = f'<div style="{card_style}"><div style="{header_style}"><span style="{title_style}">발신 목적 (AI 추천)</span><span style="{link_style}">ⓘ 이 발신목적이 추천된 이유</span></div><div style="{subtitle_style}">{purpose_name}</div><div style="{list_style}"><div style="{item_style}">• 최근 30일 탐색(방문, 조회), 참여(찜, 장바구니) 있음</div><div style="{item_style}">• 최근 30일 구매 없음</div><div>• 구매를 자연스럽게 고려하도록 돕는 전환 유도 메시지 필요</div></div></div>'

persona_card = f'<div style="{card_style}"><div style="{header_style}"><span style="{title_style}">고객 페르소나</span><span style="{link_style}">ⓘ 페르소나 분류 이유</span></div><div style="{subtitle_style}">{persona_type}</div><div style="{list_style}"><div style="{item_style}">• 실패 없는 선택을 위해 랭킹과 리뷰를 신뢰하는 2845 직장인</div><div style="{item_style}">• 베스트템과 리뷰를 기반으로 검증된 제품만 구매하는 성향</div><div>• 할인 이벤트 시 베스트템을 챙겨두는 합리적 쇼핑 패턴</div></div></div>'

cards_html = f'<div style="display: flex; gap: 1rem; margin-bottom: 1rem;">{purpose_card}{persona_card}</div>'
st.markdown(cards_html, unsafe_allow_html=True)

# 메시지 생성 로직
selected_purpose_id = ai_rec.get('recommended_purpose', 'promotion') if ai_rec else 'promotion'

if generate_btn:
    if 'rag' not in st.session_state:
        st.error("시스템 초기화 필요")
        st.stop()

    with st.spinner("상품 검색 중..."):
        try:
            retrieved_products = st.session_state.rag.retrieve_products(
                selected_persona, brand, purpose=selected_purpose_id, k=num_products
            )
            if not retrieved_products:
                st.warning("상품을 찾지 못했습니다.")
                st.stop()
        except Exception as e:
            st.error(f"상품 검색 실패: {str(e)}")
            st.stop()

    with st.spinner("메시지 생성 중..."):
        try:
            message = generator.generate(
                selected_persona, brand, selected_purpose_id, retrieved_products
            )
        except Exception as e:
            st.error(f"메시지 생성 실패: {str(e)}")
            st.stop()

    st.session_state.last_result = {
        'title': message.get('title', ''),
        'body': message.get('body', ''),
        'products': retrieved_products,
        'persona': selected_persona,
        'brand': brand,
        'purpose': selected_purpose_id,
        'debug_info': message.get('debug_info')
    }

# 추천 상품 섹션
st.markdown('<p class="section-title">추천 상품</p>', unsafe_allow_html=True)

if 'last_result' in st.session_state and st.session_state.last_result:
    products = st.session_state.last_result['products']

    # 상품 카드 개별 생성
    product_cards = []
    for i, product in enumerate(products[:3]):
        name = product.get('name', '상품명')
        price = product.get('price', 0)
        discount = product.get('discount_rate', 0)

        if discount > 0:
            original = int(price / (1 - discount / 100))
            price_html = f'<div style="margin-top: 0.5rem;"><span style="color: #EF4444; font-size: 0.85rem; font-weight: 700;">{discount}%</span><span style="color: #AAAAAA; font-size: 0.75rem; text-decoration: line-through; margin-left: 0.3rem;">{original:,}원</span></div><div style="color: #111827; font-size: 0.9rem; font-weight: 700;">{price:,}원</div>'
        else:
            price_html = f'<div style="color: #111827; font-size: 0.9rem; font-weight: 700; margin-top: 0.5rem;">{price:,}원</div>'

        card_html = f'<div style="flex: 1; background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; padding: 0.75rem; box-shadow: 0 2px 10px 3px rgba(0,0,0,0.12);"><div style="font-size: 0.8rem; color: #111827; font-weight: 500; line-height: 1.4;">{name}</div>{price_html}</div>'
        product_cards.append(card_html)

    # 3개 미만이면 빈 카드 추가
    for _ in range(3 - len(products[:3])):
        product_cards.append('<div style="flex: 1; background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; padding: 0.75rem; box-shadow: 0 2px 10px 3px rgba(0,0,0,0.12);"><div style="font-size: 0.8rem; color: #AAAAAA;">상품 없음</div></div>')

    product_cards_html = '<div style="display: flex; gap: 1rem; margin-bottom: 1rem;">' + ''.join(product_cards) + '</div>'
    st.markdown(product_cards_html, unsafe_allow_html=True)
else:
    # 기본 상품 (피그마 예시) - 한 줄로 작성
    card_style = "flex: 1; background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; padding: 0.75rem; box-shadow: 0 2px 10px 3px rgba(0,0,0,0.12);"
    default_card = f'<div style="{card_style}"><div style="font-size: 0.8rem; color: #111827; font-weight: 500; line-height: 1.4;">[브랜드] 블루 에너지 에센스 인 로션 EX 125ml</div><div style="margin-top: 0.5rem;"><span style="color: #EF4444; font-size: 0.85rem; font-weight: 700;">10%</span><span style="color: #AAAAAA; font-size: 0.75rem; text-decoration: line-through; margin-left: 0.3rem;">135,000원</span></div><div style="color: #111827; font-size: 0.9rem; font-weight: 700;">121,500원</div></div>'
    default_products_html = f'<div style="display: flex; gap: 1rem; margin-bottom: 1rem;">{default_card}{default_card}{default_card}</div>'
    st.markdown(default_products_html, unsafe_allow_html=True)

# 생성된 메시지 섹션
st.markdown('<p class="section-title">생성된 메시지</p>', unsafe_allow_html=True)

if 'last_result' in st.session_state and st.session_state.last_result:
    result = st.session_state.last_result
    title = result['title']
    body = result['body']
    title_len = len(title)
    body_len = len(body)

    # 검증 결과 확인
    validation = result.get('validation', {})
    is_valid = validation.get('valid', True)
    issues = validation.get('issues', [])

    # 글자수 표시 스타일 (검증 통과 여부에 따라)
    title_status = "✓" if title_len <= 40 else "✗"
    body_status = "✓" if 300 <= body_len <= 350 else "⚠"
    body_color = "#10B981" if 300 <= body_len <= 350 else "#F59E0B"

    st.markdown(f'''
    <div class="message-box">
        <div class="message-title-row">
            <span class="message-title-text">{title}</span>
            <span class="message-char-count">{title_status} {title_len}/40자</span>
        </div>
        <div class="message-body">{body}</div>
        <div class="message-body-footer">
            <span class="message-char-count" style="color: {body_color}">{body_status} {body_len}/350자</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # 검증 실패 시 경고 표시
    if not is_valid and issues:
        issues_text = " | ".join(issues)
        st.warning(f"⚠️ 품질 검증: {issues_text}")
else:
    # 기본 메시지 (피그마 예시)
    default_title = "아모레님, 하루의 끝에 힐링을 선물해 줄 [오설록] 제품명 어쩌구를 추천드려요 🍵"
    default_body = """바쁜 일상 속에도 피부 건강을 잊지 않는 민지님!
라네즈가 당신을 위해 특별한 프로모션을 준비했습니다. 복합성 피부의 모공과 피지 고민을 효과적으로 해결할 블루 에너지 세트를 만나보세요.
블루 에너지 에센스 인 로션 EX, 래디언씨 선크림, 블루 에너지 스킨 토너 EX 모두 40% 할인을 받아요. 지금 바로 이 기회를 놓치지 마세요!
오늘이 마지막일 수 있어요."""

    st.markdown(f'''
    <div class="message-box">
        <div class="message-title-row">
            <span class="message-title-text">{default_title}</span>
            <span class="message-char-count">✓ 39/40자</span>
        </div>
        <div class="message-body">{default_body}</div>
        <div class="message-body-footer">
            <span class="message-char-count">✓ 344/350자</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
