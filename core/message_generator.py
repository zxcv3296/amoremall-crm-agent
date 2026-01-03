# -*- coding: utf-8 -*-
# message_generator.py
"""
LLM 기반 마케팅 메시지 생성기
브랜드 톤앤매너에 맞는 개인화된 CRM 메시지를 생성합니다.
"""

import sys
import os
import json
import re
import requests

# 상위 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.personas import brand_tones
from core.context_builder import MessageContextBuilder
from config import PURPOSE_NAMES, MODEL_OPTIONS, get_purpose_name


def josa(word, josa_type):
    """
    한국어 조사 자동 선택 함수

    Args:
        word: 단어
        josa_type: 조사 유형 ('이가', '은는', '을를')

    Returns:
        적절한 조사
    """
    if not word:
        return ""

    # 마지막 글자의 유니코드 값
    last_char = word[-1]

    # 한글인지 확인
    if '가' <= last_char <= '힣':
        # 종성 확인 (받침 있는지)
        code = ord(last_char) - ord('가')
        jongseong = code % 28
        has_jongseong = jongseong > 0
    else:
        # 숫자나 영문의 경우 발음 기준
        # 간단히 숫자 처리 (1,7,8,0은 받침 있음으로 간주)
        if last_char in '1780lmnLMN':
            has_jongseong = True
        else:
            has_jongseong = False

    # 조사 선택
    if josa_type == '이가':
        return '이' if has_jongseong else '가'
    elif josa_type == '은는':
        return '은' if has_jongseong else '는'
    elif josa_type == '을를':
        return '을' if has_jongseong else '를'
    else:
        return ''


