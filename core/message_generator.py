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
from config import PURPOSE_NAMES, MODEL_OPTIONS, get_purpose_name, get_ollama_url


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
            "api_url": "https://router.huggingface.co/novita/v3/openai/chat/completions",
            "display_name": "Qwen 2.5 7B (HuggingFace API, 무료)",
            "cost": "무료"
        },
        "exaone3.5:7.8b": {
            "provider": "ollama",
            "api_url": get_ollama_url(),
            "display_name": "EXAONE 3.5 7.8B (Ollama, 한국어 특화)",
            "cost": "무료"
        },
        "qwen2.5:7b": {
            "provider": "ollama",
            "api_url": get_ollama_url(),
            "display_name": "Qwen 2.5 7B (Ollama, 로컬)",
            "cost": "무료"
        },
        "gpt-4o-mini": {
            "provider": "openai",
            "api_url": "https://api.openai.com/v1/chat/completions",
            "display_name": "GPT-4o-mini (₩0.33/회)",
            "cost": "~₩0.33/회"
        },
        "gpt-4o": {
            "provider": "openai",
            "api_url": "https://api.openai.com/v1/chat/completions",
            "display_name": "GPT-4o (₩5.5/회)",
            "cost": "~₩5.5/회"
        }
    }

    def __init__(self, api_key=None, openai_api_key=None, model="exaone3.5:7.8b", temperature=0.7):
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

        # 모델 설정 (없으면 기본 EXAONE)
        model_config = self.SUPPORTED_MODELS.get(model, self.SUPPORTED_MODELS["exaone3.5:7.8b"])
        self.provider = model_config["provider"]
        self.api_url = model_config["api_url"]

        # API 키 확인
        if self.provider == "ollama":
            # Ollama는 로컬 실행이라 API 키 불필요
            self.llm = True
            self.active_api_key = "ollama"  # 더미 값
        elif self.provider == "openai" and openai_api_key:
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
        """Few-shot learning을 위한 브랜드별/페르소나별 우수 예시 (2024.01 업데이트)"""

        # 350자 이내로 맞춘 Few-shot 예시 - 친근한 CRM 스타일
        examples = {
            "라네즈": {
                "맞춤 제품 추천": """
📌 예시 (라네즈 - 친근한 CRM 스타일, 본문 340자):
{
  "title": "라네즈의 블루 에너지 세트는 어떠세요?",
  "body": "바쁜 일상 속에도 피부 건강을 잊지 않는 민지님! 라네즈가 당신을 위해 특별한 프로모션을 준비했습니다. 복합성 피부의 모공과 피지 고민을 효과적으로 해결할 블루 에너지 세트를 만나보세요. 블루 에너지 에센스 인 로션 EX, 래디언서 선크림, 블루 에너지 스킨 토너 EX 모두 40% 할인을 받아요. 지금 바로 이 기회를 놓치지 마세요! 오늘이 마지막일 수 있어요."
}""",
                "재구매 유도": """
📌 예시 (라네즈 - 친근한 CRM 스타일, 본문 320자):
{
  "title": "민지님, 워터뱅크 다시 만나볼까요?",
  "body": "민지님, 지난번 워터뱅크 세럼 어떠셨어요? 피부가 촉촉해졌다는 후기가 정말 많더라고요. 이번엔 크림도 함께 써보시는 건 어떨까요? 세럼이랑 같이 쓰면 보습력이 훨씬 오래간대요. 재구매 고객님께만 드리는 15% 추가 할인도 있어요. 놓치면 아쉬울 거예요!"
}""",
                "특가/프로모션 알림": """
📌 예시 (라네즈 - 친근한 CRM 스타일, 본문 300자):
{
  "title": "민지님, 이 특가 놓치면 안 돼요!",
  "body": "민지님을 위한 깜짝 특가 소식이에요! 워터뱅크 세럼+크림 세트가 40% 할인 중이에요. 복합성 피부 고민, 이 조합이면 충분해요. 리뷰 평점 4.8점의 검증된 베스트셀러예요. 오늘만 이 가격이니까 서두르세요. 장바구니에 담아두셨다가 품절되면 후회할 수 있어요!"
}""",
                "신제품 론칭 안내": """
📌 예시 (라네즈 - 친근한 CRM 스타일, 본문 310자):
{
  "title": "민지님, 라네즈 신상 먼저 알려드려요!",
  "body": "기다리셨죠? 라네즈 워터뱅크 NEW 버전이 드디어 나왔어요! 수분 지속력이 2배로 강화됐대요. 민지님 피부 타입에 딱 맞을 것 같아서 먼저 알려드려요. 론칭 기념 20% 할인에 미니어처 세트까지 증정해요. 한정 수량이라 빨리 품절될 수 있어요. 지금 확인해보세요!"
}"""
            },
            "설화수": {
                "맞춤 제품 추천": """
📌 예시 (설화수 - 친근하면서도 품격있는 스타일, 본문 340자):
{
  "title": "수진님, 설화수 자음생 라인은 어떠세요?",
  "body": "피부 관리에 진심이신 수진님! 설화수가 특별한 제안을 준비했어요. 복합성 피부의 탄력 고민, 자음생 에센스로 해결해보세요. 한방 성분이 피부 깊숙이 영양을 전달해요. 꾸준히 쓰시는 분들 사이에서 피부결이 달라졌다는 후기가 많아요. 지금 구매하시면 미니어처 세트도 함께 드려요. 소중한 분께 선물하기에도 좋답니다!"
}""",
                "재구매 유도": """
📌 예시 (설화수 - 친근하면서도 품격있는 스타일, 본문 330자):
{
  "title": "수진님, 자음생 에센스 다시 만나볼까요?",
  "body": "수진님, 지난번 자음생 에센스 어떠셨어요? 피부가 훨씬 탄탄해졌다는 분들이 많더라고요. 이번엔 윤조 에센스도 함께 써보시는 건 어떨까요? 둘이 같이 쓰면 시너지가 대단해요. 재구매 고객님께만 드리는 특별 샘플 세트도 준비했어요. 계속 함께해주셔서 감사해요!"
}""",
                "특가/프로모션 알림": """
📌 예시 (설화수 - 친근하면서도 품격있는 스타일, 본문 320자):
{
  "title": "수진님, 설화수 특별 혜택 놓치지 마세요!",
  "body": "수진님께 특별한 소식이에요! 자음생 라인을 30% 할인된 가격에 만나보실 수 있어요. 탄력과 윤기를 동시에 잡는 프리미엄 케어예요. 명절 선물로도 정말 좋은 구성이에요. 한정 수량이라 서두르셔야 해요. 이번 기회 놓치면 아쉬울 거예요!"
}""",
                "신제품 론칭 안내": """
📌 예시 (설화수 - 친근하면서도 품격있는 스타일, 본문 320자):
{
  "title": "수진님, 설화수 신제품 먼저 알려드려요!",
  "body": "수진님, 기다리셨죠? 설화수가 새로운 제품을 내놨어요! 오랜 연구 끝에 완성한 포뮬라예요. 탄력과 윤기 고민을 한번에 해결할 수 있대요. 론칭 기념 특별 혜택도 있어요. 수진님처럼 피부 관리에 진심이신 분들께 먼저 알려드리고 싶었어요. 지금 바로 확인해보세요!"
}"""
            },
            "이니스프리": {
                "맞춤 제품 추천": """
📌 예시 (이니스프리 - 친근한 자연주의 스타일, 본문 340자):
{
  "title": "서준님, 그린티 시드 세럼은 어떠세요?",
  "body": "온 가족 피부 건강을 챙기시는 서준님! 이니스프리가 딱 맞는 제품을 찾았어요. 그린티 시드 세럼은 자연 유래 성분이라 남녀노소 누구나 안심하고 쓸 수 있어요. 대용량 리필도 있어서 가성비까지 챙길 수 있답니다. 지금 구매하시면 사은품도 드려요. 제주 자연의 힘을 경험해보세요!"
}""",
                "재구매 유도": """
📌 예시 (이니스프리 - 친근한 자연주의 스타일, 본문 320자):
{
  "title": "서준님, 그린티 리필할 때 됐어요!",
  "body": "서준님, 지난번 구매하신 제품 잘 쓰고 계시죠? 슬슬 리필할 때가 된 것 같아요. 대용량 리필팩이 20% 할인 중이에요. 온 가족이 쓰시니까 금방 떨어지시죠? 이번에 사은품으로 미니어처 세트도 드려요. 알뜰하게 장바구니 채워보세요!"
}""",
                "특가/프로모션 알림": """
📌 예시 (이니스프리 - 친근한 자연주의 스타일, 본문 300자):
{
  "title": "서준님, 이 특가 놓치면 아까워요!",
  "body": "서준님을 위한 깜짝 특가예요! 베스트셀러 대용량 제품이 40% 할인 중이에요. 온 가족이 함께 쓰는 바디/헤어 제품에 사은품까지! 순한 성분에 가격까지 착해요. 오늘만 이 가격이니까 서두르세요. 장바구니에 담아두셨다 품절되면 후회해요!"
}""",
                "신제품 론칭 안내": """
📌 예시 (이니스프리 - 친근한 자연주의 스타일, 본문 310자):
{
  "title": "서준님, 이니스프리 신상 나왔어요!",
  "body": "서준님, 반가운 소식이에요! 온 가족이 함께 쓸 수 있는 순한 신제품이 나왔어요. 제주 녹차 성분이 듬뿍 들어가서 아이부터 어른까지 안심이에요. 론칭 기념 대용량 특가에 사은품까지 드려요. 빨리 품절될 수 있으니 서두르세요!"
}"""
            },
            "에뛰드": {
                "맞춤 제품 추천": """
📌 예시 (에뛰드 - 트렌디하고 친근한 스타일, 본문 340자):
{
  "title": "하은님, 플레이컬러 팔레트는 어떠세요?",
  "body": "SNS 트렌드에 빠삭한 하은님! 에뛰드가 딱 맞는 걸 찾았어요. 플레이컬러 팔레트 신상이에요! 민감성 피부도 OK인 순한 포뮬라예요. 인스타에서 벌써 난리났더라고요. 트러블 걱정 없이 트렌디한 메이크업 완성할 수 있어요. 지금 구매하면 20% 할인에 미니 립까지 증정이에요. 놓치면 후회할 거예요!"
}""",
                "재구매 유도": """
📌 예시 (에뛰드 - 트렌디하고 친근한 스타일, 본문 320자):
{
  "title": "하은님, 에뛰드 또 만나요!",
  "body": "하은님, 지난번 제품 어떠셨어요? 리뷰 남겨주시면 포인트 적립 이벤트도 있어요! 이번에 나온 신상 립이 하은님 스타일에 딱일 것 같아요. 인스타에서 품절 대란이래요. 단골분께만 드리는 선공개 15% 할인 놓치지 마세요!"
}""",
                "특가/프로모션 알림": """
📌 예시 (에뛰드 - 트렌디하고 친근한 스타일, 본문 300자):
{
  "title": "하은님, 이 특가 진짜 대박이에요!",
  "body": "하은님을 위한 깜짝 특가예요! SNS 핫템 모음이 50% 할인 중이에요. 트렌디한 메이크업 완성하면서 지갑도 지키는 똑똑한 선택이에요. 포인트 적립에 사은품까지! 오늘만 이 가격이니까 서두르세요. 품절되면 진짜 아쉬울 거예요!"
}""",
                "신제품 론칭 안내": """
📌 예시 (에뛰드 - 트렌디하고 친근한 스타일, 본문 310자):
{
  "title": "하은님, 에뛰드 신상 먼저 알려줄게요!",
  "body": "하은님, 드디어 나왔어요! 인스타 티저만 올라왔는데 벌써 난리난 그 신상이에요! 하은님 스타일에 완전 딱인 컬러 구성이에요. 론칭 기념 20% 할인에 한정판 파우치까지 증정해요. 빨리 품절될 거 같으니 서두르세요!"
}"""
            },
            "메이크온": {
                "맞춤 제품 추천": """
📌 예시 (메이크온 - 친근한 전문가 스타일, 본문 340자):
{
  "title": "지아님, LED 마스크는 어떠세요?",
  "body": "홈케어에 진심이신 지아님! 메이크온이 딱 맞는 제품을 찾았어요. LED 마스크로 집에서 피부과급 케어를 해보세요. 지성 피부 트러블과 모공 고민을 한번에 잡을 수 있어요. 갈바닉 기능까지 있어서 세럼 흡수율도 확 올라가요. 꾸준히 쓰면 피부가 달라지는 게 눈에 보여요. 지금 구매하면 전용 세럼도 증정이에요!"
}""",
                "재구매 유도": """
📌 예시 (메이크온 - 친근한 전문가 스타일, 본문 320자):
{
  "title": "지아님, 전용 세럼 리필할 때예요!",
  "body": "지아님, 메이크온 디바이스 잘 쓰고 계시죠? 피부가 많이 좋아지셨을 것 같아요. 전용 세럼이랑 같이 쓰면 효과가 배가 된다는 거 아시죠? 이번에 새로 나온 업그레이드 세럼 추천드려요. 재구매 고객님 한정 20% 할인이에요. 놓치면 아쉬울 거예요!"
}""",
                "특가/프로모션 알림": """
📌 예시 (메이크온 - 친근한 전문가 스타일, 본문 300자):
{
  "title": "지아님, 이 특가 진짜 대박이에요!",
  "body": "지아님을 위한 깜짝 특가예요! 메이크온 시그니처 디바이스가 30% 할인 중이에요. LED+갈바닉 듀얼 기능으로 피부과급 케어를 집에서! 전용 세럼까지 증정이에요. 한정 수량이라 빨리 품절될 수 있어요. 서두르세요!"
}""",
                "신제품 론칭 안내": """
📌 예시 (메이크온 - 친근한 전문가 스타일, 본문 310자):
{
  "title": "지아님, 메이크온 신상 나왔어요!",
  "body": "지아님, 기다리셨죠? 차세대 디바이스가 드디어 출시됐어요! LED 파장이 업그레이드되고 갈바닉 기능도 강화됐어요. 트러블과 모공 케어에 특화된 신기술이에요. 론칭 기념 25% 할인에 전용 세럼까지 드려요. 빨리 품절될 것 같으니 서두르세요!"
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
            # 이름에서 나이 제거: "장수빈(25세)" → "장수빈"
            raw_name = persona.get('name', '')
            if '(' in raw_name:
                name = raw_name.split('(')[0].strip()
            else:
                name = raw_name

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

        # 0. 딱딱한 표현 → 친근한 표현 변환 (모든 브랜드 공통)
        # 긴 표현부터 먼저 처리해야 부분 매칭 방지
        friendly_replacements = [
            # 긴 표현 먼저 (부분 매칭 방지)
            ("만나보실 수 있습니다", "만나보세요"),
            ("경험하실 수 있습니다", "경험해보세요"),
            ("받으실 수 있습니다", "받으세요"),
            ("확인하실 수 있습니다", "확인해보세요"),
            ("피부 본연의 아름다움을 되찾으시길 바랍니다", "피부 본연의 아름다움을 되찾아보세요"),
            ("되찾으시길 바랍니다", "되찾아보세요"),
            ("특별한 기회를 마련했습니다", "특별한 기회를 준비했어요"),
            ("기회를 마련했습니다", "기회를 준비했어요"),
            ("마련했습니다", "마련했어요"),
            ("준비되어 있습니다", "준비했어요"),
            ("준비하였습니다", "준비했어요"),
            ("마련하였습니다", "마련했어요"),
            ("소개해 드립니다", "준비했어요"),
            ("안내해 드립니다", "알려드려요"),
            ("추천해 드립니다", "추천드려요"),
            ("경험하시기 바랍니다", "경험해보세요"),
            ("확인하시기 바랍니다", "확인해보세요"),
            ("만나보시기 바랍니다", "만나보세요"),
            ("이용하시기 바랍니다", "이용해보세요"),
            ("하시기 바랍니다", "해보세요"),
            ("되시길 바랍니다", "되실 거예요"),
            ("첫선을 보입니다", "드디어 나왔어요"),
            # 딱딱한 존댓말 → 친근한 존댓말 (ㅂ니다 → 요 체계)
            ("출시되었습니다", "출시됐어요"),
            ("출시했습니다", "출시했어요"),
            ("제공합니다", "제공해요"),
            ("만들어줍니다", "만들어줘요"),
            ("도와줍니다", "도와줘요"),
            ("전달합니다", "전달해요"),
            ("담았습니다", "담았어요"),
            ("소개드립니다", "준비했어요"),
            ("안내드립니다", "알려드려요"),
            ("추천드립니다", "추천드려요"),
            ("선보입니다", "나왔어요"),
            ("있습니다", "있어요"),
            ("됩니다", "돼요"),
            ("합니다", "해요"),
            ("입니다", "예요"),
            ("습니다", "어요"),
            # 광고/딱딱한 느낌 제거
            ("소중한 ", ""),  # "소중한 OO님께" 패턴
            ("님께,", "님,"),  # 쉼표 앞 "께" 제거
            ("고객님께", "님께"),
            ("고객 여러분", ""),
            ("특별히 준비한", "준비한"),
            ("엄선된", ""),
            ("특별히 제작된", "만든"),
            ("탁월한 성분을 담았답니다", "좋은 성분이 가득해요"),
            ("프리미엄 솔루션입니다", "프리미엄 솔루션이에요"),
            ("완성하세요", "완성해보세요"),
            ("케어하며", "케어해주고"),
        ]

        for old, new in friendly_replacements:
            title = title.replace(old, new)
            body = body.replace(old, new)

        # 중국어 문자 제거 (유니코드 범위: 4E00-9FFF)
        import re
        body = re.sub(r'[\u4e00-\u9fff]+', '', body)
        title = re.sub(r'[\u4e00-\u9fff]+', '', title)

        # 영어 단어 제거 (Trial, OK 등 - 한글 사이에 끼어있는 영어)
        body = re.sub(r'[A-Za-z]{2,}', '', body)
        title = re.sub(r'[A-Za-z]{2,}', '', title)

        # 깨진 텍스트 패턴 제거
        body = re.sub(r'함서\w*님', '', body)
        title = re.sub(r'함서\w*님', '', title)

        # ★ 이름에서 나이 제거 - "서수진(33세)님" → "서수진님"
        # 패턴: 이름(숫자세)님 또는 이름(숫자)님, 또는 이름(숫자세) (님 없는 경우도)
        body = re.sub(r'([가-힣]{2,4})\(\d+세?\)님', r'\1님', body)
        body = re.sub(r'([가-힣]{2,4})\(\d+세?\)', r'\1', body)  # 님 없는 경우
        title = re.sub(r'([가-힣]{2,4})\(\d+세?\)님', r'\1님', title)
        title = re.sub(r'([가-힣]{2,4})\(\d+세?\)', r'\1', title)  # 님 없는 경우

        # ★ 이름 환각(hallucination) 교정 - Qwen이 잘못 생성한 이름 수정
        # 고객 이름이 2-4글자 한글이라 가정하고, 잘못된 이름 패턴을 찾아서 교체
        if name:
            correct_name_pattern = f"{name}님"

            # 비슷하지만 잘못된 이름 패턴들 (예: 정지호 → 진지호, 지지호 등)
            # 첫 글자가 다르거나 한 글자가 다른 경우
            korean_name_pattern = r'[가-힣]{2,4}님'

            def replace_wrong_name(text):
                """잘못된 이름을 올바른 이름으로 교체"""
                import re
                # 모든 "XX님" 패턴을 찾음
                matches = re.findall(korean_name_pattern, text)
                for match in matches:
                    # 올바른 이름이 아니면 교체
                    if match != correct_name_pattern and match != "고객님":
                        text = text.replace(match, correct_name_pattern)
                return text

            body = replace_wrong_name(body)
            title = replace_wrong_name(title)

            # 이름 없이 "님께", "님!" 등으로 시작하는 경우 이름 추가
            body = re.sub(r'^님께', f'{name}님께', body)
            body = re.sub(r'^님!', f'{name}님!', body)
            title = re.sub(r'^님께', f'{name}님께', title)
            title = re.sub(r'^님!', f'{name}님!', title)

        # 연속 공백 정리
        body = re.sub(r'\s+', ' ', body).strip()
        title = re.sub(r'\s+', ' ', title).strip()

        # 브랜드별 금지 표현 (톤 미스매치)
        forbidden_expressions = {
            "설화수": {
                # 설화수는 우아하고 격식있는 톤 → 캐주얼한 표현 금지
                "forbidden": ["GO!", "ㅎㅎ", "ㅋㅋ", "~요!", "꿀팁", "꿀조합", "JMT", "TMI",
                              "핫한", "핫템", "레알", "진짜루", "존맛", "갓성비", "뿌듯"],
                "replace": {
                    "GO!": "경험해보세요",
                    "꿀조합": "최상의 조합",
                    "핫한": "주목받는",
                    "핫템": "인기 제품",
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
                " 한방 성분이 피부 깊숙이 영양을 전달해줘요.",
                f" {concern} 고민이 있다면 더욱 효과적이에요.",
                " 피부 본연의 빛을 되찾을 수 있어요.",
                f" {feature} 효과와 함께 피부 탄력까지 케어해보세요.",
                " 지금 바로 이 기회를 놓치지 마세요!",
                " 피부 속부터 채워지는 깊은 보습감을 느껴보세요.",
                " 오늘이 마지막일 수 있어요.",
            ]
        elif brand == "이니스프리":
            all_extensions = [
                " 제주의 청정 자연 성분이 피부 고민을 케어해줘요.",
                f" {concern} 걱정은 이제 자연에게 맡겨보세요.",
                " 자연이 주는 건강한 아름다움을 느껴보세요.",
                f" {feature} 효과와 함께 순한 성분으로 피부 진정까지!",
                " 지금 바로 이 기회를 놓치지 마세요!",
                " 피부에도 환경에도 좋은 클린뷰티예요.",
                " 오늘이 마지막일 수 있어요.",
            ]
        else:  # 라네즈, 헤라, 아이오페 등 기타 브랜드
            all_extensions = [
                " 딱 맞는 제품이에요!",
                f" {concern} 고민, 이제 해결해보세요.",
                " 매일 쓸수록 달라지는 피부결을 경험해보세요.",
                f" {feature} 효과로 하루종일 촉촉한 피부를 유지해요.",
                " 지금 바로 이 기회를 놓치지 마세요!",
                " 피부 컨디션이 좋아지는 걸 느끼실 거예요.",
                " 오늘이 마지막일 수 있어요.",
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

    def _validate_message(self, title: str, body: str, customer_name: str) -> dict:
        """
        메시지 품질 검증

        Returns:
            {
                'valid': True/False,
                'issues': ['글자수 부족', '이름 횟수 초과', ...],
                'stats': {'body_len': 300, 'name_count': 2, ...}
            }
        """
        issues = []

        # 본문 글자수 체크 (300~350자)
        body_len = len(body)
        if body_len < 300:
            issues.append(f'본문 글자수 부족 ({body_len}자 < 300자)')
        elif body_len > 400:
            issues.append(f'본문 글자수 초과 ({body_len}자 > 400자)')

        # 제목 글자수 체크 (40자 이내)
        title_len = len(title)
        if title_len > 45:
            issues.append(f'제목 글자수 초과 ({title_len}자 > 45자)')

        # 이름 횟수 체크 (2~4번 허용)
        name_pattern = f'{customer_name}님'
        name_count = body.count(name_pattern) + title.count(name_pattern)
        if name_count < 1:
            issues.append(f'이름 부족 ({name_count}번 < 1번)')
        elif name_count > 4:
            issues.append(f'이름 과다 ({name_count}번 > 4번)')

        # 금지어 체크
        banned_words = ['귀하', '고객님', '분들께', '소개드립니다', '(제품명)', '(피부타입)']
        found_banned = [w for w in banned_words if w in body or w in title]
        if found_banned:
            issues.append(f'금지어 포함: {", ".join(found_banned)}')

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'stats': {
                'body_len': body_len,
                'title_len': title_len,
                'name_count': name_count
            }
        }

    def _fix_message(self, title: str, body: str, customer_name: str, validation: dict) -> tuple:
        """
        검증 실패 시 간단한 후처리 수정
        """
        fixed_title = title
        fixed_body = body

        # 이름이 3번 이상이면 중간 것들 제거
        name_pattern = f'{customer_name}님'
        name_count = validation['stats']['name_count']

        if name_count > 3:
            # 본문에서 중간에 있는 이름들 제거 (첫번째, 마지막만 유지)
            parts = fixed_body.split(name_pattern)
            if len(parts) > 3:
                # 첫 부분 + 이름 + 중간들(이름 없이) + 이름 + 마지막 부분
                fixed_body = parts[0] + name_pattern + ''.join(parts[1:-1]) + name_pattern + parts[-1]

        # 금지어 대체
        replacements = {
            '귀하': '',
            '고객님': f'{customer_name}님',
            '분들께': '',
            '소개드립니다': '준비했어요',
            '(제품명)': '',
            '(피부타입)': ''
        }
        for old, new in replacements.items():
            fixed_title = fixed_title.replace(old, new)
            fixed_body = fixed_body.replace(old, new)

        return fixed_title, fixed_body

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

            # 고객 이름 추출 (persona에서) - 나이 제거
            raw_name = persona.get("name", "고객")
            # "서수진(33세)" -> "서수진" 추출
            if '(' in raw_name:
                customer_name = raw_name.split('(')[0].strip()
            else:
                customer_name = raw_name

            # 프롬프트 생성 (v12 - 간결하고 명확한 지시)
            formatted_prompt = f"""브랜드: {brand}
고객: {customer_name}
목적: {purpose_kr}

{optimized_context}

JSON으로 출력: {{"title":"...", "body":"..."}}"""""

            # API 호출 (OpenAI 또는 HuggingFace)
            headers = {
                "Authorization": f"Bearer {self.active_api_key}",
                "Content-Type": "application/json"
            }

            # 발신목적별 시스템 메시지 템플릿
            common_rules = f"""당신은 아모레퍼시픽 CRM 마케팅 메시지 작성 전문가입니다.

[필수 규칙]
1. 본문 300~350자 (7~9문장)
2. "{customer_name}님" 2~3번만 사용 (첫문장 + 중간 or 마지막)
3. 친근한 말투: ~해요, ~예요, ~세요 (합니다/입니다 금지)
4. 고객 프로필(피부타입, 관심사, 라이프스타일)을 자연스럽게 반영
5. 추천 상품의 특징과 혜택을 구체적으로 언급

[금지 사항]
- 이름에 나이 붙이기: (33세), (25세) 등
- 괄호 안 데이터: (280,000원), (+10% 할인) 등
- 상투적 마무리: "오늘도 당신의 아름다움을 응원합니다"
- 이모지: 📈, 📊, ✨ 등
- 플레이스홀더: (제품명), (피부타입)

[마무리 예시]
- "지금 바로 이 기회를 놓치지 마세요!"
- "오늘이 마지막일 수 있어요."
- "장바구니에 담아보세요!"
- "이번 기회 놓치면 아쉬울 거예요."""

            priority_prompts = {
                "onboarding": f"""{common_rules}

[발신목적: 온보딩 - 신규 고객 환영]
- 환영하는 톤, 구매 압박 없이 브랜드 소개
- 첫 방문 혜택, 베스트셀러 가볍게 언급

[좋은 예시]
{customer_name}님, {brand}에 처음 오신 것을 환영해요! 저희는 피부 본연의 아름다움을 지켜드리는 브랜드예요. 복합성 피부도 편안하게 사용할 수 있는 순한 제품들을 준비했어요. 베스트셀러 윤조에센스는 많은 분들이 첫 제품으로 선택하고 계세요. 피부 깊숙이 수분을 전달하고 촉촉함이 오래 지속되는 게 특징이에요. 신규 회원 혜택으로 특별 쿠폰도 받으실 수 있어요. 천천히 둘러보시면서 피부에 맞는 제품을 찾아보세요. {customer_name}님의 뷰티 여정을 함께할 수 있어서 기뻐요!""",

                "engagement": f"""{common_rules}

[발신목적: 참여유도 - 탐색 중인 고객]
- 가벼운 권유, 구매보다 탐색/찜 유도
- 인기 상품, 리뷰 언급으로 관심 유도

[좋은 예시]
바쁜 일상 속에도 피부 건강을 잊지 않는 {customer_name}님! {brand}에서 요즘 가장 인기 있는 아이템들을 모아봤어요. 건조한 계절에 딱 맞는 고보습 라인이 많은 사랑을 받고 있어요. 가볍게 발리면서도 촉촉함이 하루 종일 유지되는 게 장점이에요. 마음에 드시는 제품이 있다면 찜 버튼으로 담아두셔도 좋아요. 실제 사용자들의 생생한 리뷰도 한번 살펴보세요. 지금 보시는 제품들은 할인 중이라 더 좋은 기회예요. {customer_name}님, 부담 없이 편하게 둘러보시다 가세요!""",

                "conversion": f"""{common_rules}

[발신목적: 전환유도 - 구매 직전 고객]
- 혜택과 신뢰 강조, 마지막 한 푸시
- 할인율, 사은품, 무료배송 등 구체적 혜택 언급

[좋은 예시]
{customer_name}님, 관심 가지셨던 {brand} 제품 소식이에요! 지금이 정말 좋은 타이밍이에요. 특별 할인 중이라 평소보다 훨씬 합리적인 가격에 만나볼 수 있어요. 피부에 깊은 영양을 전달하고 탄력을 케어해 줘요. 실제 사용자들의 리뷰도 정말 좋아서 재구매율이 높은 제품이에요. 지금 구매하시면 미니어처 사은품도 함께 받으실 수 있어요. 무료 배송은 물론 교환과 반품도 부담 없이 가능해요. {customer_name}님, 망설이셨던 그 제품 지금 장바구니에 담아보세요!""",

                "reactivation": f"""{common_rules}

[발신목적: 재활성화 - 휴면 고객]
- 부드러운 재회, 구매 압박 없이
- 신제품/리뉴얼 소식, 돌아온 고객 혜택 언급

[좋은 예시]
{customer_name}님, 정말 오랜만이에요! 그동안 잘 지내셨나요? {brand}에 그사이 새롭고 좋은 소식들이 많이 생겼어요. 인기 라인이 리뉴얼되어서 더욱 좋아졌어요. 예전에 좋아하셨던 보습 라인도 성분이 업그레이드됐어요. 오랜만에 찾아주시는 분께 드리는 특별 혜택도 준비되어 있어요. 부담 없이 가볍게 구경만 하셔도 괜찮아요. 시간 되실 때 편하게 한번 들러보시는 건 어떠세요? {customer_name}님을 다시 만나면 정말 반가울 것 같아요!""",

                "default": f"""{common_rules}

[발신목적: 프로모션 - 할인/혜택 안내]
- 친근하게 프로모션 안내
- 구체적 할인율, 상품 특징, 긴급성 강조

[좋은 예시]
바쁜 일상 속에도 피부 건강을 잊지 않는 {customer_name}님! {brand}가 특별한 프로모션을 준비했어요. 복합성 피부의 모공과 피지 고민을 효과적으로 해결할 제품을 만나보세요. 피부 속부터 수분을 채워주고 깊은 보습감을 전달해요. 꾸준히 사용하면 피부결이 부드러워지고 탄력도 느낄 수 있어요. 지금 구매하시면 40% 할인 혜택까지 받을 수 있어요. 무료 배송에 사은품까지 드려요. {customer_name}님, 지금 바로 이 기회를 놓치지 마세요! 오늘이 마지막일 수 있어요."""
            }

            # 고객의 발신목적 코드 가져오기
            from core.customer_analytics import get_message_priority
            priority_info = get_message_priority(persona)
            priority_code = priority_info.get('priority_code', 'default')

            # 발신목적에 맞는 시스템 메시지 선택
            system_message = priority_prompts.get(priority_code, priority_prompts["default"])

            # OpenAI / Ollama 모델은 시스템 메시지 사용
            if self.provider in ("openai", "ollama"):
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": formatted_prompt}
                ]
            else:
                # HuggingFace (Qwen 등) - 발신목적별 지시 + 친근한 톤 강화

                # 발신목적별 톤 지시
                purpose_tone_guide = {
                    "onboarding": f"""[온보딩 메시지 - 신규 고객 환영]
- 환영하고 안내하는 톤, 구매 압박 금지
- "처음 오신 것을 환영해요", "천천히 둘러보세요" 느낌
- 브랜드 소개 + 베스트셀러 가볍게 언급""",

                    "engagement": f"""[참여유도 메시지 - 탐색 고객]
- 가벼운 권유, 구매보다 탐색/찜 유도
- "한번 구경해보세요", "마음에 드시면 담아두세요" 느낌
- 인기 제품 소개 + 리뷰 언급""",

                    "conversion": f"""[전환유도 메시지 - 구매 전환]
- 관심 존중 + 혜택/신뢰 강조
- "관심 가지셨던", "지금이 좋은 기회예요" 느낌
- 할인/사은품 혜택 강조 + 후기 언급""",

                    "reactivation": f"""[재활성화 메시지 - 휴면 고객]
- 부드러운 재회, 구매 압박 금지
- "오랜만이에요", "그동안 새로운 것들이 생겼어요" 느낌
- 신제품/리뉴얼 소식 + 특별 혜택 언급""",

                    "default": f"""[프로모션 메시지]
- 친근하게 혜택 안내
- "특별한 기회예요", "놓치면 아쉬워요" 느낌
- 할인율/사은품 구체적으로 언급"""
                }

                tone_guide = purpose_tone_guide.get(priority_code, purpose_tone_guide["default"])

                qwen_system = f"""한국 화장품 CRM 메시지 작성 전문가.

[글자수 규칙 - 가장 중요!]
- 본문: 반드시 320~350자 작성 (현재 200자 수준으로 너무 짧음!)
- 9~10문장 필수 (각 문장 35~40자)
- 200자대는 실패! 최소 320자 이상!

[이름 규칙]
- "{customer_name}님"만 사용
- 절대 금지: 나이, 괄호, (33세), (20세) 등

[말투 규칙]
- ~해요/~예요만 사용
- 금지: ~합니다, ~입니다, 경험하실 수 있습니다

[금지 사항]
- (280,000원), (+10% 할인), (+6일) 등 괄호 데이터
- "오늘도 당신의 아름다움을 응원합니다" 같은 상투적 마무리
- "감사해요" 마무리

{tone_guide}

[320자 예시 - 이 길이를 참고!]
{customer_name}님, 바쁜 일상 속에도 피부 건강을 잊지 않으셨군요! {brand}가 특별한 프로모션을 준비했어요. 복합성 피부의 고민을 효과적으로 해결할 제품들을 만나보세요. 피부 속부터 수분을 채워주는 보습 라인이에요. 꾸준히 쓰시는 분들 사이에서 피부결이 달라졌다는 후기가 정말 많아요. 지금 구매하시면 특별 할인에 미니어처 세트까지 드려요. 무료 배송은 물론 교환과 반품도 부담 없이 가능해요. 이번 기회를 놓치면 정말 아쉬울 거예요. {customer_name}님, 지금 바로 장바구니에 담아보세요!

출력: JSON만 {{"title":"...","body":"..."}}"""

                messages = [
                    {"role": "system", "content": qwen_system},
                    {"role": "user", "content": formatted_prompt}
                ]

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": 800  # 충분한 토큰 확보
            }

            # Ollama는 인증 헤더 불필요, CPU 추론은 느리므로 타임아웃 길게
            if self.provider == "ollama":
                headers = {"Content-Type": "application/json"}
                response = requests.post(self.api_url, headers=headers, json=payload, timeout=180)
            else:
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

            # ========== 후처리 검증 ==========
            # customer_name은 이미 위에서 나이 제거된 상태
            validation = self._validate_message(title, body, customer_name)

            # 검증 실패 시 후처리 수정 시도
            if not validation['valid']:
                title, body = self._fix_message(title, body, customer_name, validation)
                # 수정 후 재검증
                validation = self._validate_message(title, body, customer_name)

            original_len = len(body)
            extended = False

            # ========== 글자수 부족 시 자동 보강 ==========
            if len(body) < 300:
                body = self._extend_body(body, persona, brand, products)
                extended = True

            # ========== 이름 누락 패턴 수정 ==========
            # "의 선택", "께,", "님께 딱" 등 이름 없이 조사만 있는 패턴 수정
            name_missing_patterns = [
                (r'\s+의\s+(?:선택|피부|알뜰)', f' {customer_name}님의 '),  # " 의 선택" → "OO님의 선택"
                (r'\s+께,', f' {customer_name}님,'),  # " 께," → "OO님,"
                (r'\s+께\s+', f' {customer_name}님께 '),  # " 께 " → "OO님께 "
                (r'(?<![가-힣])님께\s+딱', f'{customer_name}님께 딱'),  # "님께 딱" → "OO님께 딱"
                (r',\s+이번', f'. {customer_name}님, 이번'),  # ", 이번" → ". OO님, 이번"
            ]
            for pattern, replacement in name_missing_patterns:
                body = re.sub(pattern, replacement, body)

            # ========== 어색한 표현 수정 ==========
            awkward_fixes = [
                # 가격/기간 플레이스홀더 제거
                (r'\s*\(\+\d+일\)', ''),  # "(+6일)" 제거
                (r'\s*\(\d{1,3}(,\d{3})*원\)', ''),  # "(280,000원)" 제거
                (r'\s*\(\+\d+%\s*할인\)', ''),  # "(+10% 할인)" 제거
                # 상투적/어색한 마무리 제거
                (r'감사해요,?\s*[가-힣]+님\.?', ''),  # "감사해요, OO님." 제거
                (r'오늘도\s*당신의\s*아름다움을\s*응원합니다\.?', ''),  # 상투적 마무리
                (r'오늘도\s*당신의\s*아름다움을\s*응원해요\.?', ''),
                # 말투 통일 (ㅂ니다/이죠/답니다 → 해요/예요)
                (r'효과적예요', '효과적이에요'),
                (r'될\s*것예요', '될 거예요'),
                (r'있을\s*것예요', '있을 거예요'),
                (r'경험하실\s*수\s*있습니다', '경험해보세요'),
                (r'전합니다', '전해요'),
                (r'부여해\s*준답니다', '부여해줘요'),
                (r'준답니다', '줘요'),
                (r'이죠', '이에요'),
                (r'거든요', '거예요'),
                (r'있답니다', '있어요'),
                (r'해준답니다', '해줘요'),
                # 반복/불필요한 표현
                (r'지금\s*바로\s*장바구니에\s*담아보세요!\s*망설이는\s*순간이\s*기회를\s*잃는\s*순간이\s*될\s*수\s*있어요\.', '지금 바로 장바구니에 담아보세요!'),
            ]
            for pattern, replacement in awkward_fixes:
                body = re.sub(pattern, replacement, body)
                title = re.sub(pattern, replacement, title)

            # ========== 이름 연속 반복 제거 ==========
            # "서수진님. 서수진님," → "서수진님,"
            name_pattern = f'{customer_name}님'
            body = re.sub(rf'{re.escape(name_pattern)}[.\s]+{re.escape(name_pattern)}', name_pattern, body)

            # 이름이 5번 이상이면 중간 것들 제거 (첫 2번 + 마지막 1번만 유지)
            name_count = body.count(name_pattern)
            if name_count > 4:
                parts = body.split(name_pattern)
                if len(parts) > 5:
                    # 첫 2번 + 마지막 1번만 유지
                    new_body = parts[0] + name_pattern + parts[1] + name_pattern
                    new_body += ''.join(parts[2:-1])
                    new_body += name_pattern + parts[-1]
                    body = new_body

            # 최종 검증
            validation = self._validate_message(title, body, customer_name)

            # 실행 시간 기록
            from datetime import datetime
            now = datetime.now()
            timestamp = now.strftime("%m/%d %H:%M")

            # 검증 결과 로깅
            if validation['valid']:
                print(f"[LOG] {timestamp} | 모델: {self.model} | 성공 | {validation['stats']['body_len']}자")
            else:
                print(f"[LOG] {timestamp} | 모델: {self.model} | 검증실패: {', '.join(validation['issues'])}")

            # 최종 결과 (디버그 정보 + 비용 + 검증 포함)
            result = {
                "title": title,
                "body": body,
                "title_over": len(title) > 40,
                "body_over": len(body) > 350,
                "validation": validation,
                "debug_info": {
                    "original_len": original_len,
                    "final_len": len(body),
                    "extended": extended,
                    "model": self.model,
                    "provider": self.provider,
                    "timestamp": timestamp,
                    "validation_passed": validation['valid'],
                    "validation_issues": validation['issues'],
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
