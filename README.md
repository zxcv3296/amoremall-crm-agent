# 아모레몰 CRM 메시지 자동 생성 시스템

**RAG + LLM + ML 기반 개인화 마케팅 메시지 자동 생성 Agent**

---

## 프로젝트 개요

고객 페르소나와 브랜드 톤앤매너를 기반으로 개인화된 CRM 마케팅 메시지를 자동으로 생성하는 시스템입니다.

### 주요 기능

- **RAG 기반 상품 추천**: FAISS 벡터 검색으로 페르소나에 맞는 상품 자동 검색
- **LLM 메시지 생성**: Claude/Qwen 모델로 브랜드 톤에 맞는 메시지 작성
- **ML 발신 목적 추천**: RandomForest 기반 최적 발신 목적 자동 추천
- **브랜드 클러스터링**: 29개 브랜드를 3축 분석 기반 7개 클러스터로 분류
- **이탈 예측**: 고객 이탈 확률 계산 및 위험도 분석
- **다중 페르소나 지원**: 21개 고객 페르소나 (테스트용)
- **실시간 UI**: Streamlit 기반 직관적인 웹 인터페이스

---

## 시스템 아키텍처

```
[페르소나 입력] → [ML 발신목적 추천] → [RAG 상품 검색] → [LLM 메시지 생성] → [결과 출력]
                  (RandomForest)        (FAISS)           (Claude/Qwen)
```

---

## 폴더 구조

```
notion/
├── app.py                 # Streamlit 메인 UI
├── config.py              # 환경설정, API 키, 상수 정의
├── README.md
├── requirements.txt
│
├── core/                  # 핵심 로직
│   ├── message_generator.py    # LLM 메시지 생성기
│   ├── rag_engine.py           # FAISS 기반 상품 검색
│   ├── context_builder.py      # 페르소나 → LLM 컨텍스트 변환
│   ├── churn_calculator.py     # 이탈 확률 계산
│   ├── customer_analytics.py   # 고객 세그먼트 분석
│   └── validators.py           # 입력값 검증
│
├── ml/                    # ML 모델
│   ├── ml_classifier.py        # RandomForest 분류기
│   ├── purpose_recommender.py  # 발신목적 추천 (ML 기반)
│   ├── ml_trainer.py           # 모델 학습기
│   ├── simple_train.py         # 간단 학습 스크립트
│   ├── ml_answer_key.py        # 100개 학습 데이터 라벨
│   ├── purpose_model.pkl       # 학습된 RF 모델
│   ├── compare_models.py       # ML vs Rule 비교
│   ├── quick_compare.py        # 빠른 비교
│   └── train_and_log.py        # 학습 로깅
│
├── analysis/              # 브랜드 분석 (3축 클러스터링)
│   ├── analyze_keywords.py     # 키워드 빈도 분석
│   ├── analyze_price.py        # 가격 데이터 분석
│   ├── analyze_brand.py        # 주관적 브랜드 분석
│   ├── combine_analysis.py     # 3가지 분석 종합 + K-means
│   ├── visualize_brand_matrix.py  # 브랜드 매트릭스 시각화
│   ├── brand_cluster_map.png   # 7개 클러스터 맵
│   ├── matrix_mass_tech.png    # Mass/Premium × 기술/감성
│   ├── matrix_mass_necessity.png  # Mass/Premium × 필수재/사치재
│   └── matrix_necessity_tech.png  # 필수재/사치재 × 기술/감성
│
├── crawlers/              # 데이터 크롤링
│   ├── crawler_amore_v3.py     # 아모레몰 상품 크롤러
│   ├── crawler_review.py       # 아모레몰 리뷰 크롤러
│   └── amore_brands.py         # 30개 브랜드 목록 및 URL
│
├── data/                  # 데이터 파일
│   ├── personas.py             # 21개 테스트 페르소나
│   ├── personas_full.py        # 확장 페르소나 + 상품 데이터
│   ├── answer_key.py           # 21개 테스트 데이터 라벨
│   ├── enrich_products.py      # 상품 데이터 보강
│   ├── crawled_products.json   # 크롤링된 상품 (1,572개)
│   ├── crawled_reviews.json    # 크롤링된 리뷰 (5,976개)
│   ├── brand_analysis.json     # 주관적 분석 결과
│   ├── keyword_analysis.json   # 키워드 빈도 분석 결과
│   ├── price_analysis.json     # 가격 분석 결과
│   └── combined_analysis.json  # 종합 분석 + 클러스터 결과
│
└── docs/                  # 문서
    ├── llm_token_structure.md
    └── purpose_recommendation_comparison.md
```