class MessageGenerator:
    """
    개인화된 마케팅 메시지 생성기
    - 다중 LLM 지원 (HuggingFace, OpenAI)
    - 브랜드별 톤앤매너 적용
    - 페르소나 맞춤 메시지
    """

    # 지원 모델 목록
    SUPPORTED_MODELS = {
        "Qwen/Qwen2.5-7B-Instruct": {
            "provider": "huggingface",
            "api_url": "https://router.huggingface.co/v1/chat/completions",
            "display_name": "Qwen 2.5 7B (무료)",
            "cost": "무료"
        },
        "gpt-4o-mini": {
            "provider": "openai",
            "api_url": "https://api.openai.com/v1/chat/completions",
            "display_name": "GPT-4o-mini (추천)",
            "cost": "~₩0.6/회"
        },
        "gpt-4.1": {
            "provider": "openai",
            "api_url": "https://api.openai.com/v1/chat/completions",
            "display_name": "GPT-4.1",
            "cost": "~₩8/회"
        },
        "gpt-4.1-mini": {
            "provider": "openai",
            "api_url": "https://api.openai.com/v1/chat/completions",
            "display_name": "GPT-4.1 Mini",
            "cost": "~₩1.6/회"
        },
        "gpt-4.1-nano": {
            "provider": "openai",
            "api_url": "https://api.openai.com/v1/chat/completions",
            "display_name": "GPT-4.1 Nano",
            "cost": "~₩0.4/회"
        }
    }

    def __init__(self, api_key=None, openai_api_key=None, model="Qwen/Qwen2.5-7B-Instruct", temperature=0.7):
        """
        메시지 생성기 초기화

        Args:
            api_key: Hugging Face API 키
            openai_api_key: OpenAI API 키
            model: 사용할 모델
            temperature: 창의성 수준 (0.0~1.0)
        """
        self.hf_api_key = api_key
        self.openai_api_key = openai_api_key
        self.model = model
        self.temperature = temperature
        self.llm = None
        self.context_builder = MessageContextBuilder()

        # 모델 설정
        model_config = self.SUPPORTED_MODELS.get(model, self.SUPPORTED_MODELS["Qwen/Qwen2.5-7B-Instruct"])
        self.provider = model_config["provider"]
        self.api_url = model_config["api_url"]

        # API 키 확인
        if self.provider == "openai" and openai_api_key:
            self.llm = True
            self.active_api_key = openai_api_key
        elif self.provider == "huggingface" and api_key:
            self.llm = True
            self.active_api_key = api_key
        elif api_key:
            # fallback to HuggingFace
            self.llm = True
            self.active_api_key = api_key
            self.provider = "huggingface"
            self.api_url = "https://router.huggingface.co/v1/chat/completions"

    def _get_few_shot_examples(self, brand, purpose):
        """Few-shot learning을 위한 브랜드별 우수 예시"""

        # 350자 이내로 맞춘 Few-shot 예시
        examples = {
            "라네즈": {
                "맞춤 제품 추천": """
📌 예시 (라네즈 - 맞춤 추천, 본문 340자):
{
  "title": "민지님만을 위한 라네즈 추천",
  "body": "바쁜 일상 속에서도 피부 관리는 놓치고 싶지 않으신 민지님! 라네즈가 함께할게요. 복합성 피부의 모공, 피지 고민을 간편하게 해결하세요. 네오쿠션은 출근 전 오 분이면 완성되는 완벽 커버력! 트렌디하면서도 가성비까지 챙긴 똑똑한 선택이에요. 인스타에서 핫한 워터뱅크 세럼으로 하루종일 촉촉함도 유지하세요. 지금 바로 장바구니에 담아보세요!"
}""",
                "재구매 유도": """
📌 예시 (라네즈 - 재구매 유도, 본문 320자):
{
  "title": "민지님, 또 만나 반가워요!",
  "body": "이번에도 라네즈를 찾아주신 민지님, 감사해요! 지난번 네오쿠션 어떠셨나요? 직장인분들이 계속 찾는 데는 이유가 있어요. 출근 메이크업 오 분 컷, SNS 인증샷도 완벽! 이번엔 워터뱅크 세럼도 함께 써보세요. 쿠션 지속력도 좋아지고 모공 고민도 해결돼요. 단골 고객님 특별 혜택도 준비했어요. 다시 만나러 오세요!"
}""",
                "특가/프로모션 알림": """
📌 예시 (라네즈 - 특가, 본문 300자):
{
  "title": "민지님, 이 특가 놓치면 후회해요!",
  "body": "직장인 민지님을 위한 깜짝 특가! SNS에서 핫한 네오쿠션과 워터뱅크 세럼을 가성비 좋은 가격에 만나보세요. 모공 고민 해결하고 지갑도 가벼워지는 일석이조! 출근 메이크업 오 분 컷, 퇴근 후에도 무너지지 않는 커버력을 경험하세요. 오늘만 특가니까 놓치지 마세요. 지금 바로 GO!"
}""",
                "신제품 론칭 안내": """
📌 예시 (라네즈 - 신제품, 본문 310자):
{
  "title": "민지님, 라네즈 신제품 먼저 만나보세요!",
  "body": "기다리셨죠? 라네즈 신제품이 드디어 출시됐어요! 트렌디한 민지님을 위해 특별히 개발한 제품이에요. 복합성 피부의 모공, 피지 고민을 한 번에 해결하는 올인원 솔루션! 가성비까지 완벽해서 직장인분들께 딱이에요. 론칭 기념 특별 혜택도 놓치지 마세요. 지금 바로 만나보세요!"
}"""
            },
            "설화수": {
                "맞춤 제품 추천": """
📌 예시 (설화수 - 맞춤 추천, 본문 340자):
{
  "title": "수현님을 위한 설화수 프리미엄 케어",
  "body": "수현님께, 워킹맘으로서 소중한 시간을 내어 피부를 가꾸시는 모습이 아름답습니다. 건성 피부의 주름과 탄력 고민을 설화수의 한방 지혜로 해결해드리겠습니다. 자음생 에센셜 세럼은 피부 깊숙이 한방 영양을 전달하는 프리미엄 에센스입니다. 효능을 중시하시는 분께 자신있게 추천드립니다. 피부 본연의 아름다움을 되찾으시길 바랍니다."
}""",
                "재구매 유도": """
📌 예시 (설화수 - 재구매 유도, 본문 330자):
{
  "title": "수현님, 다시 찾아주셔서 감사합니다",
  "body": "수현님께서 다시 설화수를 찾아주신 것에 깊이 감사드립니다. 지난번 자음생 세럼은 어떠셨는지요? 워킹맘으로 바쁘신 중에도 꾸준히 피부 관리에 정성을 다하시는 모습이 존경스럽습니다. 이번에는 윤조 아이크림을 함께 사용해보시면 어떨까요? 오래 사랑해주신 고객님께만 드리는 특별한 혜택도 준비되어 있습니다."
}""",
                "특가/프로모션 알림": """
📌 예시 (설화수 - 특가, 본문 320자):
{
  "title": "설화수, 수현님을 위한 특별한 제안",
  "body": "수현님께 특별한 소식을 전합니다. 워킹맘으로 바쁘신 중에도 피부 관리에 정성을 다하시는 수현님을 위해 프리미엄 한방 케어를 특별 가격으로 준비했습니다. 주름과 탄력을 케어하는 자음생 세럼을 합리적인 가격에 만나보실 수 있습니다. 피부 본연의 아름다움을 되찾아보시길 바랍니다."
}""",
                "신제품 론칭 안내": """
📌 예시 (설화수 - 신제품, 본문 320자):
{
  "title": "설화수 신제품, 수현님께 먼저 소개합니다",
  "body": "수현님께 특별한 소식을 전합니다. 설화수가 오랜 연구 끝에 완성한 신제품이 세상에 첫선을 보입니다. 건성 피부의 주름과 탄력 고민을 위해 한방 명품 성분을 집약했습니다. 효능을 중시하시는 분들께 자신있게 선보이는 프리미엄 포뮬라입니다. 피부 본연의 아름다움을 되찾으시길 바랍니다."
}"""
            },
            "이니스프리": {
                "맞춤 제품 추천": """
📌 예시 (이니스프리 - 맞춤 추천, 본문 340자):
{
  "title": "하은님, 피부에 맞는 제주 자연 케어",
  "body": "하은님께, 민감하고 건조한 피부 고민을 제주의 청정 자연으로 해결해보세요. 비자 시카밤은 민감해진 피부를 자연의 힘으로 진정시켜줍니다. 제주 비자 성분이 피부 장벽을 강화하고, 시카 성분이 빠른 진정 효과를 선사해요. 가격 부담 없이 매일 사용할 수 있어 많은 분들께 사랑받고 있어요. 지금 바로 만나보세요!"
}""",
                "재구매 유도": """
📌 예시 (이니스프리 - 재구매 유도, 본문 320자):
{
  "title": "하은님, 이번에도 이니스프리와 함께해요!",
  "body": "하은님, 또 찾아주셔서 정말 기뻐요! 지난번 비자 시카밤은 민감한 피부에 잘 맞으셨나요? 이번에는 그린티 세럼도 함께 써보는 건 어떨까요? 시카밤으로 진정시킨 피부에 제주 녹차 수분을 채워주면 건조함 걱정 끝! 단골 고객님께만 드리는 작은 선물도 준비했어요. 계속 함께해요!"
}""",
                "특가/프로모션 알림": """
📌 예시 (이니스프리 - 특가, 본문 300자):
{
  "title": "하은님, 제주 자연을 특별 가격으로!",
  "body": "특별한 제안을 준비했어요, 하은님! 비자 시카밤과 그린티 세럼을 특가로 만나보세요. 민감한 피부 고민을 자연의 힘으로 케어하면서 가격 부담까지 덜 수 있어요. 피부에도 지구에도 좋은 클린 뷰티 루틴을 지금 시작해보세요. 건강한 아름다움을 선물합니다!"
}""",
                "신제품 론칭 안내": """
📌 예시 (이니스프리 - 신제품, 본문 310자):
{
  "title": "하은님, 이니스프리 신제품 소식이에요!",
  "body": "새로운 시작을 알려요! 이니스프리 신제품이 출시됐어요. 제주의 청정 자연이 담긴 이 제품은 민감한 피부를 생각하며 만들어졌어요. 하은님의 피부 고민을 자연의 힘으로 케어해드릴게요. 피부에도 지구에도 좋은 클린 뷰티를 가장 먼저 경험해보세요!"
}"""
            }
        }

        # 브랜드와 목적에 맞는 예시 반환
        brand_examples = examples.get(brand, examples["라네즈"])

        # 목적이 정확히 매칭되지 않으면 유사한 것 선택
        if purpose in brand_examples:
            return brand_examples[purpose]
        elif "재구매" in purpose or "유도" in purpose:
            return brand_examples.get("재구매 유도", brand_examples.get("맞춤 제품 추천", ""))
        elif "맞춤" in purpose or "추천" in purpose:
            return brand_examples.get("맞춤 제품 추천", "")
        elif "특가" in purpose or "프로모션" in purpose:
            return brand_examples.get("특가/프로모션 알림", "")
        elif "신제품" in purpose or "론칭" in purpose:
            return brand_examples.get("신제품 론칭 안내", brand_examples.get("맞춤 제품 추천", ""))
        else:
            # 기본값으로 맞춤 추천 반환
            return list(brand_examples.values())[0]

    def _validate_brand_tone(self, message, brand, persona=None):
        """
        브랜드 톤앤매너 검증 및 수정 + 데이터 복붙 방지

        Args:
            message: 생성된 메시지 딕셔너리 {"title": ..., "body": ...}
            brand: 브랜드명
            persona: 페르소나 정보 (데이터 복붙 검증용)

        Returns:
            dict: 검증/수정된 메시지
        """
        title = message.get("title", "")
        body = message.get("body", "")

        # 1. 라이프스타일 데이터 그대로 노출 방지
        if persona:
            lifestyle_raw = persona.get('lifestyle', '')
            shopping_raw = persona.get('shopping_pattern', '')
            name = persona.get('name', '')

            # 라이프스타일 데이터를 자연스러운 표현으로 변환
            lifestyle_replacements = {
                "직장인, SNS 활발, 트렌디한 제품 선호": f"SNS에서 트렌드를 찾는 {name}님",
                "워킹맘, 효능 중시, 간편한 루틴": f"바쁜 일상 속에서도 피부 관리를 챙기는 {name}님",
                "대학생, 유튜브/인스타 참고, 실험적": f"유튜브와 인스타로 최신 뷰티 정보를 찾는 {name}님",
                "전문직, 프리미엄 케어, 성분 연구": f"성분 하나하나 꼼꼼히 따지는 {name}님",
                "재택근무, 미니멀 루틴, 클린뷰티": f"순한 성분의 클린뷰티를 추구하는 {name}님",
            }

            # 그대로 노출된 데이터 대체
            if lifestyle_raw in body:
                replacement = lifestyle_replacements.get(lifestyle_raw, f"{name}님")
                body = body.replace(lifestyle_raw, replacement)

            # "~님처럼 [데이터]에게" 패턴 수정
            import re
            awkward_pattern = rf"{name}님처럼\s+{re.escape(lifestyle_raw)}에게"
            if re.search(awkward_pattern, body):
                body = re.sub(awkward_pattern, lifestyle_replacements.get(lifestyle_raw, f"{name}님에게"), body)

            # 반복 표현 제거 (같은 이름 4번 이상만 → 3번으로 줄임)
            # 글자 손실 방지를 위해 보수적으로 처리
            name_pattern = f"{name}님"
            name_count = body.count(name_pattern)
            if name_count > 3:
                # 4번 이상일 때만 중간 하나 제거 (안전하게)
                # 두 번째 등장하는 이름만 제거
                first_idx = body.find(name_pattern)
                if first_idx != -1:
                    second_idx = body.find(name_pattern, first_idx + len(name_pattern))
                    if second_idx != -1:
                        # 두 번째 이름만 제거
                        body = body[:second_idx] + body[second_idx + len(name_pattern):]

            # 2. 텍스트 누락 수정 (이름이 빠진 패턴 찾아서 채우기)
            import re
            missing_patterns = [
                (r"^을 위해", f"{name}님을 위해"),
                (r"^의 피부", f"{name}님의 피부"),
                (r"^께도 ", f"{name}님께도 "),
                (r"^께는 ", f"{name}님께는 "),
                (r"^께서 ", f"{name}님께서 "),
                (r"^처럼 ", f"{name}님처럼 "),
                (r" 을 위해", f" {name}님을 위해"),
                (r" 의 피부", f" {name}님의 피부"),
                (r" 께도 ", f" {name}님께도 "),
                (r" 께는 ", f" {name}님께는 "),
                (r" 께서 ", f" {name}님께서 "),
                (r" 처럼 ", f" {name}님처럼 "),
                (r"께 드", f"{name}님께 드"),
                (r"의 복합성", f"{name}님의 복합성"),
                (r"의 건성", f"{name}님의 건성"),
                (r"의 지성", f"{name}님의 지성"),
                (r"의 민감성", f"{name}님의 민감성"),
            ]

            for pattern, replacement in missing_patterns:
                body = re.sub(pattern, replacement, body)
                title = re.sub(pattern, replacement, title)

        # 브랜드별 금지 표현 (톤 미스매치)
        forbidden_expressions = {
            "설화수": {
                # 설화수는 우아하고 격식있는 톤 → 캐주얼한 표현 금지
                "forbidden": ["GO!", "ㅎㅎ", "ㅋㅋ", "~요!", "꿀팁", "꿀조합", "대박", "JMT", "TMI",
                              "핫한", "핫템", "레알", "진짜루", "완전", "존맛", "갓성비", "뿌듯"],
                "replace": {
                    "GO!": "경험해보세요",
                    "꿀조합": "최상의 조합",
                    "핫한": "주목받는",
                    "핫템": "인기 제품",
                    "대박": "놀라운",
                    "완전": "매우",
                    "지금 바로 GO!": "지금 바로 경험해보세요"
                }
            },
            "라네즈": {
                # 라네즈는 친근하고 트렌디한 톤 → 과하게 격식있는 표현 금지
                "forbidden": ["~시옵소서", "~하시옵길", "삼가"],
                "replace": {}
            },
            "이니스프리": {
                # 이니스프리는 자연스럽고 건강한 톤 → 과하게 화려한 표현 금지
                "forbidden": ["럭셔리", "명품", "VIP", "프리미엄 중의 프리미엄"],
                "replace": {
                    "럭셔리": "자연의 힘이 담긴",
                    "명품": "제주의 청정함이 담긴",
                    "프리미엄": "자연 유래"
                }
            }
        }

        brand_rules = forbidden_expressions.get(brand, {})
        forbidden = brand_rules.get("forbidden", [])
        replacements = brand_rules.get("replace", {})

        # 금지 표현 대체
        for old, new in replacements.items():
            title = title.replace(old, new)
            body = body.replace(old, new)

        # 남은 금지 표현 제거 (대체어 없는 경우)
        for word in forbidden:
            if word in title:
                title = title.replace(word, "")
            if word in body:
                body = body.replace(word, "")

        # 연속 공백 정리
        import re
        title = re.sub(r'\s+', ' ', title).strip()
        body = re.sub(r'\s+', ' ', body).strip()

        return {
            "title": title,
            "body": body,
            "title_over": message.get("title_over", len(title) > 40),
            "body_over": message.get("body_over", len(body) > 350)
        }

    def _extend_body(self, body, persona, brand, products):
        """
        본문이 300자 미만일 때 자동으로 보강 (완전 재작성 버전)

        Args:
            body: 원본 본문
            persona: 페르소나 정보
            brand: 브랜드명
            products: 추천 상품 리스트

        Returns:
            str: 보강된 본문 (300~350자)
        """
        TARGET_LEN = 320  # 목표 글자수
        # name은 이름만 추출 (나이 제외)
        display_name = persona.get('display_name') or persona.get('name', '고객')
        # "김서연(42세)" -> "김서연" 추출
        if '(' in display_name:
            name = display_name.split('(')[0]
        else:
            name = display_name
        skin_type = persona.get('skin_type', '피부')
        concerns = persona.get('concerns') or ['피부고민']
        concern = concerns[0] if concerns else '피부고민'

        # 첫 번째 상품 정보 활용 (Edge case: 빈 리스트 처리)
        if products and len(products) > 0:
            product_features = products[0].get('features') or ['보습']
        else:
            product_features = ['보습']
        feature = product_features[0] if product_features else '보습'

        # 모든 보강 문구를 하나의 리스트로 통합 (브랜드별 + 일반)
        all_extensions = []

        if brand == "설화수":
            all_extensions = [
                f" {name}님의 {skin_type} 피부를 위해 엄선된 한방 성분이 깊은 영양을 전합니다.",
                f" 특히 {concern} 고민이 있으시다면 더욱 효과적입니다.",
                " 오랜 세월 검증된 한방의 지혜로 피부 본연의 빛을 되찾아 드립니다.",
                f" {feature} 효과와 함께 피부 탄력까지 케어해보세요.",
                " 지금 아모레몰에서 설화수의 프리미엄 케어를 경험해보세요.",
                f" {name}님만을 위한 특별한 혜택을 놓치지 마세요.",
                " 피부 속부터 채워지는 깊은 보습감을 느껴보세요.",
                " 한방 명품 스킨케어의 진가를 경험하실 수 있습니다.",
            ]
        elif brand == "이니스프리":
            all_extensions = [
                f" 제주의 청정 자연 성분으로 {name}님의 피부 고민을 케어해 드려요.",
                f" {concern} 걱정은 이제 자연에게 맡겨보세요.",
                " 자연이 주는 건강한 아름다움을 매일 피부로 느껴보세요.",
                f" {feature} 효과와 함께 자연 유래 순한 성분으로 피부 진정까지!",
                " 아모레몰에서 제주의 자연을 만나보세요!",
                f" {name}님만을 위한 특별한 혜택을 놓치지 마세요.",
                " 피부에도 환경에도 좋은 클린뷰티를 경험해보세요.",
                " 제주 녹차의 싱그러운 수분감이 하루종일 지속됩니다.",
            ]
        else:  # 라네즈, 헤라, 아이오페 등 기타 브랜드
            all_extensions = [
                f" {name}님에게 딱 맞는 제품이에요!",
                f" {concern} 고민, 이제 {brand}와 함께 해결해보세요.",
                " 매일 쓸수록 달라지는 피부결을 직접 경험해보세요.",
                f" {feature} 효과로 하루종일 촉촉하고 건강한 피부를 유지할 수 있어요.",
                f" 지금 바로 아모레몰에서 {brand}를 만나보세요!",
                f" {name}님만을 위한 특별한 혜택을 놓치지 마세요.",
                " 트렌디하면서도 실속있는 스킨케어를 경험해보세요.",
                " 피부 컨디션이 좋아지는 걸 직접 느끼실 수 있어요.",
            ]

        # 300자가 될 때까지 계속 추가
        idx = 0
        while len(body) < TARGET_LEN and idx < len(all_extensions):
            # 마침표나 느낌표로 끝나지 않으면 마침표 추가
            if body and body[-1] not in ".!?":
                body += "."
            body += all_extensions[idx]
            idx += 1

        # 그래도 부족하면 더 추가
        extra_extensions = [
            " 오늘 주문하시면 빠른 배송으로 만나보실 수 있어요!",
            f" {skin_type} 피부에 딱 맞는 케어로 매일 건강한 피부를 유지해보세요.",
            " 후회 없는 선택이 될 거예요!",
            " 이번 기회를 절대 놓치지 마세요!",
            " 지금 바로 장바구니에 담아보세요!",
        ]

        extra_idx = 0
        while len(body) < TARGET_LEN and extra_idx < len(extra_extensions):
            if body and body[-1] not in ".!?":
                body += "."
            body += extra_extensions[extra_idx]
            extra_idx += 1

        # 350자 초과 방지
        if len(body) > 350:
            # 350자 이내에서 마지막 마침표/느낌표 찾기
            cut_point = min(350, len(body))
            for i in range(min(349, len(body) - 1), 299, -1):
                if i < len(body) and body[i] in '.!?':
                    cut_point = i + 1
                    break
            body = body[:cut_point]

        return body

    def _get_purpose_instructions(self, purpose):
        """발신 목적별 필수 표현 및 지침 반환"""
        instructions = {
            "신제품 론칭 안내": """
⚠️ 신제품 메시지 필수 요소:
- 제목에 "신제품", "새로운", "출시", "론칭" 중 하나 포함
- 본문에 "드디어 출시", "첫선을 보입니다", "새롭게 선보이는" 등 신규성 강조
- "론칭 기념", "먼저 만나보세요" 등 선점 효과 강조
- 기존 제품과의 차별점 언급""",

            "재구매 유도": """
⚠️ 재구매 메시지 필수 요소:
- 제목에 "또", "다시", "이번에도" 중 하나 포함
- 본문에 "지난번", "이전에 구매하신", "꾸준히 사랑해주신" 등 과거 구매 언급
- "단골 고객님", "특별 혜택", "재구매 할인" 등 충성 고객 대우
- 이전 제품 + 새 제품 조합 추천 (크로스셀링)""",

            "특가/프로모션 알림": """
⚠️ 특가 메시지 필수 요소:
- 제목에 "특가", "할인", "세일", "프로모션" 중 하나 포함
- 본문에 구체적 할인 표현: "특별 가격", "파격 할인", "한정 특가"
- 긴급성 강조: "오늘만", "한정 수량", "놓치면 후회"
- 가격 혜택 명확히 전달""",

            "맞춤 제품 추천": """
⚠️ 맞춤 추천 메시지 필수 요소:
- 제목에 "추천", "맞춤", "위한" 중 하나 포함
- 본문에 고객의 피부 고민 구체적 언급
- 제품이 고민을 어떻게 해결하는지 설명
- 개인화된 느낌: "OO님만을 위한", "OO님의 피부에 딱 맞는\""""
        }

        # 목적에 맞는 지침 반환
        for key, instruction in instructions.items():
            if key in purpose or any(word in purpose for word in key.split("/")):
                return instruction

        # 기본값
        return instructions.get("맞춤 제품 추천", "")

    def generate(self, persona, brand, purpose, products):
        """
        개인화된 마케팅 메시지 생성

        Args:
            persona: 페르소나 딕셔너리
            brand: 브랜드명 (설화수/라네즈/이니스프리)
            purpose: 발신 목적
            products: 추천 상품 리스트

        Returns:
            dict: {"title": "제목", "body": "본문"}
        """
        # 브랜드 톤앤매너 가져오기
        tone_info = brand_tones.get(brand, brand_tones["라네즈"])

        # LLM이 없으면 바로 템플릿 사용
        if not self.llm:
            return self._generate_template_message(persona, brand, purpose, products)

        # LLM 호출 (Direct API)
        try:
            # 브랜드별 Few-shot 예시 생성
            few_shot_examples = self._get_few_shot_examples(brand, purpose)

            # 발신목적 매핑 (영문 -> 한글) - config.py 기반
            # Few-shot용 세부 매핑 (LLM 프롬프트에서만 사용)
            purpose_detail_mapping = {
                "promotion": "특가/프로모션 알림",
                "new_product": "신제품 론칭 안내",
                "best_curation": "맞춤 제품 추천",
                "repurchase": "재구매 유도",
                "churn_prevention": "맞춤 제품 추천",  # 휴면방지는 맞춤추천 톤으로
                "seasonal_gift": "맞춤 제품 추천"  # 선물도 맞춤추천 톤으로
            }
            purpose_kr = purpose_detail_mapping.get(purpose, get_purpose_name(purpose))

            # context_builder로 최적화된 컨텍스트 생성
            optimized_context = self.context_builder.build(persona, purpose, brand, products)

            # 프롬프트 생성 (v8 - context_builder 통합)
            formatted_prompt = f"""{brand} 브랜드의 개인화 마케팅 메시지를 작성하세요.

🚨 글자수 규칙:
- 제목: 25~40자
- 본문: 300~350자

⚠️ 필수 준수:
1. 한국어만 사용
2. 아래 고객 컨텍스트를 자연스럽게 반영
3. 브랜드 톤 정확히 반영
4. CTA 강력하게
5. 같은 이름 반복 금지 (최대 2번)

{few_shot_examples}

{optimized_context}

브랜드 톤:
{brand}는 {tone_info["tone"]} 톤으로 {tone_info["style"]} 스타일입니다.

{self._get_purpose_instructions(purpose_kr)}

메시지 작성:
- 제목: 40자 이내
- 본문: 300-350자

JSON 형식으로만 출력:
{{\"title\": \"제목\", \"body\": \"본문\"}}"""

            # API 호출 (OpenAI 또는 HuggingFace)
            headers = {
                "Authorization": f"Bearer {self.active_api_key}",
                "Content-Type": "application/json"
            }

            # GPT 모델용 시스템 메시지 추가 (글자수 강제)
            system_message = """당신은 K-Beauty 브랜드의 CRM 마케팅 메시지 전문가입니다.

🚨 중요: 본문은 반드시 300~350자로 작성해야 합니다!
- 200자대 본문 = 실패
- 300자 미만 = 실패
- 300~350자 = 성공

본문 300자를 채우는 구조:
1. 인사/공감 (30자) - "~님, 요즘 ~고민이시죠?"
2. 제품 소개 (80자) - 추천 제품 효능 설명
3. 피부고민 연결 (60자) - 고객 고민 해결 방법
4. 추가 효과 (60자) - 부가 효과 설명
5. CTA (50자) - "지금 바로 아모레몰에서~"
6. 마무리 (20자) - 따뜻한 마무리

총합 = 300자 이상!"""

            # OpenAI 모델은 시스템 메시지 사용
            if self.provider == "openai":
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": formatted_prompt}
                ]
            else:
                messages = [
                    {"role": "user", "content": formatted_prompt}
                ]

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": 800  # 충분한 토큰 확보
            }

            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result_data = response.json()

            # 토큰 사용량 추출 (OpenAI API 응답 형식)
            usage = result_data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            # 비용 계산
            cost_info = MessageContextBuilder.calculate_cost(self.model, input_tokens, output_tokens)

            # OpenAI 형식 응답 파싱
            content = result_data.get("choices", [{}])[0].get("message", {}).get("content", "")

            # JSON 추출 (개선: 중첩 구조 처리)
            content = content.strip()

            # 마크다운 코드블록 제거
            if "```json" in content:
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'```\s*$', '', content)
            elif "```" in content:
                content = re.sub(r'```\s*', '', content)

            # JSON 패턴 찾기 (개선: 중첩 구조 지원)
            # 방법 1: { 로 시작해서 마지막 } 까지
            start_idx = content.find('{')
            end_idx = content.rfind('}')

            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx+1]
                try:
                    result = json.loads(json_str)
                except:
                    # 실패하면 기존 regex 시도
                    json_match = re.search(r'\{.*?"title".*?"body".*?\}', content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                    else:
                        raise ValueError("JSON 형식을 찾을 수 없습니다")
            else:
                raise ValueError("JSON 형식을 찾을 수 없습니다")

            # 글자수 검증 (자르지 않음 - LLM이 제한 준수하도록 유도)
            title = result.get("title", "")
            body = result.get("body", "")

            # 브랜드 톤 검증 및 수정 + 데이터 복붙 방지 (먼저 실행)
            temp_result = {
                "title": title,
                "body": body,
                "title_over": len(title) > 40,
                "body_over": len(body) > 350
            }
            temp_result = self._validate_brand_tone(temp_result, brand, persona)
            title = temp_result["title"]
            body = temp_result["body"]

            # 본문이 300자 미만이면 자동 보강 (톤 검증 후 실행!)
            original_len = len(body)
            extended = False
            if original_len < 300:
                body = self._extend_body(body, persona, brand, products)
                extended = True

            # 실행 시간 기록
            from datetime import datetime
            now = datetime.now()
            timestamp = now.strftime("%m/%d %H:%M")
            print(f"[LOG] {timestamp} | 모델: {self.model} | 성공")

            # 최종 결과 (디버그 정보 + 비용 포함)
            result = {
                "title": title,
                "body": body,
                "title_over": len(title) > 40,
                "body_over": len(body) > 350,
                "debug_info": {
                    "original_len": original_len,
                    "final_len": len(body),
                    "extended": extended,
                    "model": self.model,
                    "provider": self.provider,
                    "timestamp": timestamp,
                    # 토큰 & 비용 정보
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost_krw": cost_info["total_cost_krw"],
                    "cost_usd": cost_info["total_cost_usd"],
                    "is_free": cost_info["is_free"]
                }
            }

            return result

        except Exception as e:
            # 폴백: 템플릿 기반 메시지
            from datetime import datetime
            now = datetime.now()
            timestamp = now.strftime("%m/%d %H:%M")
            self.last_error = str(e)
            print(f"[LOG] {timestamp} | 모델: {self.model} | 실패: {str(e)[:50]}")

            template_result = self._generate_template_message(persona, brand, purpose, products)
            template_result["debug_info"] = {
                "original_len": len(template_result.get("body", "")),
                "final_len": len(template_result.get("body", "")),
                "extended": False,
                "model": self.model,
                "provider": self.provider,
                "error": str(e),
                "fallback": True
            }
            return template_result

    def _generate_template_message(self, persona, brand, purpose, products):
        """
        LLM 실패 시 템플릿 기반 메시지 생성 (개선된 버전 - 조사 자동화, 250-350자 본문)
        """
        tone_info = brand_tones.get(brand, brand_tones["라네즈"])

        # Edge case: 빈 상품 리스트 처리
        if not products or len(products) == 0:
            # 기본 상품 정보로 대체
            products = [{
                'name': f'{brand} 대표 제품',
                'features': ['보습', '진정'],
                'description': f'{brand}의 대표 스킨케어 제품입니다.',
                'price': 50000,
                'discount_rate': 0,
                'promotions': []
            }]

        # 안전한 페르소나 이름 접근
        persona_name = persona.get('display_name') or persona.get('name', '고객')

        # 브랜드별 감성 표현
        brand_expressions = {
            "설화수": {
                "greeting": "님께",
                "intro": "소중한 시간을 내어",
                "value": "한방의 지혜가 담긴",
                "ending": "피부 본연의 아름다움을 되찾으시길 바랍니다"
            },
            "라네즈": {
                "greeting": "님",
                "intro": "바쁜 일상 속에서도",
                "value": "매일을 빛나게 하는",
                "ending": "오늘도 당신의 아름다움을 응원합니다"
            },
            "이니스프리": {
                "greeting": "님께",
                "intro": "자연과 함께하는",
                "value": "제주의 청정 자연이 담긴",
                "ending": "건강한 아름다움을 선물합니다"
            }
        }

        expr = brand_expressions.get(brand, brand_expressions["라네즈"])

        # 상품별 자연스러운 설명 재해석
        def interpret_product(product, brand):
            """상품 설명을 브랜드 톤에 맞게 자연스럽게 재해석 (할인/프로모션 포함)"""
            name = product['name']
            features = product['features']
            description = product['description']

            # 할인/프로모션 정보 추가
            promo_text = ""
            if product.get('discount_rate'):
                promo_text = f" 지금 {product['discount_rate']}% 할인 중이에요!"
            if product.get('promotions'):
                promo_text += f" [{', '.join(product['promotions'])}]"

            if brand == "설화수":
                # 우아하고 격식있는 표현 (완결된 문장)
                if "세럼" in name or "에센스" in name:
                    base = "피부 깊숙한 곳까지 한방 영양을 전달하여 탄력과 윤기를 선사하는 프리미엄 에센스입니다."
                elif "크림" in name:
                    base = "풍부한 영양감으로 피부를 감싸며, 시간이 지날수록 탄력있고 빛나는 피부로 가꿔주는 고영양 크림입니다."
                elif "아이크림" in name or "아이케어" in name:
                    base = "섬세한 눈가 피부에 집중적인 영양을 공급하여 주름과 다크서클을 개선하는 아이 케어 솔루션입니다."
                else:
                    base = "한방 성분의 정수를 담아 피부 본연의 힘을 깨우는 명품 케어입니다."
                return base + promo_text

            elif brand == "라네즈":
                # 친근하고 트렌디한 표현 (완결된 문장)
                if "세럼" in name:
                    base = "피부 속 수분을 가득 채워주면서도 끈적임 없이 산뜻한 데일리 세럼입니다."
                elif "쿠션" in name:
                    base = "아침 메이크업부터 저녁까지 무너지지 않는 완벽한 커버력과 지속력의 쿠션입니다."
                elif "크림" in name:
                    base = "촉촉한 보습감이 하루종일 지속되는 데일리 수분 크림입니다."
                else:
                    base = "바쁜 일상 속에서도 간편하게 완성하는 효과적인 피부 케어입니다."
                return base + promo_text

            else:  # 이니스프리
                # 자연스럽고 건강한 표현 (완결된 문장)
                if "세럼" in name:
                    base = "제주 자연에서 얻은 청정 성분이 피부에 생기를 불어넣는 순한 세럼입니다."
                elif "크림" in name:
                    base = "자연 유래 성분으로 피부에 부담 없이 수분과 영양을 채워주는 크림입니다."
                elif "시카" in name or "밤" in name:
                    base = "민감해진 피부를 자연의 힘으로 진정시키고 편안하게 가라앉혀주는 시카 케어입니다."
                else:
                    base = "제주의 청정 자연이 선사하는 건강한 피부 케어입니다."
                return base + promo_text

        # 안전한 필드 접근
        skin_type = persona.get('skin_type', '복합성')
        concerns = persona.get('concerns') or ['피부고민']

        # 목적별 메시지 템플릿 (250-350자, 조사 자동화, 자연스러운 재해석)
        if purpose == "맞춤 제품 추천":
            title = f"{persona_name}{expr['greeting']} 특별히 준비한 {brand} 추천"

            product_desc = interpret_product(products[0], brand)
            product_name = products[0]['name']

            if brand == "설화수":
                body = f"{persona_name}{expr['greeting']}, {skin_type} 피부의 {', '.join(concerns[:2])} 고민으로 어려움을 겪고 계신가요? "
                body += f"설화수{josa(brand, '이가')} 오랜 연구 끝에 완성한 {product_name}{josa(product_name, '을를')} 소개합니다. "
                body += f"{product_desc}입니다. "
                body += f"한방 명품 성분이 피부 깊숙이 스며들어, 단 한 번의 터치로도 깊은 영양감을 느끼실 수 있습니다. "
                body += f"효능을 중시하시는 {persona_name}{expr['greeting']} 자신있게 추천드리는 프리미엄 케어입니다. "
                body += f"지금 바로 경험해보시고, {expr['ending']}"
            elif brand == "라네즈":
                body = f"바쁜 일상 속에서도 피부 관리만큼{josa('관리', '은는')} 놓치고 싶지 않으신 {persona_name}{expr['greeting']}, 라네즈가 함께합니다. "
                body += f"{skin_type} 피부의 {', '.join(concerns[:2])} 고민, 이제 간편하게 해결하세요. "
                body += f"{product_name}{josa(product_name, '은는')} {product_desc} "
                body += f"트렌디하면서도 가성비까지 챙긴 똑똑한 선택이에요. "
                body += f"출근 전 바쁜 아침에도 5분이면 완성되는 완벽한 루틴을 경험해보세요. "
                body += f"실제 사용자 리뷰에서도 만족도가 높은 검증된 아이템입니다. "
                body += f"{expr['ending']}"
            else:  # 이니스프리
                body = f"{persona_name}{expr['greeting']}, {skin_type} 피부의 {', '.join(concerns[:2])} 고민을 제주의 자연으로 해결해보세요. "
                body += f"이니스프리 {product_name}{josa(product_name, '은는')} {product_desc} "
                body += f"제주 청정 자연 성분이 피부에 산뜻한 수분{josa('수분', '은는')} 채우고, 고민{josa('고민', '은는')} 덜어줍니다. "
                body += f"가격 부담 없이 매일 사용할 수 있어서 많은 분들께 사랑받고 있어요. "
                body += f"피부에도 지구에도 좋은 클린 뷰티로, {expr['ending']}"

        elif purpose == "신제품 론칭 안내":
            title = f"{brand} 신제품, {persona_name}{expr['greeting']} 먼저 소개합니다"

            product_desc = interpret_product(products[0], brand)
            product_name = products[0]['name']

            if brand == "설화수":
                body = f"{persona_name}{expr['greeting']} 특별한 소식을 전합니다. 설화수{josa('설화수', '이가')} 오랜 연구 끝에 완성한 신제품 {product_name}{josa(product_name, '이가')} 세상에 첫선을 보입니다. "
                body += f"{skin_type} 피부의 {', '.join(concerns[:2])} 고민을 위해 한방 명품 성분을 집약했습니다. "
                body += f"{product_desc} 피부 본연의 힘을 깨우는 프리미엄 포뮬라입니다. "
                body += f"효능을 중시하시는 분들께 자신있게 선보이는 이번 신제품, "
                body += f"우아한 아름다움을 꿈꾸시는 {persona_name}{expr['greeting']} 가장 먼저 경험해보세요. "
                body += f"{expr['ending']}"
            elif brand == "라네즈":
                body = f"기다리셨죠? 라네즈의 신제품 {product_name}{josa(product_name, '이가')} 드디어 출시되었어요! "
                body += f"트렌디한 {persona_name}{expr['greeting']}을 위해 특별히 개발한 제품입니다. "
                body += f"{product_desc} {skin_type} 피부의 {', '.join(concerns[:2])} 고민을 한 번에 해결하는 올인원 솔루션이에요. "
                body += f"가성비까지 완벽한 이 제품, 론칭 기념 특별 혜택도 놓치지 마세요. "
                body += f"SNS에서 이미 화제라는 소문! 지금 바로 만나보세요. "
                body += f"{expr['ending']}"
            else:  # 이니스프리
                body = f"새로운 시작을 알립니다. 이니스프리의 {product_name}{josa(product_name, '이가')} 출시되었습니다. "
                body += f"제주의 청정 자연이 담긴 이 제품{josa('제품', '은는')} {skin_type} 피부를 생각하며 만들어졌어요. "
                body += f"{product_desc} {', '.join(concerns[:2])} 고민이 있으신 {persona_name}{expr['greeting']} 자연의 힘으로 건강한 피부를 가꿔보세요. "
                body += f"피부에도 지구에도 좋은 클린 뷰티를 가장 먼저 경험하실 수 있습니다. "
                body += f"{expr['ending']}"

        elif purpose == "재구매 유도":
            title = f"{persona_name}{expr['greeting']}, 다시 만나 반갑습니다"

            product_desc = interpret_product(products[0], brand)
            product_name = products[0]['name']

            if brand == "설화수":
                body = f"다시 찾아뵙게 되어 영광입니다, {persona_name}{expr['greeting']}. 이전에 관심 가져주셨던 {product_name}, 기억하고 계신가요? "
                body += f"많은 분들께서 꾸준한 사용으로 눈에 띄는 피부 변화를 경험하셨다는 소식을 전합니다. "
                body += f"{product_desc} {skin_type} 피부의 {', '.join(concerns[:2])} 고민을 한방 성분으로 근본부터 케어합니다. "
                body += f"피부 본연의 건강한 빛을 되찾으실 수 있도록, 프리미엄 품질로 입증된 제품입니다. "
                body += f"소중한 인연 다시 이어가며, {expr['ending']}"
            elif brand == "라네즈":
                body = f"{persona_name}{expr['greeting']} 생각이 나서 다시 연락드려요. 예전에 찜해두셨던 {product_name}, 기억하시죠? "
                body += f"여전히 베스트셀러로 많은 사랑을 받고 있어요. {product_desc} {skin_type} 피부의 {', '.join(concerns[:2])} 고민을 해결하는 검증된 제품이거든요. "
                body += f"리뷰 평점 4.8점의 실력파! 지금 다시 시작하시면 피부{josa('피부', '이가')} 훨씬 좋아질 거예요. "
                body += f"트렌디한 {persona_name}{expr['greeting']}, 함께 해요. "
                body += f"{expr['ending']}"
            else:  # 이니스프리
                body = f"오랜만입니다, {persona_name}{expr['greeting']}. 여전히 자연친화적인 라이프스타일을 즐기고 계신가요? "
                body += f"이전에 관심 보이셨던 {product_name}{josa(product_name, '을를')} 다시 추천드립니다. "
                body += f"{product_desc} 많은 분들{josa('분들', '이가')} 꾸준히 사용하며 {skin_type} 피부를 건강하게 유지하고 계세요. "
                body += f"제주의 청정 자연과 함께 {', '.join(concerns[:2])} 고민을 자연스럽게 케어하면서, 지구도 함께 생각하는 클린 뷰티를 다시 시작해보세요. "
                body += f"순한 성분으로 매일 안심하고 사용할 수 있는 제품입니다. "
                body += f"{expr['ending']}"

        else:  # 특가/프로모션
            title = f"{persona_name}{expr['greeting']}만을 위한 특별 혜택"

            product_desc = interpret_product(products[0], brand)
            product_name = products[0]['name']

            if brand == "설화수":
                body = f"소중한 {persona_name}{expr['greeting']}, 설화수{josa('설화수', '이가')} 특별한 기회를 마련했습니다. "
                body += f"한방 명품 라인 {product_name}{josa(product_name, '을를')} 포함한 {len(products)}종의 프리미엄 제품을 특별 가격으로 만나보실 수 있습니다. "
                body += f"{skin_type} 피부의 {', '.join(concerns[:2])} 고민을 위한 완벽한 케어 루틴을 완성하세요. "
                body += f"오랜 연구로 검증된 한방 성분이 피부 근본부터 케어하며, 효능을 중시하시는 분들께 자신있게 추천하는 프리미엄 솔루션입니다. "
                body += f"{expr['ending']}"
            elif brand == "라네즈":
                body = f"{persona_name}{expr['greeting']}, 놓치면 후회할 특가 소식이에요! "
                body += f"평소 찜해두셨던 {product_name} 포함 {len(products)}종을 특별 가격에 드려요. "
                body += f"바쁜 일상 속에서도 간편하게 사용할 수 있는 아이템들로만 구성했어요. "
                body += f"{skin_type} 피부의 {', '.join(concerns[:2])} 고민을 한번에 해결하는 베스트 조합입니다. "
                body += f"가성비까지 완벽! 트렌디한 {persona_name}{expr['greeting']}, 지금 바로 장바구니 담아보세요. "
                body += f"{expr['ending']}"
            else:  # 이니스프리
                body = f"특별한 제안을 준비했습니다, {persona_name}{expr['greeting']}. "
                body += f"이니스프리의 {product_name} 외 제주의 청정 자연이 담긴 {len(products)}가지 제품을 특가로 만나보세요. "
                body += f"{skin_type} 피부의 {', '.join(concerns[:2])} 고민을 자연의 힘으로 케어하면서, 가격 부담까지 덜 수 있어요. "
                body += f"피부에도 지구에도 좋은 클린 뷰티 루틴을 지금 시작해보세요. "
                body += f"자연과 함께하는 건강한 아름다움을 경험하실 수 있습니다. "
                body += f"{expr['ending']}"

        # 길이 제한
        title = title[:40]
        body = body[:350]

        return {"title": title, "body": body}


# 테스트 코드
if __name__ == "__main__":
    from data.personas import personas, products

    # API 키 설정 필요
    # generator = MessageGenerator(api_key="your-huggingface-token")

    # 테스트 데이터
    test_persona = personas[0]  # 민지(25세)
    test_products = products[:3]
    test_brand = "라네즈"
    test_purpose = "맞춤 제품 추천"

    print(f"\n📌 테스트 설정:")
    print(f"   페르소나: {test_persona['name']}")
    print(f"   브랜드: {test_brand}")
    print(f"   목적: {test_purpose}")
    print(f"   상품 수: {len(test_products)}")

    # 메시지 생성
    # message = generator.generate(test_persona, test_brand, test_purpose, test_products)
    #
    # print(f"\n📨 생성된 메시지:")
    # print(f"   제목: {message['title']}")
    # print(f"   본문: {message['body']}")
