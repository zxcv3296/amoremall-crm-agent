# -*- coding: utf-8 -*-
# app.py
"""
아모레몰 CRM 메시지 자동 생성 시스템 - Streamlit UI (v3 - AI 발신목적 추천)
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
    """폰트 파일을 base64로 인코딩"""
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
    page_title="아모레몰 CRM Agent",
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

# 커스텀 CSS - 새로운 디자인 (#3074FF, #F1F1F1, #AAAAAA)
st.markdown(f"""
<style>
    {font_face_css}

    /* 전체 폰트 적용 */
    html, body, [class*="css"], .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, span, div {{
        font-family: 'Arita Dotum', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }}

    /* 메인 컨테이너 */
    .main {{
        background: #F1F1F1;
    }}

    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {{
        background: white;
        box-shadow: 5px 0 10px rgba(0,0,0,0.05);
    }}

    [data-testid="stSidebar"] [data-testid="stMarkdown"] {{
        color: #333;
    }}

    /* 사이드바 텍스트 겹침 방지 */
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown h4 {{
        white-space: normal;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    /* 사이드바 expander 내부 테이블 */
    [data-testid="stSidebar"] .cost-table {{
        width: 100%;
        table-layout: fixed;
    }}

    [data-testid="stSidebar"] .cost-table td {{
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    /* 사이드바 카드 오버플로우 */
    [data-testid="stSidebar"] .model-card {{
        overflow: hidden;
    }}

    [data-testid="stSidebar"] .model-card p {{
        margin: 0.2rem 0;
        line-height: 1.4;
    }}

    /* ===== Material Icons 깨진 텍스트 완전 숨김 ===== */

    /* Streamlit Expander 기본 스타일 재정의 */
    [data-testid="stExpander"] {{
        border: none !important;
    }}

    [data-testid="stExpander"] summary {{
        list-style: none !important;
        cursor: pointer;
    }}

    [data-testid="stExpander"] summary::-webkit-details-marker {{
        display: none !important;
    }}

    /* 아이콘 컨테이너 완전 숨김 - 더 강력한 선택자 */
    [data-testid="stExpander"] [data-testid="stExpanderToggleIcon"],
    [data-testid="stExpander"] summary svg,
    [data-testid="stExpander"] summary [data-testid="stIconMaterial"],
    [data-testid="stExpander"] summary span[class*="icon"],
    [data-testid="stExpander"] summary > div > div:first-child:not([data-testid="stMarkdownContainer"]) {{
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        position: absolute !important;
        left: -9999px !important;
    }}

    /* Expander 헤더 레이아웃 */
    [data-testid="stExpander"] details > summary {{
        padding: 0.8rem 1rem !important;
        background: white !important;
        border-radius: 8px !important;
        position: relative !important;
    }}

    [data-testid="stExpander"] details > summary > div {{
        display: flex !important;
        align-items: center !important;
        margin-left: 1.2rem !important;
    }}

    /* CSS 기반 화살표 아이콘 - summary에 직접 적용 */
    [data-testid="stExpander"] details > summary::before {{
        content: "▶" !important;
        position: absolute !important;
        left: 1rem !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        font-size: 0.7rem !important;
        color: #666 !important;
        font-family: Arial, sans-serif !important;
        display: inline-block !important;
        z-index: 10 !important;
    }}

    [data-testid="stExpander"] details[open] > summary::before {{
        content: "▼" !important;
    }}

    /* Expander 헤더 텍스트 스타일 */
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span {{
        margin: 0 !important;
        font-weight: 500 !important;
    }}

    /* 사이드바 collapse 버튼 숨기기 */
    [data-testid="stSidebar"] button[kind="headerNoPadding"],
    [data-testid="collapsedControl"],
    button[data-testid="baseButton-headerNoPadding"],
    [data-testid="stSidebar"] > div > div:first-child > div > button {{
        display: none !important;
    }}

    /* 타이틀 스타일 */
    .title-container {{
        background: #3074FF;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 5px 10px rgba(0,0,0,0.15);
    }}

    .title-text {{
        color: white;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        text-align: left;
    }}

    .subtitle-text {{
        color: rgba(255,255,255,0.85);
        font-size: 0.95rem;
        text-align: left;
        margin-top: 0.3rem;
    }}

    /* 카드 스타일 - 새로운 섀도우 */
    .info-card {{
        background: white;
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 5px 10px rgba(0,0,0,0.15);
        margin-bottom: 1rem;
        border-left: 4px solid #3074FF;
    }}

    .brand-card {{
        background: white;
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 5px 10px rgba(0,0,0,0.15);
        margin-bottom: 1rem;
        border-left: 4px solid #3074FF;
    }}

    /* 메시지 결과 박스 */
    .message-result {{
        background: white;
        color: #333;
        padding: 1.5rem;
        border-radius: 12px;
        margin-top: 1rem;
        box-shadow: 0 5px 10px rgba(0,0,0,0.15);
        animation: fadeIn 0.5s ease-out;
        border: 1px solid #E0E0E0;
    }}

    .message-title-box {{
        background: #F1F1F1;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 3px solid #3074FF;
    }}

    .message-body-box {{
        background: #FAFAFA;
        padding: 1.2rem;
        border-radius: 8px;
        line-height: 1.8;
        border: 1px solid #E0E0E0;
    }}

    /* 상품 카드 */
    .product-card {{
        background: white;
        padding: 1.2rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border: 1px solid #E0E0E0;
        box-shadow: 0 5px 10px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
        animation: fadeIn 0.3s ease-out;
    }}

    .product-card:hover {{
        border-color: #3074FF;
        box-shadow: 0 8px 15px rgba(48,116,255,0.2);
        transform: translateY(-2px);
    }}

    /* 버튼 */
    .stButton>button {{
        background: #3074FF;
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 5px 10px rgba(48,116,255,0.3);
    }}

    .stButton>button:hover {{
        background: #2563EB;
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(48,116,255,0.4);
    }}

    /* 팁 박스 */
    .tip-box {{
        background: #EBF4FF;
        border-left: 4px solid #3074FF;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #333;
    }}

    /* 섹션 헤더 */
    .section-header {{
        background: white;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.8rem;
        box-shadow: 0 5px 10px rgba(0,0,0,0.15);
        border-left: 4px solid #3074FF;
    }}

    .section-header h3 {{
        margin: 0;
        color: #333;
        font-size: 1.1rem;
        font-weight: 600;
    }}

    /* 애니메이션 */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* 푸터 */
    .footer {{
        text-align: center;
        padding: 1.5rem;
        color: #AAAAAA;
        border-top: 1px solid #E0E0E0;
        margin-top: 2rem;
        background: white;
        border-radius: 12px;
    }}

    /* 복사 버튼 */
    .copy-btn {{
        background: #3074FF;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        color: white;
        cursor: pointer;
        margin-top: 0.5rem;
    }}

    /* selectbox 스타일 */
    .stSelectbox > div > div {{
        background: white;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
    }}

    /* 경고/정보 박스 색상 */
    .warning-box {{
        background: #FFF8E1;
        border-left: 4px solid #FFB300;
        padding: 0.8rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }}

    .success-box {{
        background: #E8F5E9;
        border-left: 4px solid #4CAF50;
        padding: 0.5rem 0.8rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }}

    /* expander 스타일 */
    .streamlit-expanderHeader {{
        background: white;
        border-radius: 8px;
    }}

    /* Expander 내부 컨텐츠 겹침 방지 */
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
        padding-top: 0.5rem !important;
    }}

    [data-testid="stExpander"] [data-testid="stExpanderDetails"] p,
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] div {{
        position: relative !important;
        z-index: 1 !important;
    }}

    /* Expander 헤더와 컨텐츠 사이 간격 */
    [data-testid="stExpander"] details[open] > div {{
        margin-top: 0.5rem !important;
    }}

    /* Expander 내부 텍스트 오버플로우 처리 */
    [data-testid="stExpander"] .stMarkdown {{
        overflow: visible !important;
        word-wrap: break-word !important;
    }}

    /* Expander 내부 카드 스타일 - 겹침 방지 */
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] > div > div {{
        clear: both !important;
    }}

    /* Expander 내부 그리드/컬럼 겹침 방지 */
    [data-testid="stExpander"] [data-testid="column"] {{
        overflow: visible !important;
    }}

    [data-testid="stExpander"] [data-testid="column"] > div {{
        height: auto !important;
        min-height: fit-content !important;
    }}

    /* Expander 열릴 때 컨텐츠 표시 보장 */
    [data-testid="stExpander"] details[open] [data-testid="stExpanderDetails"] {{
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        overflow: visible !important;
    }}

    /* 메트릭 카드 */
    .metric-card {{
        background: white;
        padding: 0.8rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 5px 10px rgba(0,0,0,0.15);
        border-top: 3px solid #3074FF;
    }}

    /* 스크롤바 */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}

    ::-webkit-scrollbar-track {{
        background: #F1F1F1;
    }}

    ::-webkit-scrollbar-thumb {{
        background: #AAAAAA;
        border-radius: 4px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: #888;
    }}