---

## 브랜드 클러스터링

### 3축 분석 방법론

| 축 | 가중치 | 설명 |
|---|--------|------|
| **Mass/Premium** | 가격 50% + 키워드 30% + 주관 20% | 대중 ↔ 프리미엄 |
| **필수재/사치재** | 키워드 50% + 주관 50% | 생필품 ↔ 힐링/기분전환 |
| **기술/감성** | 키워드 60% + 주관 40% | 기능성 ↔ 감성/디자인 |

### 7개 클러스터 결과

| 클러스터 | 특징 | 브랜드 |
|---------|------|--------|
| **프리미엄 기능** | 고가 + 기술 중심 | 메이크온 |
| **프리미엄 밸런스** | 고가 + 균형 | 설화수, 헤라, 아모레퍼시픽, 에이피뷰티, 홀리추얼 |
| **중가 라이프스타일** | 힐링/감성 | 오설록, 롱테이크, 퍼즐우드 |
| **중가 필수케어** | 더마코스메틱 | 아이오페, 에스트라 |
| **대중 감성** | 저가 + 감성 | 에뛰드, 에스쁘아, 해피바스, 앞바다즈, 아모레성수 |
| **대중 밸런스** | 저가 + 균형 | 라네즈, 이니스프리, 마몽드, 한율, 프리메라 등 9개 |
| **대중 필수케어** | 저가 + 필수품 | 메디안, 일리윤, 라보에이치, 아모레베이직 |

---

## ML 발신 목적 추천

### 6가지 발신 목적

| ID | 발신 목적 | 설명 |
|----|----------|------|
| `promotion` | 프로모션 | 할인, 적립금, 쿠폰 등 혜택 안내 |
| `new_product` | 신제품 안내 | 새로 출시된 제품 소개 |
| `best_curation` | 베스트 큐레이션 | 인기 상품, 브랜드 베스트 추천 |
| `repurchase` | 재구매 유도 | 구매 주기 도래 고객 재구매 유도 |
| `churn_prevention` | 휴면 방지 | 이탈 위험 고객 재활성화 |
| `seasonal_gift` | 선물/시즌 | 명절, 기념일 선물 구매 유도 |

### 성능 비교

| 지표 | Rule-Based | RandomForest |
|------|------------|--------------|
| **1순위 정확도** | 61.9% | **90.5%** |
| **평균 예측 시간** | **0.003ms** | 4.6ms |

---

## 설치 및 실행

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
# .streamlit/secrets.toml
ANTHROPIC_API_KEY = "your-key"
HF_API_KEY = "your-key"
```

### 3. 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| **UI** | Streamlit |
| **RAG** | LangChain + FAISS |
| **LLM** | Claude API / Qwen2.5-7B (HuggingFace) |
| **ML** | scikit-learn (RandomForest) |
| **임베딩** | sentence-transformers (로컬) |
| **크롤링** | Selenium + BeautifulSoup |
| **시각화** | Matplotlib |
| **언어** | Python 3.10+ |

---

## 데이터 수집 현황

| 항목 | 수량 |
|------|------|
| 브랜드 | 30개 (뷔 제외 29개 분석) |
| 상품 | 1,572개 |
| 리뷰 | 5,976개 |
| 학습 페르소나 | 100개 |
| 테스트 페르소나 | 21개 |
