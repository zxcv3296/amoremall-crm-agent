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
from ml.purpose_recommender import PurposeRecommender
from ml.persona_classifier import PersonaClassifier
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
        padding-top: 1rem !important;
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

    /* 고객 정보 카드 - 피그마 회색 배경 + 그림자 */
    .customer-card {{
        background: #F1F1F1;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
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

    /* 발신 목적 / 고객 페르소나 카드 - 피그마 + 그림자 */
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
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
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

    /* 추천 상품 - 피그마 3열 + 그림자 */
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
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
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

    /* 생성된 메시지 - 피그마 + 그림자 */
    .message-box {{
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
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

# 모델 옵션
MODEL_OPTIONS = {
    "qwen2.5:7b": "Qwen 2.5 7B (무료)",
    "Qwen/Qwen2.5-7B-Instruct": "Qwen 2.5 7B HuggingFace (무료)",
    "gpt-4.1-nano": "GPT-4.1 Nano (₩0.22/건)",
    "gpt-4o-mini": "GPT-4o-mini (₩0.33/건)",
    "gpt-4.1-mini": "GPT-4.1 Mini (₩0.88/건)",
    "gpt-4.1": "GPT-4.1 (₩4.4/건)"
}

# 세션 상태 초기화
if 'api_key' not in st.session_state:
    st.session_state.api_key = get_api_key("HF_API_KEY") or ""
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = get_api_key("OPENAI_API_KEY") or ""
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = "qwen2.5:7b"
if 'message_history' not in st.session_state:
    st.session_state.message_history = []
if 'ai_purpose_recommendation' not in st.session_state:
    st.session_state.ai_purpose_recommendation = None
if 'last_persona_id' not in st.session_state:
    st.session_state.last_persona_id = None
if 'persona_classifier' not in st.session_state:
    st.session_state.persona_classifier = PersonaClassifier()
if 'ml_persona_prediction' not in st.session_state:
    st.session_state.ml_persona_prediction = None

# ============ 사이드바 - 피그마 스타일 ============
with st.sidebar:
    st.markdown('<p class="sidebar-title">설정</p>', unsafe_allow_html=True)

    # LLM 모델
    st.markdown('<p class="sidebar-label">LLM 모델</p>', unsafe_allow_html=True)
    selected_model = st.selectbox(
        "모델",
        list(MODEL_OPTIONS.keys()),
        format_func=lambda x: MODEL_OPTIONS[x],
        index=list(MODEL_OPTIONS.keys()).index(st.session_state.selected_model),
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

    # 브랜드
    st.markdown('<p class="sidebar-label">브랜드</p>', unsafe_allow_html=True)
    brand = st.selectbox(
        "브랜드",
        list(brand_tones.keys()),
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # AI 발신 목적 추천
    st.markdown('<p class="sidebar-label">AI 발신 목적 추천</p>', unsafe_allow_html=True)

    # AI 추천 자동 실행
    if st.session_state.last_persona_id != selected_persona['id']:
        st.session_state.last_persona_id = selected_persona['id']
        try:
            recommender = PurposeRecommender()
            st.session_state.ai_purpose_recommendation = recommender.recommend_purpose(selected_persona)
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
            recommender = PurposeRecommender()
            st.session_state.ai_purpose_recommendation = recommender.recommend_purpose(selected_persona)
        except:
            pass

    # AI 추천 카드 - 피그마 파란 배경
    ai_rec = st.session_state.ai_purpose_recommendation
    if ai_rec:
        purpose_name = ai_rec.get('purpose_name', '신제품 안내')
        confidence = ai_rec.get('confidence', 0.89)
        st.markdown(f'''
        <div class="ai-recommend-card">
            <div class="label">AI 추천</div>
            <div class="value">{purpose_name}</div>
            <div class="confidence">신뢰도: {confidence*100:.0f}%</div>
        </div>
        ''', unsafe_allow_html=True)

        # 추천 이유 버튼
        with st.expander("추천 이유"):
            st.write(ai_rec.get('reasoning', '고객 행동 데이터 기반 추천'))

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

# 발신 목적 (AI 추천) + 고객 페르소나 - 2열
col1, col2 = st.columns(2)

with col1:
    purpose_name = ai_rec.get('purpose_name', '전환 유도') if ai_rec else '전환 유도'
    st.markdown(f'''
    <div class="info-card">
        <div class="info-card-header">
            <span class="info-card-title">발신 목적 (AI 추천)</span>
            <span class="info-card-link">ⓘ 이 발신목적이 추천된 이유</span>
        </div>
        <div class="info-card-subtitle">{purpose_name}</div>
        <div class="info-card-list">
            <div class="info-card-list-item">최근 30일 탐색(방문, 조회), 참여(찜, 장바구니) 있음</div>
            <div class="info-card-list-item">최근 30일 구매 없음</div>
            <div class="info-card-list-item">구매를 자연스럽게 고려하도록 돕는 전환 유도 메시지 필요</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

with col2:
    ml_pred = st.session_state.ml_persona_prediction
    persona_type = ml_pred.get('persona', '합리적 큐레이터') if ml_pred else '합리적 큐레이터'
    st.markdown(f'''
    <div class="info-card">
        <div class="info-card-header">
            <span class="info-card-title">고객 페르소나</span>
            <span class="info-card-link">ⓘ 페르소나 분류 이유</span>
        </div>
        <div class="info-card-subtitle">{persona_type}</div>
        <div class="info-card-list">
            <div class="info-card-list-item">실패 없는 선택을 위해 랭킹과 리뷰를 신뢰하는 2845 직장인</div>
            <div class="info-card-list-item">베스트템과 리뷰를 기반으로 검증된 제품만 구매하는 성향</div>
            <div class="info-card-list-item">할인 이벤트 시 베스트템을 챙겨두는 합리적 쇼핑 패턴</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

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
    cols = st.columns(3)

    for i, product in enumerate(products[:3]):
        with cols[i]:
            name = product.get('name', '상품명')
            price = product.get('price', 0)
            discount = product.get('discount_rate', 0)

            if discount > 0:
                original = int(price / (1 - discount / 100))
                price_html = f'''
                <div>
                    <span class="product-discount">{discount}%</span>
                    <span class="product-original">{original:,}원</span>
                </div>
                <div class="product-price">{price:,}원</div>
                '''
            else:
                price_html = f'<div class="product-price">{price:,}원</div>'

            st.markdown(f'''
            <div class="product-card">
                <div class="product-name">{name}</div>
                {price_html}
            </div>
            ''', unsafe_allow_html=True)
else:
    # 기본 상품 (피그마 예시)
    cols = st.columns(3)
    for i in range(3):
        with cols[i]:
            st.markdown(f'''
            <div class="product-card">
                <div class="product-name">[브랜드] 블루 에너지 에센스 인 로션 EX 125ml</div>
                <div>
                    <span class="product-discount">10%</span>
                    <span class="product-original">135,000원</span>
                </div>
                <div class="product-price">121,500원</div>
            </div>
            ''', unsafe_allow_html=True)

# 생성된 메시지 섹션
st.markdown('<p class="section-title">생성된 메시지</p>', unsafe_allow_html=True)

if 'last_result' in st.session_state and st.session_state.last_result:
    result = st.session_state.last_result
    title = result['title']
    body = result['body']
    title_len = len(title)
    body_len = len(body)

    st.markdown(f'''
    <div class="message-box">
        <div class="message-title-row">
            <span class="message-title-text">{title}</span>
            <span class="message-char-count">✓ {title_len}/40자</span>
        </div>
        <div class="message-body">{body}</div>
        <div class="message-body-footer">
            <span class="message-char-count">✓ {body_len}/350자</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
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