</style>

<script>
// Material Icons 깨진 텍스트 제거 스크립트 (더 강력한 버전)
function removeIconText() {{
    // 제거할 텍스트 패턴들
    const patterns = [
        /keyboard_arrow_down/gi,
        /keyboard_arrow_up/gi,
        /keyboard_double_arrow_left/gi,
        /keyboard_double_arrow_right/gi,
        /keyboard[_a-z]*/gi,
        /expand_more/gi,
        /expand_less/gi,
        /chevron_right/gi,
        /chevron_left/gi,
        /arrow_drop_down/gi,
        /arrow_drop_up/gi
    ];

    // 모든 텍스트 노드 탐색
    const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );

    let node;
    const nodesToModify = [];

    while (node = walker.nextNode()) {{
        if (node.textContent) {{
            let shouldModify = false;
            for (const pattern of patterns) {{
                if (pattern.test(node.textContent)) {{
                    shouldModify = true;
                    break;
                }}
            }}
            if (shouldModify) {{
                nodesToModify.push(node);
            }}
        }}
    }}

    nodesToModify.forEach(node => {{
        let text = node.textContent;
        patterns.forEach(pattern => {{
            text = text.replace(pattern, '');
        }});
        node.textContent = text.trim();
    }});

    // Expander 헤더 내의 겹치는 요소 직접 숨김
    document.querySelectorAll('[data-testid="stExpander"] summary').forEach(summary => {{
        // 첫 번째 자식 div 내의 아이콘 관련 요소 숨김
        const iconElements = summary.querySelectorAll('svg, [class*="icon"], [data-testid*="Icon"]');
        iconElements.forEach(el => {{
            el.style.display = 'none';
            el.style.visibility = 'hidden';
            el.style.width = '0';
            el.style.height = '0';
            el.style.position = 'absolute';
            el.style.left = '-9999px';
        }});
    }});
}}

// 페이지 로드 후 실행
document.addEventListener('DOMContentLoaded', removeIconText);

// Streamlit 리렌더링 대응 (MutationObserver)
const observer = new MutationObserver(function(mutations) {{
    removeIconText();
}});

// body가 준비되면 observer 시작
if (document.body) {{
    observer.observe(document.body, {{ childList: true, subtree: true }});
    removeIconText();
}} else {{
    document.addEventListener('DOMContentLoaded', function() {{
        observer.observe(document.body, {{ childList: true, subtree: true }});
        removeIconText();
    }});
}}
</script>
""", unsafe_allow_html=True)

# 타이틀 섹션
st.markdown("""
<div class="title-container">
    <h1 class="title-text">아모레몰 CRM Agent</h1>
    <p class="subtitle-text">RAG + LLM 기반 개인화 마케팅 메시지 생성 시스템</p>
