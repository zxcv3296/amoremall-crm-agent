# -*- coding: utf-8 -*-
"""Ollama CRM 메시지 생성 테스트"""

from core.message_generator import MessageGenerator

# Ollama 모델로 테스트
generator = MessageGenerator(model='qwen2.5:7b', temperature=0.7)

print('=== Ollama Qwen 2.5 7B CRM Test ===')
print('Model:', generator.model)
print('Provider:', generator.provider)
print('API URL:', generator.api_url)
print('LLM Ready:', generator.llm)
print()

# 테스트 페르소나
test_persona = {
    'name': '김서연',
    'display_name': '김서연(28세)',
    'skin_type': '복합성',
    'concerns': ['모공', '피지'],
    'lifestyle': '직장인',
    'shopping_pattern': '가성비'
}

# 테스트 상품
test_products = [{
    'name': '워터뱅크 블루 히알루로닉 세럼',
    'features': ['수분공급', '모공케어'],
    'description': '히알루론산 성분으로 깊은 보습',
    'price': 38000,
    'discount_rate': 30,
    'promotions': ['신규회원 할인']
}]

print('=== Generating CRM Message ===')
result = generator.generate(test_persona, '라네즈', 'promotion', test_products)
print()
print('Title:', result.get('title'))
print()
print('Body:', result.get('body'))
print()
print('Title len:', len(result.get('title', '')))
print('Body len:', len(result.get('body', '')))
if result.get('debug_info'):
    debug = result['debug_info']
    print('Model:', debug.get('model'))
    print('Cost:', debug.get('cost_krw', 0), 'KRW')
    print('Free:', debug.get('is_free', True))
    if debug.get('error'):
        print('Error:', debug.get('error'))