</div>
""", unsafe_allow_html=True)

# API 키 자동 로드 (Streamlit Secrets)
def get_api_key(key_name="HF_API_KEY"):
    """Streamlit Secrets에서 API 키 자동 로드"""
    try:
        return st.secrets[key_name]
    except:
        return None

# 지원 모델 목록 (실제 API 사용 가능 모델만)
# 비용 계산: 입력 ~400토큰 + 출력 ~300토큰 기준
MODEL_OPTIONS = {
    "Qwen/Qwen2.5-7B-Instruct": "Qwen 2.5 7B (무료)",
    "gpt-4.1-nano": "GPT-4.1 Nano (₩0.22/건)",
    "gpt-4o-mini": "GPT-4o-mini (₩0.33/건) ⭐추천",
    "gpt-4.1-mini": "GPT-4.1 Mini (₩0.88/건)",
    "gpt-4.1": "GPT-4.1 (₩4.4/건)"
}

# 세션 상태 초기화
if 'api_key' not in st.session_state:
    st.session_state.api_key = get_api_key("HF_API_KEY") or ""
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = get_api_key("OPENAI_API_KEY") or ""
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = "Qwen/Qwen2.5-7B-Instruct"
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

# API 키는 세션에만 저장 (환경변수에 노출하지 않음)
# 필요시 generator/recommender에 직접 전달

# 사이드바
with st.sidebar:
    st.markdown("### ⚙️ 설정")

    # 모델 선택
    st.markdown("#### 🤖 LLM 모델")
    selected_model = st.selectbox(
        "모델 선택",
        list(MODEL_OPTIONS.keys()),
        format_func=lambda x: MODEL_OPTIONS[x],
        index=list(MODEL_OPTIONS.keys()).index(st.session_state.selected_model),
        label_visibility="collapsed"
    )
    st.session_state.selected_model = selected_model

    # OpenAI 모델 선택 시 API 키 입력
    if selected_model.startswith("gpt"):
        if not st.session_state.openai_api_key:
            openai_key = st.text_input(
                "OpenAI API Key",
                type="password",
                placeholder="sk-...",
                label_visibility="collapsed"
            )
            if openai_key:
                st.session_state.openai_api_key = openai_key
                st.rerun()
            st.caption("💡 [OpenAI API 키 발급](https://platform.openai.com/api-keys)")

    # API 상태 표시
    if selected_model.startswith("gpt"):
        if st.session_state.openai_api_key:
            st.success(f"✅ {MODEL_OPTIONS[selected_model]} 연결됨")
        else:
            st.warning("⚠️ OpenAI API 키 필요")
    else:
        if st.session_state.api_key:
            st.success(f"✅ {MODEL_OPTIONS[selected_model]} 연결됨")
        else:
            st.warning("⚠️ API 키 없음 - 템플릿 모드")

    # 모델별 상세 정보
    with st.expander("📊 모델별 비용/품질 비교"):
        st.markdown("""
        <style>
            .model-card {
                padding: 0.6rem;
                border-radius: 8px;
                margin-bottom: 0.4rem;
                border-left: 4px solid;
                overflow: hidden;
            }
            .model-recommend {
                background: #EBF4FF;
                border-left-color: #3074FF;
            }
            .model-good {
                background: #f3f4f6;
                border-left-color: #9CA3AF;
            }
            .model-card p {
                margin: 0.15rem 0 !important;
                line-height: 1.3 !important;
                white-space: normal !important;
            }
            .cost-info {
                font-size: 0.7rem;
                color: #666;
                margin-top: 0.2rem;
            }
        </style>

        <div class="model-card model-recommend">
            <p style="font-weight:bold; color:#3074FF; font-size:0.9rem;">🥇 GPT-4o-mini (추천)</p>
            <p style="font-size:0.75rem; color:#555;">품질: 85-90점 | 안정성: ★★★★★</p>
            <p class="cost-info">💰 ₩0.33/건 | 📅 ₩990/월(100건)</p>
        </div>

        <div class="model-card model-good">
            <p style="font-weight:bold; color:#333; font-size:0.9rem;">🥈 GPT-4.1-mini</p>
            <p style="font-size:0.75rem; color:#555;">품질: 88-92점 | 안정성: ★★★★☆</p>
            <p class="cost-info">💰 ₩0.88/건 | 📅 ₩2,640/월</p>
        </div>

        <div class="model-card model-good">
            <p style="font-weight:bold; color:#333; font-size:0.9rem;">🥉 GPT-4.1-nano</p>
            <p style="font-size:0.75rem; color:#555;">품질: 80-85점 | 안정성: ★★★★☆</p>
            <p class="cost-info">💰 ₩0.22/건 | 📅 ₩660/월</p>
        </div>

        <div class="model-card model-good">
            <p style="font-weight:bold; color:#333; font-size:0.9rem;">🔥 GPT-4.1</p>
            <p style="font-size:0.75rem; color:#555;">품질: 95점+ | 안정성: ★★★★★</p>
            <p class="cost-info">💰 ₩4.4/건 | 📅 ₩13,200/월</p>
        </div>

        <div class="model-card model-good">
            <p style="font-weight:bold; color:#333; font-size:0.9rem;">🆓 Qwen 2.5 7B</p>
            <p style="font-size:0.75rem; color:#555;">품질: 70-80점 | 안정성: ★★★☆☆</p>
            <p class="cost-info" style="color:#4CAF50;">💰 무료 (HuggingFace)</p>
        </div>

        <p style="margin:0.3rem 0 0 0; font-size:0.65rem; color:#999; text-align:center;">
            * 환율 ₩1,400/$ 기준
        </p>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 페르소나 선택
    st.markdown("#### 👤 고객")
    persona_names = [f"{p['display_name']} - {p['skin_type']}" for p in personas]
    selected_idx = st.selectbox(
        "페르소나 선택",
        range(len(persona_names)),
        format_func=lambda i: persona_names[i],
        label_visibility="collapsed"
    )
    selected_persona = personas[selected_idx]

    st.markdown("<br>", unsafe_allow_html=True)

    # 브랜드 선택
    st.markdown("#### 🎨 브랜드")
    brand = st.selectbox(
        "브랜드 선택",
        list(brand_tones.keys()),
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ========== AI 발신 목적 추천 (Rule-based 자동 실행) ==========
    st.markdown("#### 🎯 AI 발신 목적 추천")

    # 페르소나 변경 감지 → AI 추천 + ML 페르소나 예측 자동 갱신
    if st.session_state.last_persona_id != selected_persona['id']:
        st.session_state.last_persona_id = selected_persona['id']
        # 고객 변경 시 자동으로 추천 실행 (Rule-based라 API 키 불필요)
        try:
            recommender = PurposeRecommender()
            st.session_state.ai_purpose_recommendation = recommender.recommend_purpose(selected_persona)
        except Exception as e:
            st.session_state.ai_purpose_recommendation = None

        # ML 페르소나 예측 실행
        try:
            # 고객 데이터를 ML 입력 형식으로 변환
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
        except Exception as e:
            st.session_state.ml_persona_prediction = None

    # 초기 로드 시에도 추천 실행
    if st.session_state.ai_purpose_recommendation is None:
        try:
            recommender = PurposeRecommender()
            st.session_state.ai_purpose_recommendation = recommender.recommend_purpose(selected_persona)
        except Exception:
            pass

    # 초기 로드 시 ML 페르소나 예측도 실행
    if st.session_state.ml_persona_prediction is None:
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
        except Exception:
            pass

    # AI 추천 결과 표시
    ai_rec = st.session_state.ai_purpose_recommendation
    if ai_rec:
        confidence = ai_rec.get('confidence', 0)
        confidence_color = "#4CAF50" if confidence >= 0.8 else "#FFC107" if confidence >= 0.6 else "#FF5722"

        st.markdown(f"""
        <div style="background: #3074FF;
                    padding: 1rem; border-radius: 10px; margin: 0.5rem 0; color: white; box-shadow: 0 5px 10px rgba(48,116,255,0.3);">
            <p style="margin: 0; font-size: 0.85rem; opacity: 0.9;">AI 추천</p>
            <p style="margin: 0.3rem 0; font-size: 1.2rem; font-weight: bold;">
                {ai_rec.get('purpose_name', 'N/A')}
            </p>
            <p style="margin: 0.3rem 0; font-size: 0.9rem;">
                신뢰도: <span style="color: {confidence_color}; font-weight: bold;">{confidence*100:.0f}%</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 추천 이유 (접기)
        with st.expander("📊 추천 이유"):
            st.write(ai_rec.get('reasoning', 'N/A'))
            if ai_rec.get('key_factors'):
                st.caption(f"핵심 요소: {', '.join(ai_rec.get('key_factors', []))}")
            if ai_rec.get('alternative_purposes'):
                purpose_names = {
                    "promotion": "프로모션",
                    "new_product": "신제품 안내",
                    "best_curation": "베스트 큐레이션",
                    "repurchase": "재구매 & 리텐션",
                    "churn_prevention": "휴면 방지",
                    "seasonal_gift": "선물 & 시즌"
                }
                alt_names = [purpose_names.get(p, p) for p in ai_rec.get('alternative_purposes', [])]
                st.caption(f"대안: {', '.join(alt_names)}")

    st.markdown("<br>", unsafe_allow_html=True)

    # 발신 목적 선택 (AI 추천이 맨 위, 사용자가 최종 선택)
    st.markdown("#### 📌 발신 목적 선택")

    # 발신 목적 옵션 구성
    purpose_options = [
        ("promotion", "프로모션", "할인/쿠폰 혜택 안내"),
        ("new_product", "신제품 안내", "새로 출시된 제품 소개"),
        ("best_curation", "베스트 큐레이션", "브랜드 인기 상품 추천"),
        ("repurchase", "재구매 & 리텐션", "구매 주기 도래 고객"),
        ("churn_prevention", "휴면 방지", "이탈 위험 고객 재활성화"),
        ("seasonal_gift", "선물 & 시즌", "명절/기념일 선물 추천")
    ]

    # AI 추천이 있으면 해당 항목을 맨 위로
    if ai_rec:
        recommended_id = ai_rec.get('recommended_purpose', '')
        # 추천 항목을 맨 위로 이동
        purpose_options_sorted = []
        for opt in purpose_options:
            if opt[0] == recommended_id:
                purpose_options_sorted.insert(0, (opt[0], f"⭐ {opt[1]} (AI 추천)", opt[2]))
            else:
                purpose_options_sorted.append(opt)
        purpose_options = purpose_options_sorted

    # 라디오 버튼 대신 selectbox 사용 (AI 추천 강조)
    purpose_labels = [f"{opt[1]}" for opt in purpose_options]
    selected_purpose_idx = st.selectbox(
        "목적 선택",
        range(len(purpose_options)),
        format_func=lambda i: purpose_labels[i],
        label_visibility="collapsed"
    )

    selected_purpose_id = purpose_options[selected_purpose_idx][0]
    purpose = purpose_options[selected_purpose_idx][1].replace("⭐ ", "").replace(" (AI 추천)", "")

    # AI 추천과 다른 선택 시 경고
    if ai_rec and selected_purpose_id != ai_rec.get('recommended_purpose'):
        st.warning("⚠️ AI 추천과 다른 목적을 선택했습니다")

    # 발신 목적별 대상 적합성 검증
    eligibility = check_purpose_eligibility(selected_persona, selected_purpose_id)
    if not eligibility['eligible']:
        # 부적합 시 경고 표시
        st.markdown(f"""
        <div style="background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px; padding: 0.8rem; margin: 0.5rem 0;">
            <strong>⚠️ 대상 부적합</strong><br>
            <span style="font-size: 0.85rem;">{eligibility['reason']}</span><br>
            <span style="font-size: 0.8rem; color: #666;">현재 상태: {eligibility['dormancy_status']} | 권장 목적: {eligibility.get('recommendation', 'N/A')}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 적합 시 확인 표시
        st.markdown(f"""
        <div style="background: #d4edda; border-left: 4px solid #28a745; border-radius: 4px; padding: 0.5rem; margin: 0.5rem 0;">
            <span style="font-size: 0.85rem;">✅ {eligibility['reason']}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 상품 개수
    st.markdown("#### 🛍️ 추천 상품 수")
    num_products = st.slider(
        "상품 개수",
        min_value=1,
        max_value=5,
        value=3,
        label_visibility="collapsed"
    )

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 생성 버튼
    generate_btn = st.button("🚀 메시지 생성", use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # 페르소나-브랜드 미스매치 경고
    def check_persona_brand_match(persona_name, brand_name):
        """페르소나와 브랜드 조합의 적합성 검사"""
        mismatches = {
            ("민지(25세)", "설화수"): ("⚠️ 주의", "민지님은 가성비 중시 → 라네즈/이니스프리 추천", "#fff3cd"),
            ("지우(19세)", "설화수"): ("⚠️ 주의", "지우님은 저렴한 가격 선호 → 이니스프리 추천", "#fff3cd"),
            ("수현(32세)", "이니스프리"): ("💡 참고", "수현님은 프리미엄 선호 → 설화수/라네즈 추천", "#d1ecf1"),
            ("은정(45세)", "이니스프리"): ("💡 참고", "은정님은 프리미엄 케어 선호 → 설화수 추천", "#d1ecf1"),
        }
        return mismatches.get((persona_name, brand_name))

    mismatch = check_persona_brand_match(selected_persona['display_name'], brand)
    if mismatch:
        icon, message, bg_color = mismatch
        st.markdown(f"""
        <div style="background: {bg_color}; border-radius: 8px; padding: 0.8rem; margin: 0.5rem 0;">
            <strong>{icon}</strong><br>
            <span style="font-size: 0.85rem;">{message}</span>
        </div>
        """, unsafe_allow_html=True)

    # 팁 박스
    st.markdown("""
    <div class="tip-box">
        <strong>💡 Tip</strong><br>
        페르소나와 브랜드를 바꿔가며<br>
        다양한 메시지를 생성해보세요!
    </div>
    """, unsafe_allow_html=True)

# RAG 초기화
if 'rag' not in st.session_state:
    with st.spinner("🔧 RAG 엔진 초기화 중..."):
        try:
            st.session_state.rag = ProductRAG()
        except Exception as e:
            st.error(f"❌ RAG 초기화 실패: {str(e)}")

# Generator 초기화 (모델 변경 시 재생성)
def get_generator():
    """현재 설정에 맞는 Generator 반환"""
    current_model = st.session_state.get('selected_model', 'Qwen/Qwen2.5-7B-Instruct')
    hf_key = st.session_state.get('api_key', '')
    openai_key = st.session_state.get('openai_api_key', '')

    return MessageGenerator(
        api_key=hf_key if hf_key else None,
        openai_api_key=openai_key if openai_key else None,
        model=current_model,
        temperature=0.7
    )

# Generator는 매번 새로 생성 (모델 변경 반영)
try:
    generator = get_generator()
except Exception as e:
    st.error(f"❌ Generator 초기화 실패: {str(e)}")
    generator = None

# 메인 영역 - 새로운 2열 레이아웃 (왼쪽: 고객정보+상품, 오른쪽: 메시지)
main_col1, main_col2 = st.columns([1, 1])

with main_col1:
    # 고객 정보 섹션
    st.markdown("""
    <div class="section-header">
        <h3>👤 선택된 고객</h3>
    </div>
    """, unsafe_allow_html=True)

    # ML 페르소나 예측 결과
    ml_pred = st.session_state.ml_persona_prediction
    persona_line = ""
    if ml_pred:
        ml_confidence = ml_pred.get('confidence', 0)
        ml_persona = ml_pred.get('persona', 'N/A')
        if ml_confidence >= 0.7:
            conf_color = "#4CAF50"
        elif ml_confidence >= 0.5:
            conf_color = "#FFC107"
        else:
            conf_color = "#FF5722"
        conf_bg = conf_color + "22"
        conf_pct = int(ml_confidence * 100)
        persona_line = f'<p style="margin: 0.4rem 0;"><strong style="color: #3074FF;">페르소나:</strong> <span style="background: {conf_bg}; color: {conf_color}; padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: bold;">{ml_persona}</span> <span style="color: #888; font-size: 0.85rem; margin-left: 0.5rem;">신뢰도 {conf_pct}%</span></p>'

    # 기본 정보
    basic_info_html = f"""
    <div style="padding: 1rem 1.2rem; background: white; border-radius: 10px; box-shadow: 0 5px 10px rgba(0,0,0,0.15); margin-bottom: 1rem;">
        <p style="margin: 0.4rem 0;"><strong style="color: #3074FF;">이름:</strong> {selected_persona['display_name']}</p>
        <p style="margin: 0.4rem 0;"><strong style="color: #3074FF;">피부타입:</strong> {selected_persona['skin_type']}</p>
        <p style="margin: 0.4rem 0;"><strong style="color: #3074FF;">피부고민:</strong> {', '.join(selected_persona['concerns'])}</p>
        <p style="margin: 0.4rem 0;"><strong style="color: #3074FF;">쇼핑패턴:</strong> {selected_persona['shopping_pattern']}</p>
        <p style="margin: 0.4rem 0;"><strong style="color: #3074FF;">관심제품:</strong> {', '.join(selected_persona['interests'])}</p>
        <p style="margin: 0.4rem 0;"><strong style="color: #3074FF;">라이프스타일:</strong> {selected_persona['lifestyle']}</p>
        {persona_line}
    </div>
    """
    st.markdown(basic_info_html, unsafe_allow_html=True)

    # 행동 데이터 표시 (있는 경우)
    if 'activity' in selected_persona or 'purchase' in selected_persona or 'risk' in selected_persona:
        activity = selected_persona.get('activity', {})
        purchase = selected_persona.get('purchase', {})
        brand_info = selected_persona.get('brand', {})

        # 이탈 확률 자동 계산 (하드코딩 → 동적 계산)
        churn_info = get_churn_details(selected_persona)
        risk_level = churn_info['level']
        churn_prob = churn_info['probability']
        risk_factors = churn_info['factors']
        cycle_ratio = churn_info['cycle_ratio']

        # 위험도에 따른 색상
        risk_color = "#dc3545" if risk_level == "높음" else "#ffc107" if risk_level == "중" else "#28a745"

        # 구매 주기 상태
        last_days = purchase.get('last_purchase_days_ago', 0)
        avg_interval = purchase.get('avg_interval', 30)
        cycle_pct = int(last_days / avg_interval * 100) if avg_interval > 0 else 0

        # 위험 요인 텍스트
        factors_text = ", ".join(risk_factors) if risk_factors else "없음"

        st.markdown(f"""
        <div style="padding: 0.5rem 1rem; background: #f8f9fa; border-radius: 8px; margin-top: 0.5rem; border-left: 3px solid {risk_color};">
            <p style="margin: 0; font-weight: bold; color: #555;">📊 행동 데이터</p>
            <p style="margin: 0.3rem 0; font-size: 0.9rem;">
                <span style="color: #666;">마지막 접속:</span> {activity.get('last_visit_days_ago', 'N/A')}일 전 |
                <span style="color: #666;">방문빈도:</span> {activity.get('visit_frequency', 'N/A')}
            </p>
            <p style="margin: 0.3rem 0; font-size: 0.9rem;">
                <span style="color: #666;">구매 주기:</span> {last_days}일/{avg_interval}일 ({cycle_pct}%) |
                <span style="color: #666;">총 구매:</span> {purchase.get('total_count', 0)}회
            </p>
            <p style="margin: 0.3rem 0; font-size: 0.9rem;">
                <span style="color: #666;">주 브랜드:</span> {brand_info.get('primary_brand', 'N/A')} |
                <span style="color: #666;">충성도:</span> {brand_info.get('loyalty', 'N/A')}
            </p>
            <p style="margin: 0.3rem 0; font-size: 0.9rem;">
                <span style="color: #666;">이탈 위험:</span>
                <span style="color: {risk_color}; font-weight: bold;">{risk_level}</span>
                ({churn_prob*100:.0f}%) - <span style="color: #888; font-size: 0.8rem;">📈 자동계산</span>
            </p>
            <p style="margin: 0.2rem 0; font-size: 0.8rem; color: #888;">
                💡 요인: {factors_text}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 고객 분석 지표 (확장 패널)
        with st.expander("📈 AI 분석 지표 (자동 계산)", expanded=False):
            analysis = get_full_customer_analysis(selected_persona)

            # 3열 레이아웃
            m1, m2, m3 = st.columns(3)

            with m1:
                cv = analysis['customer_value']
                st.markdown(f"""
                <div style="text-align: center; padding: 0.5rem; background: linear-gradient(135deg, #f5f7fa, #c3cfe2); border-radius: 8px; margin-bottom: 0.5rem;">
                    <p style="margin: 0; font-size: 0.75rem; color: #666;">고객 등급</p>
                    <p style="margin: 0; font-size: 1.3rem; font-weight: bold; color: {cv['tier_color']};">{cv['tier']}</p>
                    <p style="margin: 0; font-size: 0.7rem; color: #888;">연 {cv['annual_value']:,}원</p>
                </div>
                """, unsafe_allow_html=True)

            with m2:
                pm = analysis['purchase_momentum']
                st.markdown(f"""
                <div style="text-align: center; padding: 0.5rem; background: linear-gradient(135deg, #f5f7fa, #c3cfe2); border-radius: 8px; margin-bottom: 0.5rem;">
                    <p style="margin: 0; font-size: 0.75rem; color: #666;">구매 추세</p>
                    <p style="margin: 0; font-size: 1.3rem; font-weight: bold; color: {pm['trend_color']};">{pm['trend_icon']} {pm['trend']}</p>
                    <p style="margin: 0; font-size: 0.7rem; color: #888;">모멘텀 {pm['momentum']}</p>
                </div>
                """, unsafe_allow_html=True)

            with m3:
                rt = analysis['repurchase_timing']
                st.markdown(f"""
                <div style="text-align: center; padding: 0.5rem; background: linear-gradient(135deg, #f5f7fa, #c3cfe2); border-radius: 8px; margin-bottom: 0.5rem;">
                    <p style="margin: 0; font-size: 0.75rem; color: #666;">재구매 타이밍</p>
                    <p style="margin: 0; font-size: 1.3rem; font-weight: bold; color: {rt['urgency_color']};">{rt['urgency_icon']} {rt['urgency']}</p>
                    <p style="margin: 0; font-size: 0.7rem; color: #888;">{rt['days_remaining']:+d}일</p>
                </div>
                """, unsafe_allow_html=True)

            # 4열 레이아웃 (추가 지표)
            m4, m5, m6, m7 = st.columns(4)

            with m4:
                dd = analysis['discount_dependency']
                st.markdown(f"""
                <div style="text-align: center; padding: 0.4rem; background: #f8f9fa; border-radius: 6px; border-left: 3px solid {dd['level_color']};">
                    <p style="margin: 0; font-size: 0.7rem; color: #666;">할인 의존도</p>
                    <p style="margin: 0; font-size: 0.9rem; font-weight: bold; color: {dd['level_color']};">{dd['level']}</p>
                </div>
                """, unsafe_allow_html=True)

            with m5:
                bs = analysis['brand_switch_risk']
                st.markdown(f"""
                <div style="text-align: center; padding: 0.4rem; background: #f8f9fa; border-radius: 6px; border-left: 3px solid {bs['level_color']};">
                    <p style="margin: 0; font-size: 0.7rem; color: #666;">브랜드 이탈</p>
                    <p style="margin: 0; font-size: 0.9rem; font-weight: bold; color: {bs['level_color']};">{bs['level']}</p>
                </div>
                """, unsafe_allow_html=True)

            with m6:
                cp = analysis['crosssell_potential']
                st.markdown(f"""
                <div style="text-align: center; padding: 0.4rem; background: #f8f9fa; border-radius: 6px; border-left: 3px solid {cp['level_color']};">
                    <p style="margin: 0; font-size: 0.7rem; color: #666;">크로스셀</p>
                    <p style="margin: 0; font-size: 0.9rem; font-weight: bold; color: {cp['level_color']};">{cp['level']}</p>
                </div>
                """, unsafe_allow_html=True)

            with m7:
                pr = analysis['promotion_response']
                st.markdown(f"""
                <div style="text-align: center; padding: 0.4rem; background: #f8f9fa; border-radius: 6px; border-left: 3px solid {pr['level_color']};">
                    <p style="margin: 0; font-size: 0.7rem; color: #666;">프로모션 반응</p>
                    <p style="margin: 0; font-size: 0.9rem; font-weight: bold; color: {pr['level_color']};">{pr['level']}</p>
                </div>
                """, unsafe_allow_html=True)

            # 권장 액션
            st.markdown(f"""
            <div style="margin-top: 0.5rem; padding: 0.5rem; background: #e3f2fd; border-radius: 6px;">
                <p style="margin: 0; font-size: 0.8rem; color: #1565c0;">
                    💡 <strong>권장:</strong> {rt['action']} | {dd['recommendation']}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # 휴면 상태 & 고객 유형 (추가 정보)
            st.markdown("<hr style='margin: 0.8rem 0; border-color: #eee;'>", unsafe_allow_html=True)

            dormancy = get_dormancy_status(selected_persona)
            cust_type = classify_customer_type(selected_persona)
            shop_persona = get_shopping_persona(selected_persona)

            t1, t2, t3 = st.columns(3)

            with t1:
                st.markdown(f"""
                <div style="text-align: center; padding: 0.5rem; background: {dormancy['color']}22; border-radius: 8px; border: 1px solid {dormancy['color']};">
                    <p style="margin: 0; font-size: 0.75rem; color: #666;">휴면 상태</p>
                    <p style="margin: 0; font-size: 1.2rem;">{dormancy['icon']} {dormancy['status']}</p>
                    <p style="margin: 0; font-size: 0.7rem; color: #888;">이탈확률 {dormancy['churn_probability']:.0%}</p>
                </div>
                """, unsafe_allow_html=True)

            with t2:
                st.markdown(f"""
                <div style="text-align: center; padding: 0.5rem; background: {cust_type['color']}22; border-radius: 8px; border: 1px solid {cust_type['color']};">
                    <p style="margin: 0; font-size: 0.75rem; color: #666;">고객 성향 유형</p>
                    <p style="margin: 0; font-size: 1.2rem;">{cust_type['icon']} {cust_type['type']}</p>
                    <p style="margin: 0; font-size: 0.7rem; color: #888;">{cust_type['description'][:15]}...</p>
                </div>
                """, unsafe_allow_html=True)

            with t3:
                st.markdown(f"""
                <div style="text-align: center; padding: 0.5rem; background: {shop_persona['color']}22; border-radius: 8px; border: 1px solid {shop_persona['color']};">
                    <p style="margin: 0; font-size: 0.75rem; color: #666;">쇼핑 페르소나</p>
                    <p style="margin: 0; font-size: 1.2rem;">{shop_persona['icon']} {shop_persona['type']}</p>
                    <p style="margin: 0; font-size: 0.7rem; color: #888;">비중 {shop_persona['weight']}</p>
                </div>
                """, unsafe_allow_html=True)

            # 메시지 우선순위 표시
            msg_priority = get_message_priority(selected_persona)
            st.markdown(f"""
            <div style="margin-top: 0.5rem; padding: 0.6rem; background: {msg_priority['color']}22; border-left: 4px solid {msg_priority['color']}; border-radius: 4px;">
                <p style="margin: 0; font-size: 0.8rem;">
                    <strong>{msg_priority['icon']} 메시지 우선순위 {msg_priority['priority']}순위: {msg_priority['priority_name']}</strong>
                </p>
                <p style="margin: 0; font-size: 0.75rem; color: #666;">
                    {msg_priority['reason']} → 권장: {msg_priority['recommended_purpose']}
                </p>
            </div>
            """, unsafe_allow_html=True)

    # 브랜드 톤앤매너 (왼쪽 컬럼에 포함)
    st.markdown("""
    <div class="section-header">
        <h3>🎨 브랜드 톤앤매너</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding: 1rem 1.2rem; background: white; border-radius: 10px; box-shadow: 0 5px 10px rgba(0,0,0,0.15); margin-bottom: 1rem;">
        <p style="margin: 0.4rem 0;"><strong style="color: #3074FF;">브랜드:</strong> {brand}</p>
        <p style="margin: 0.4rem 0;"><strong style="color: #3074FF;">톤:</strong> {brand_tones[brand]['tone']}</p>
        <p style="margin: 0.4rem 0;"><strong style="color: #3074FF;">스타일:</strong> {brand_tones[brand]['style']}</p>
        <p style="margin: 0.4rem 0;"><strong style="color: #3074FF;">발신 목적:</strong> {purpose}</p>
    </div>
    """, unsafe_allow_html=True)

# 오른쪽 컬럼 - 생성된 메시지 표시 영역
with main_col2:
    st.markdown("""
    <div class="section-header">
        <h3>📨 생성된 메시지</h3>
    </div>
    """, unsafe_allow_html=True)

    # 메시지 생성 로직 (오른쪽 컬럼 내부에서 실행)
    if generate_btn:
        if 'rag' not in st.session_state:
            st.error("❌ 시스템이 초기화되지 않았습니다.")
            st.stop()

        # 부적절 조합 강력 차단
        def check_and_block_mismatch(persona, brand_name):
            """부적절한 페르소나-브랜드 조합 차단"""
            shopping = persona.get('shopping_pattern', '')
            age = persona.get('age', 30)

            # 가성비/저렴한 가격 선호 + 프리미엄 브랜드 = 차단
            display_name = persona.get('display_name', persona.get('name', '고객'))
            if '가성비' in shopping or '저렴' in shopping:
                if brand_name == "설화수":
                    return ("❌ 부적절한 조합!",
                            f"{display_name}님은 가성비를 중시하는 고객입니다.\n"
                            f"설화수(10~20만원대)는 프리미엄 브랜드로 적합하지 않습니다.",
                            "💡 추천: **라네즈** 또는 **이니스프리**")

            # 프리미엄 선호 + 저가 브랜드 = 경고
            if '프리미엄' in shopping:
                if brand_name == "이니스프리":
                    return ("⚠️ 주의: 최적이 아닌 조합",
                            f"{display_name}님은 프리미엄을 선호하는 고객입니다.\n"
                            f"이니스프리(1~3만원대)보다 설화수가 더 적합합니다.",
                            "💡 추천: **설화수**")

            # 10대 + 안티에이징 브랜드 = 경고
            if age < 25 and brand_name == "설화수":
                return ("⚠️ 주의: 연령 미스매치",
                        f"{display_name}님은 {age}세로 안티에이징 제품이 필요하지 않을 수 있습니다.",
                        "💡 추천: **이니스프리** (청소년/대학생용)")

            return None

        mismatch_result = check_and_block_mismatch(selected_persona, brand)
        if mismatch_result:
            icon, message, suggestion = mismatch_result
            if icon.startswith("❌"):
                # 강력 차단
                st.error(f"{icon}\n\n{message}")
                st.info(suggestion)
                st.stop()
            else:
                # 경고만 (계속 진행 가능)
                st.warning(f"{icon}\n\n{message}")
                st.info(suggestion)

        with st.spinner("🔍 상품 검색 중..."):
            try:
                retrieved_products = st.session_state.rag.retrieve_products(
                    selected_persona,
                    brand,
                    purpose=selected_purpose_id,  # 영문 ID 전달 (new_product, promotion 등)
                    k=num_products
                )

                if not retrieved_products:
                    st.warning("⚠️ 추천할 상품을 찾지 못했습니다.")
                    st.stop()
            except Exception as e:
                st.error(f"❌ 상품 검색 실패: {str(e)}")
                st.stop()

        model_display = MODEL_OPTIONS[st.session_state.selected_model].split('(')[0].strip()
        with st.spinner(f"✨ {model_display} 모델로 메시지 작성 중..."):
            try:
                message = generator.generate(
                    selected_persona,
                    brand,
                    selected_purpose_id,  # 영문 ID 전달
                    retrieved_products
                )
            except Exception as e:
                st.error(f"❌ 메시지 생성 실패: {str(e)}")
                st.stop()

        # 결과를 세션에 저장 (재생성용)
        st.session_state.last_result = {
            'title': message.get('title', ''),
            'body': message.get('body', ''),
            'products': retrieved_products,
            'persona': selected_persona,
            'brand': brand,
            'purpose': selected_purpose_id,  # 영문 ID 저장
            'purpose_name': purpose,  # 한글 이름도 저장
            'debug_info': message.get('debug_info')  # 디버그 정보 저장
        }

        # 히스토리에 저장 (새 생성 시에만)
        st.session_state.message_history.append({
            'persona': selected_persona['display_name'],
            'brand': brand,
            'purpose': purpose,
            'title': message.get('title', ''),
            'body': message.get('body', '')
        })

# 결과 표시 (세션에 저장된 결과가 있으면) - 오른쪽 컬럼에 표시
if 'last_result' in st.session_state and st.session_state.last_result:
    with main_col2:
        result = st.session_state.last_result
        title = result['title']
        body = result['body']
        retrieved_products = result['products']

        # 글자수 표시 (경고 포함)
        title_len = len(title)
        body_len = len(body)

        # 제목 상태 (40자 제한)
        if title_len > 40:
            title_status = f"⚠️ {title_len}자 (40자 초과)"
        elif title_len < 20:
            title_status = f"ℹ️ {title_len}자 (너무 짧음)"
        else:
            title_status = f"✅ {title_len}자"

        # 본문 상태 (300-350자 권장)
        if body_len > 350:
            body_status = f"⚠️ {body_len}자 (350자 초과)"
        elif body_len < 300:
            body_status = f"ℹ️ {body_len}자 (300자 미만)"
        else:
            body_status = f"✅ {body_len}자"

        # 실행 정보 표시 (비용 포함)
        debug_info = result.get('debug_info')
        if debug_info:
            if debug_info.get('fallback'):
                st.warning(f"⚠️ LLM 실패 → 템플릿 모드")
            else:
                timestamp = debug_info.get('timestamp', '')
                model_name = debug_info.get('model', '').split('/')[-1]  # 모델명만 추출

                # 비용 정보
                is_free = debug_info.get('is_free', True)
                cost_krw = debug_info.get('cost_krw', 0)
                input_tokens = debug_info.get('input_tokens', 0)
                output_tokens = debug_info.get('output_tokens', 0)
                total_tokens = debug_info.get('total_tokens', 0)

                if is_free:
                    cost_str = "무료"
                    cost_color = "#4CAF50"
                elif cost_krw < 1:
                    cost_str = f"₩{cost_krw:.2f}"
                    cost_color = "#4CAF50"
                else:
                    cost_str = f"₩{cost_krw:.1f}"
                    cost_color = "#FFC107" if cost_krw < 3 else "#FF5722"

                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center;
                            background: white; padding: 0.5rem 1rem; border-radius: 8px; margin-bottom: 1rem; box-shadow: 0 5px 10px rgba(0,0,0,0.15);">
                    <span style="color: #666; font-size: 0.85rem;">
                        🕐 {timestamp} | 🤖 {model_name}
                    </span>
                    <span style="font-size: 0.85rem;">
                        📊 {total_tokens:,}토큰 |
                        <span style="color: {cost_color}; font-weight: bold;">💰 {cost_str}</span>
                    </span>
                </div>
                """, unsafe_allow_html=True)

        # 메시지 박스
        st.markdown(f"""
        <div class="message-result">
            <div class="message-title-box">
                <p style="margin: 0; color: #3074FF; font-size: 0.9rem; font-weight: 600;">📌 제목</p>
                <h3 style="margin: 0.5rem 0 0 0; color: #333;">{title}</h3>
                <p style="margin: 0.5rem 0 0 0; color: #AAAAAA; font-size: 0.85rem;">
                    {title_status}
                </p>
            </div>
            <div class="message-body-box">
                <p style="margin: 0 0 0.5rem 0; color: #3074FF; font-size: 0.9rem; font-weight: 600;">📝 본문</p>
                <div style="line-height: 1.8; font-size: 1rem; color: #333;">
                    {body}
                </div>
                <p style="margin: 1rem 0 0 0; color: #AAAAAA; font-size: 0.85rem;">
                    {body_status}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# 상품 카드는 왼쪽 컬럼에 표시
if 'last_result' in st.session_state and st.session_state.last_result:
    with main_col1:
        result = st.session_state.last_result
        retrieved_products = result['products']

        st.markdown("""
        <div class="section-header">
            <h3>🛍️ 추천 상품</h3>
        </div>
        """, unsafe_allow_html=True)

        # 발신목적에 따른 경고 표시
        current_purpose = result.get('purpose', '')
        has_new_product = any(p.get('is_new') for p in retrieved_products)
        has_discount = any(p.get('discount_rate', 0) > 0 for p in retrieved_products)

        if current_purpose == 'new_product' and not has_new_product:
            st.warning(f"⚠️ {brand}에 신제품이 없어 프리미엄 상품을 추천합니다.")
        elif current_purpose == 'promotion' and not has_discount:
            st.info(f"ℹ️ {brand}에 할인 상품이 없어 인기 상품을 추천합니다.")

        for i, product in enumerate(retrieved_products, 1):
            # 가격 정보 구성
            current_price = product.get('price', 0)
            discount_rate = product.get('discount_rate', 0)
            promotions = product.get('promotions', [])
            is_new = product.get('is_new', False)

            # 원가 계산 (할인율이 있으면 역산)
            if discount_rate > 0:
                original_price = int(current_price / (1 - discount_rate / 100))
                price_html = f'<p style="margin: 0; font-size: 0.9rem; color: #999; text-decoration: line-through;">{original_price:,}원</p><p style="margin: 0.2rem 0; font-size: 1.2rem; font-weight: bold; color: #3074FF;">{current_price:,}원</p><p style="margin: 0; font-size: 0.9rem; color: #FF4757; font-weight: bold;">🔥 {discount_rate}%</p>'
            else:
                price_html = f'<p style="margin: 0; font-size: 1.2rem; font-weight: bold; color: #3074FF;">{current_price:,}원</p>'

            # 뱃지 (발신목적별 강조 + 신제품 + 프로모션)
            badges_html = ""
            badge_list = []

            # 발신목적별 강조 뱃지
            if current_purpose == 'new_product' and is_new:
                badge_list.append('<span style="background: #3074FF; color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; margin-right: 0.3rem; font-weight: bold;">🆕 신제품</span>')
            elif current_purpose == 'promotion' and discount_rate > 0:
                badge_list.append(f'<span style="background: #FF4757; color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; margin-right: 0.3rem; font-weight: bold;">💥 {discount_rate}%↓</span>')
            elif current_purpose == 'seasonal_gift' and ('세트' in product.get('name', '') or '기프트' in product.get('name', '')):
                badge_list.append('<span style="background: #3074FF; color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; margin-right: 0.3rem; font-weight: bold;">🎁 선물추천</span>')
            elif is_new:
                badge_list.append('<span style="background: #4CAF50; color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; margin-right: 0.3rem;">✨ NEW</span>')

            if promotions:
                badge_list.extend([f'<span style="background: #FF6B6B; color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; margin-right: 0.3rem;">🎁 {p}</span>' for p in promotions])
            if badge_list:
                badges_html = f'<div style="margin-top: 0.5rem;">{"".join(badge_list)}</div>'

            features_str = ', '.join(product['features'])
            st.markdown(f'<div class="product-card"><div style="display: flex; justify-content: space-between; align-items: flex-start;"><div style="flex: 1;"><h4 style="margin: 0; color: #333; font-size: 1rem;">{i}. {product["name"]}</h4><p style="margin: 0.4rem 0; color: #666; font-size: 0.9rem;">{product["description"]}</p><p style="margin: 0; color: #AAAAAA; font-size: 0.85rem;">🏷️ {features_str}</p>{badges_html}</div><div style="text-align: right; min-width: 100px;">{price_html}</div></div></div>', unsafe_allow_html=True)

# 다운로드 & 복사 & 재생성 버튼 (오른쪽 컬럼 하단)
if 'last_result' in st.session_state and st.session_state.last_result:
    with main_col2:
        result = st.session_state.last_result
        title = result['title']
        body = result['body']
        retrieved_products = result['products']

        st.markdown("<br>", unsafe_allow_html=True)

        # 상품 정보 포맷팅 (할인 정보 포함)
        def format_product_for_text(idx, p):
            price = p.get('price', 0)
            discount = p.get('discount_rate', 0)
            promos = p.get('promotions', [])

            if discount > 0:
                original = int(price / (1 - discount / 100))
                price_str = f"{original:,}원 → {price:,}원 ({discount}% 할인)"
            else:
                price_str = f"{price:,}원"

            promo_str = f" [{', '.join(promos)}]" if promos else ""
            return f"{idx}. {p['name']} - {price_str}{promo_str}"

        message_text = f"""[AMORE CRM 메시지]

페르소나: {result['persona']['display_name']}
브랜드: {result['brand']}
목적: {result['purpose']}

===== 제목 =====
{title}

===== 본문 =====
{body}

===== 추천 상품 =====
{chr(10).join([format_product_for_text(i+1, p) for i, p in enumerate(retrieved_products)])}
"""

        col_btn1, col_btn2, col_btn3 = st.columns(3)

        with col_btn1:
            persona_name = result['persona'].get('display_name', result['persona'].get('name', 'customer'))
            st.download_button(
                label="💾 다운로드",
                data=message_text,
                file_name=f"crm_message_{persona_name}_{result['brand']}.txt",
                mime="text/plain",
                use_container_width=True
            )

        with col_btn2:
            # 클립보드 복사 (JavaScript)
            copy_text = f"{title}\n\n{body}"
            st.markdown(f"""
            <button onclick="navigator.clipboard.writeText(`{copy_text.replace('`', '')}`); alert('복사되었습니다!');"
                    style="width: 100%; padding: 0.6rem; background: #3074FF;
                           color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;
                           box-shadow: 0 5px 10px rgba(48,116,255,0.3);">
                📋 복사하기
            </button>
            """, unsafe_allow_html=True)

        with col_btn3:
            # 재생성 버튼
            if st.button("🔄 재생성", use_container_width=True, key="regenerate"):
                regen_model = MODEL_OPTIONS[st.session_state.selected_model].split('(')[0].strip()
                with st.spinner(f"✨ {regen_model} 모델로 재생성 중..."):
                    try:
                        new_message = generator.generate(
                            result['persona'],
                            result['brand'],
                            result['purpose'],
                            result['products']
                        )
                        st.session_state.last_result = {
                            'title': new_message.get('title', ''),
                            'body': new_message.get('body', ''),
                            'products': result['products'],
                            'persona': result['persona'],
                            'brand': result['brand'],
                            'purpose': result['purpose']
                        }
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 재생성 실패: {str(e)}")

# 히스토리 표시 (최근 3개)
if st.session_state.message_history:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📚 최근 생성 히스토리"):
        for i, h in enumerate(reversed(st.session_state.message_history[-3:]), 1):
            st.markdown(f"""
            **{i}. {h['persona']} | {h['brand']} | {h['purpose']}**
            - 제목: {h['title'][:30]}...
            """)

# 푸터 - RAG 정보 포함
current_model_name = MODEL_OPTIONS.get(st.session_state.selected_model, "Unknown")

# RAG 정보 가져오기
rag_info = ""
if 'rag' in st.session_state:
    try:
        info = st.session_state.rag.get_search_info()
        rag_info = f"| 검색: {info.get('search_type', 'Vector')} | 임베딩: ko-sroberta"
    except Exception:
        rag_info = "| 검색: 준비중"

st.markdown(f"""
<div class="footer">
    <p style="margin: 0; color: #333;">
        🤖 Powered by Hybrid RAG + LLM ({current_model_name.split('(')[0].strip()})
    </p>
    <p style="margin: 0.3rem 0 0 0; font-size: 0.85rem; color: #AAAAAA;">
        📊 한국어 임베딩 (ko-sroberta) | 하이브리드 검색 (벡터 60% + BM25 40%)
    </p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; color: #3074FF;">
        아모레몰 CRM Agent
    </p>
</div>
""", unsafe_allow_html=True)
