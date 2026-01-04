# -*- coding: utf-8 -*-
# rag_engine.py
"""
RAG 기반 상품 검색 엔진 (Phase 1+2 개선 버전)
- Phase 1: 한국어 임베딩 모델 (jhgan/ko-sroberta-multitask)
- Phase 2: 하이브리드 검색 (Vector + BM25)
- 인덱스 캐싱으로 빠른 로딩
"""

# 모델 다운로드 로그 숨기기
import os
import sys

# 상위 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

import logging
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from data.personas_full import products
from data.personas import personas
import re
from collections import Counter
import math
import pickle
import hashlib

# 캐시 디렉토리 (프로젝트 루트의 .cache)
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.cache')
FAISS_INDEX_PATH = os.path.join(CACHE_DIR, 'faiss_index')
BM25_CACHE_PATH = os.path.join(CACHE_DIR, 'bm25_cache.pkl')
DOCS_CACHE_PATH = os.path.join(CACHE_DIR, 'docs_cache.pkl')

# ============================================================
# Phase 2: BM25 키워드 검색 구현
# ============================================================

class BM25:
    """
    BM25 키워드 검색 엔진
    한국어 텍스트에서 키워드 매칭으로 관련 문서 검색
    """

    def __init__(self, k1=1.5, b=0.75):
        """
        BM25 초기화

        Args:
            k1: 단어 빈도 포화 파라미터 (기본: 1.5)
            b: 문서 길이 정규화 파라미터 (기본: 0.75)
        """
        self.k1 = k1
        self.b = b
        self.documents = []
        self.doc_lengths = []
        self.avg_doc_length = 0
        self.doc_freqs = {}  # 각 단어가 몇 개의 문서에 등장하는지
        self.idf = {}  # 역문서빈도
        self.doc_tokens = []  # 각 문서의 토큰 리스트
        self.N = 0  # 전체 문서 수

    def _tokenize(self, text):
        """
        간단한 한국어 토크나이저
        - 공백, 구두점으로 분리
        - 한글/영문/숫자 추출
        """
        # 소문자 변환 및 정규화
        text = text.lower()
        # 한글, 영문, 숫자만 추출 (공백으로 분리)
        tokens = re.findall(r'[가-힣]+|[a-z]+|[0-9]+', text)
        # 1글자 토큰 제거 (노이즈)
        tokens = [t for t in tokens if len(t) > 1]
        return tokens

    def fit(self, documents):
        """
        문서 컬렉션으로 BM25 인덱스 구축

        Args:
            documents: 문서 리스트 (각 문서는 문자열)
        """
        self.documents = documents
        self.N = len(documents)
        self.doc_tokens = []
        self.doc_lengths = []

        # 각 문서 토큰화
        for doc in documents:
            tokens = self._tokenize(doc)
            self.doc_tokens.append(tokens)
            self.doc_lengths.append(len(tokens))

        # 평균 문서 길이
        self.avg_doc_length = sum(self.doc_lengths) / self.N if self.N > 0 else 0

        # 문서 빈도 계산 (각 단어가 몇 개 문서에 등장하는지)
        self.doc_freqs = {}
        for tokens in self.doc_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        # IDF 계산
        self.idf = {}
        for token, df in self.doc_freqs.items():
            # IDF = log((N - df + 0.5) / (df + 0.5) + 1)
            self.idf[token] = math.log((self.N - df + 0.5) / (df + 0.5) + 1)

    def get_scores(self, query):
        """
        쿼리에 대한 각 문서의 BM25 점수 계산

        Args:
            query: 검색 쿼리 문자열

        Returns:
            list: 각 문서의 BM25 점수
        """
        query_tokens = self._tokenize(query)
        scores = []

        for i, doc_tokens in enumerate(self.doc_tokens):
            score = 0
            doc_len = self.doc_lengths[i]

            # 문서 내 각 토큰의 빈도
            token_counts = Counter(doc_tokens)

            for token in query_tokens:
                if token not in self.idf:
                    continue

                # 해당 토큰의 문서 내 빈도
                tf = token_counts.get(token, 0)

                # BM25 공식
                idf = self.idf[token]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)

                score += idf * (numerator / denominator) if denominator > 0 else 0

            scores.append(score)

        return scores

    def search(self, query, k=5):
        """
        쿼리로 상위 k개 문서 검색

        Args:
            query: 검색 쿼리
            k: 반환할 문서 수

        Returns:
            list: (문서 인덱스, 점수) 튜플 리스트
        """
        scores = self.get_scores(query)
        # 점수 순으로 정렬
        scored_docs = [(i, score) for i, score in enumerate(scores)]
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return scored_docs[:k]


# ============================================================
# Phase 1+2: 하이브리드 RAG 엔진
# ============================================================

class ProductRAG:
    """
    상품 검색을 위한 하이브리드 RAG 엔진
    - Phase 1: 한국어 임베딩 (jhgan/ko-sroberta-multitask)
    - Phase 2: 하이브리드 검색 (Vector + BM25)
    - FAISS를 사용한 벡터 검색
    - BM25를 사용한 키워드 검색
    - 두 검색 결과를 융합하여 최종 순위 결정
    """

    def __init__(self, model_name="jhgan/ko-sroberta-multitask", vector_weight=0.6, bm25_weight=0.4):
        """
        하이브리드 RAG 엔진 초기화

        Args:
            model_name: 한국어 임베딩 모델 (기본: jhgan/ko-sroberta-multitask)
            vector_weight: 벡터 검색 가중치 (기본: 0.6)
            bm25_weight: BM25 검색 가중치 (기본: 0.4)
        """
        self.model_name = model_name

        # Phase 1: 한국어 임베딩 모델 (한국어 특화!)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={
                'device': 'cpu',
                'trust_remote_code': True
            },
            encode_kwargs={
                'normalize_embeddings': True,
                'batch_size': 32
            }
        )

        # 하이브리드 검색 가중치
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight

        # 검색 엔진들
        self.vectorstore = None
        self.bm25 = None
        self.documents = []  # 원본 문서 저장

        self._load_or_build_indexes()

    def _get_data_hash(self):
        """상품 데이터의 해시값 계산 (캐시 유효성 검사용)"""
        data_str = str([(p['id'], p['name'], p['brand'], p.get('price', 0)) for p in products])
        return hashlib.md5(data_str.encode()).hexdigest()[:16]

    def _load_or_build_indexes(self):
        """캐시된 인덱스 로드 또는 새로 생성"""
        os.makedirs(CACHE_DIR, exist_ok=True)

        current_hash = self._get_data_hash()
        hash_file = os.path.join(CACHE_DIR, 'data_hash.txt')

        # 캐시 유효성 확인
        cache_valid = False
        if os.path.exists(hash_file):
            with open(hash_file, 'r') as f:
                saved_hash = f.read().strip()
            cache_valid = (saved_hash == current_hash)

        # 캐시가 유효하고 모든 파일이 있으면 로드
        if cache_valid and os.path.exists(FAISS_INDEX_PATH) and os.path.exists(BM25_CACHE_PATH):
            try:
                # FAISS 인덱스 로드
                self.vectorstore = FAISS.load_local(
                    FAISS_INDEX_PATH,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )

                # BM25 로드
                with open(BM25_CACHE_PATH, 'rb') as f:
                    self.bm25 = pickle.load(f)

                # Documents 로드
                with open(DOCS_CACHE_PATH, 'rb') as f:
                    self.documents = pickle.load(f)

                print(f"[RAG] 캐시 로드 성공: {len(self.documents)}개 문서")
                return  # 캐시 로드 성공
            except Exception as e:
                print(f"[RAG] 캐시 로드 실패, 새로 빌드합니다: {str(e)[:100]}")

        # 캐시가 없거나 무효하면 새로 빌드
        self._build_indexes()

        # 캐시 저장
        try:
            self.vectorstore.save_local(FAISS_INDEX_PATH)

            with open(BM25_CACHE_PATH, 'wb') as f:
                pickle.dump(self.bm25, f)

            with open(DOCS_CACHE_PATH, 'wb') as f:
                pickle.dump(self.documents, f)

            with open(hash_file, 'w') as f:
                f.write(current_hash)
            print(f"[RAG] 캐시 저장 완료: {CACHE_DIR}")
        except Exception as e:
            print(f"[RAG] 캐시 저장 실패 (무시): {str(e)[:50]}")

    def _build_indexes(self):
        """
        상품 데이터를 벡터스토어와 BM25 인덱스로 변환
        """
        documents = []
        doc_texts = []  # BM25용 텍스트

        for p in products:
            # 할인/프로모션 정보 구성
            price_info = f"{p['price']:,}원" if p.get('price') else "가격미정"
            discount_info = ""
            if p.get('discount_rate'):
                discount_info = f" (할인율: {p['discount_rate']}%)"

            promo_info = ""
            if p.get('promotions'):
                promo_info = f"\n            프로모션: {', '.join(p['promotions'])}"

            # 신상품 여부
            is_new = p.get('is_new', False)
            new_info = "\n            신상품: 예" if is_new else ""

            # 상품 정보를 자연어로 구조화 (할인/프로모션/신상품 포함)
            content = f"""
            상품명: {p['name']}
            브랜드: {p['brand']}
            카테고리: {p['category']}
            특징: {', '.join(p['features'])}
            적합피부: {', '.join(p['target_skin'])}
            설명: {p['description']}
            가격: {price_info}{discount_info}{promo_info}{new_info}
            """

            # Document 객체 생성 (메타데이터 포함)
            doc = Document(
                page_content=content,
                metadata={
                    "product_id": p['id'],
                    "brand": p['brand'],
                    "category": p['category'],
                    "price": p.get('price', 0),
                    "discount_rate": p.get('discount_rate', 0),
                    "promotions": p.get('promotions', []),
                    "is_new": is_new
                }
            )
            documents.append(doc)
            doc_texts.append(content)

        self.documents = documents

        # Phase 1: FAISS 벡터스토어 생성 (한국어 임베딩)
        self.vectorstore = FAISS.from_documents(documents, self.embeddings)

        # Phase 2: BM25 인덱스 생성
        self.bm25 = BM25()
        self.bm25.fit(doc_texts)

    def _hybrid_search(self, query, k=10):
        """
        하이브리드 검색: Vector + BM25 결합

        Args:
            query: 검색 쿼리
            k: 반환할 문서 수

        Returns:
            list: (Document, 최종점수) 튜플 리스트
        """
        # 1. 벡터 검색 (with scores)
        vector_results = self.vectorstore.similarity_search_with_score(query, k=len(products))

        # 2. BM25 검색
        bm25_scores = self.bm25.get_scores(query)

        # 3. 점수 정규화 및 융합
        # 벡터 점수: 거리 기반이므로 작을수록 좋음 → 역수로 변환
        vector_scores_dict = {}
        max_vector_dist = max(score for _, score in vector_results) if vector_results else 1
        for doc, dist in vector_results:
            product_id = doc.metadata['product_id']
            # 거리를 유사도로 변환 (0~1 범위)
            similarity = 1 - (dist / (max_vector_dist + 1e-6))
            vector_scores_dict[product_id] = similarity

        # BM25 점수 정규화
        bm25_scores_dict = {}
        max_bm25 = max(bm25_scores) if bm25_scores and max(bm25_scores) > 0 else 1
        for i, score in enumerate(bm25_scores):
            product_id = self.documents[i].metadata['product_id']
            bm25_scores_dict[product_id] = score / max_bm25 if max_bm25 > 0 else 0

        # 4. 최종 점수 계산 (가중 평균)
        final_scores = {}
        all_product_ids = set(vector_scores_dict.keys()) | set(bm25_scores_dict.keys())

        for pid in all_product_ids:
            v_score = vector_scores_dict.get(pid, 0)
            b_score = bm25_scores_dict.get(pid, 0)
            final_scores[pid] = self.vector_weight * v_score + self.bm25_weight * b_score

        # 5. 점수순 정렬
        sorted_pids = sorted(final_scores.keys(), key=lambda x: final_scores[x], reverse=True)

        # 6. Document 객체와 함께 반환
        result = []
        for pid in sorted_pids[:k]:
            doc = next((d for d in self.documents if d.metadata['product_id'] == pid), None)
            if doc:
                result.append((doc, final_scores[pid]))

        return result

    def _get_price_range(self, persona):
        """
        페르소나의 쇼핑 패턴에 맞는 가격 범위 반환

        Args:
            persona: 페르소나 딕셔너리

        Returns:
            tuple: (min_price, max_price) 또는 None (제한 없음)
        """
        shopping_pattern = persona.get('shopping_pattern', '')

        # 가성비/저렴 키워드 → 저가 상품
        if '가성비' in shopping_pattern or '저렴' in shopping_pattern:
            return (0, 50000)

        # 프리미엄 키워드 → 고가 상품
        if '프리미엄' in shopping_pattern:
            return (50000, None)

        # 그 외 → 제한 없음
        return None

    def retrieve_products(self, persona, brand, purpose=None, k=3):
        """
        페르소나와 브랜드에 맞는 상품 검색 (하이브리드 검색 + 필터링)

        Args:
            persona: 페르소나 딕셔너리
            brand: 브랜드명 (설화수/라네즈/이니스프리)
            purpose: 발신 목적 (맞춤 제품 추천/재구매 유도/특가/신제품)
            k: 검색할 상품 개수 (기본값: 3)

        Returns:
            list: 추천 상품 리스트
        """
        # 페르소나 정보를 더 구체적인 쿼리로 변환
        query = f"""
        브랜드: {brand}
        피부타입: {persona['skin_type']}
        피부고민: {', '.join(persona['concerns'])}
        관심카테고리: {', '.join(persona['interests'])}
        나이대: {persona['age']}세
        선호패턴: {persona['shopping_pattern']}
        라이프스타일: {persona['lifestyle']}
        """

        # Phase 2: 하이브리드 검색 사용!
        hybrid_results = self._hybrid_search(query, k=len(products))

        # 브랜드로 먼저 필터링 (가장 중요!)
        product_ids = [doc.metadata['product_id'] for doc, score in hybrid_results
                      if doc.metadata.get('brand') == brand]

        candidate_products = [p for p in products if p['id'] in product_ids]

        # 브랜드 제품이 없으면 해당 브랜드 전체 상품 사용
        if not candidate_products:
            candidate_products = [p for p in products if p['brand'] == brand]

        # 가격대 필터링 (페르소나 쇼핑 패턴 기반)
        price_range = self._get_price_range(persona)
        if price_range:
            min_price, max_price = price_range
            price_filtered = []
            for p in candidate_products:
                if min_price <= p['price']:
                    if max_price is None or p['price'] <= max_price:
                        price_filtered.append(p)

            # 가격 필터링 결과가 있으면 사용, 없으면 원본 유지
            if price_filtered:
                candidate_products = price_filtered

        # 페르소나 관심사/고민과 매칭되는 상품 필터링
        filtered = []

        for p in candidate_products:
            score = 0

            # 1. 카테고리 매칭 (관심제품과 일치)
            for interest in persona['interests']:
                if interest.lower() in p['category'].lower() or interest.lower() in p['name'].lower():
                    score += 3

            # 2. 피부고민 매칭 (features에 고민 키워드 포함)
            for concern in persona['concerns']:
                features_text = ' '.join(p['features']).lower()
                if concern.lower() in features_text:
                    score += 2

            # 3. 피부타입 매칭
            if persona['skin_type'] in p['target_skin'] or '모든피부' in p['target_skin']:
                score += 1

            # 점수가 있는 상품만 추가
            if score > 0:
                filtered.append((p, score))

        # 점수 순으로 정렬
        filtered.sort(key=lambda x: x[1], reverse=True)

        # 목적별 다양화 전략 (영문 ID 기반)
        result = []

        if purpose == "repurchase" or (purpose and "재구매" in purpose):
            # 재구매 유도: 다양한 카테고리 조합 (크로스셀링)
            categories_used = set()
            for p, score in filtered:
                category = p.get('category', '')
                if category not in categories_used:
                    result.append(p)
                    categories_used.add(category)
                    if len(result) >= k:
                        break

        elif purpose == "promotion" or (purpose and ("특가" in purpose or "프로모션" in purpose)):
            # 프로모션: 할인율 높은 상품 우선
            discounted = [(p, score) for p, score in filtered if p.get('discount_rate', 0) > 0]
            discounted.sort(key=lambda x: x[0].get('discount_rate', 0), reverse=True)

            if discounted:
                result = [p for p, _ in discounted[:k]]
            else:
                # 할인 상품 없으면 가격대 다양하게
                high_price = [p for p, _ in filtered if p['price'] >= 80000]
                mid_price = [p for p, _ in filtered if 40000 <= p['price'] < 80000]
                low_price = [p for p, _ in filtered if p['price'] < 40000]

                if high_price:
                    result.append(high_price[0])
                if mid_price and len(result) < k:
                    result.append(mid_price[0])
                if low_price and len(result) < k:
                    result.append(low_price[0])

        elif purpose == "new_product" or (purpose and "신제품" in purpose):
            # 신제품 안내: is_new=True인 상품 우선
            # 1. 먼저 필터링된 결과에서 신제품 찾기
            new_products = [p for p, _ in filtered if p.get('is_new')]
            if new_products:
                result = new_products[:k]
            else:
                # 2. 해당 브랜드 전체에서 신제품 찾기
                brand_new = [p for p in candidate_products if p.get('is_new')]
                if brand_new:
                    result = brand_new[:k]
                else:
                    # 3. 신제품 없음 → 최신/프리미엄 제품 (높은 가격순)
                    premium_products = sorted(filtered, key=lambda x: x[0]['price'], reverse=True)
                    result = [p for p, _ in premium_products[:k]]
                    # 결과에 신제품 없음 플래그 추가 (UI에서 표시용)
                    for p in result:
                        p['_no_new_product_warning'] = True

        elif purpose == "churn_prevention" or (purpose and "휴면" in purpose):
            # 휴면 방지: 인기/베스트 상품 + 할인 상품 조합
            discounted = [(p, score) for p, score in filtered if p.get('discount_rate', 0) > 0]
            discounted.sort(key=lambda x: x[0].get('discount_rate', 0), reverse=True)

            # 할인 상품 1개 + 점수 높은 상품
            if discounted:
                result.append(discounted[0][0])
            for p, _ in filtered:
                if p not in result and len(result) < k:
                    result.append(p)

        elif purpose == "seasonal_gift" or (purpose and ("선물" in purpose or "시즌" in purpose)):
            # 선물/시즌: 세트 상품 우선, 고가 상품
            set_products = [(p, score) for p, score in filtered
                           if '세트' in p.get('name', '') or '기프트' in p.get('name', '')]
            set_products.sort(key=lambda x: x[0]['price'], reverse=True)

            if set_products:
                result = [p for p, _ in set_products[:k]]
            else:
                # 세트 없으면 고가 상품
                premium_products = sorted(filtered, key=lambda x: x[0]['price'], reverse=True)
                result = [p for p, _ in premium_products[:k]]

        elif purpose == "best_curation" or (purpose and "큐레이션" in purpose):
            # 베스트 큐레이션: 점수 높은 순 (기본)
            result = [p for p, _ in filtered[:k]]

        else:
            # 기본 (맞춤 추천): 점수 높은 순
            result = [p for p, _ in filtered[:k]]

        # 필터링 결과가 부족하면 해당 브랜드에서 보충
        if len(result) < k:
            for p in candidate_products:
                if p not in result:
                    result.append(p)
                    if len(result) >= k:
                        break

        # Edge case: 결과가 비어있으면 해당 브랜드의 기본 상품 반환
        if not result:
            brand_products = [p for p in products if p['brand'] == brand]
            if brand_products:
                # 가격순 정렬 (중간 가격대 우선)
                brand_products.sort(key=lambda x: abs(x['price'] - 50000))
                result = brand_products[:k]
            else:
                # 브랜드 상품도 없으면 전체에서 반환 (최후의 수단)
                print(f"[RAG] 경고: '{brand}' 브랜드 상품을 찾을 수 없습니다. 전체 상품에서 선택합니다.")
                result = products[:k]

        return result[:k]

    def search_by_query(self, query_text, k=3):
        """
        자유 텍스트 쿼리로 상품 검색 (하이브리드 검색)

        Args:
            query_text: 검색 쿼리
            k: 검색할 상품 개수

        Returns:
            list: 검색된 상품 리스트
        """
        # 하이브리드 검색 사용
        results = self._hybrid_search(query_text, k=k)
        product_ids = [doc.metadata['product_id'] for doc, _ in results]
        return [p for p in products if p['id'] in product_ids]

    def get_search_info(self):
        """
        검색 엔진 정보 반환 (디버깅/UI용)

        Returns:
            dict: 검색 엔진 설정 정보
        """
        return {
            "embedding_model": "jhgan/ko-sroberta-multitask",
            "search_type": "Hybrid (Vector + BM25)",
            "vector_weight": self.vector_weight,
            "bm25_weight": self.bm25_weight,
            "total_products": len(products),
            "index_status": "Ready" if self.vectorstore and self.bm25 else "Not Ready"
        }


# 테스트 코드
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 RAG 엔진 Phase 1+2 테스트")
    print("   - Phase 1: 한국어 임베딩 (ko-sroberta)")
    print("   - Phase 2: 하이브리드 검색 (Vector + BM25)")
    print("=" * 60)

    # RAG 엔진 초기화
    print("\n⏳ RAG 엔진 초기화 중...")
    rag = ProductRAG()

    # 검색 엔진 정보 출력
    info = rag.get_search_info()
    print(f"\n📊 검색 엔진 설정:")
    print(f"   임베딩 모델: {info['embedding_model']}")
    print(f"   검색 방식: {info['search_type']}")
    print(f"   벡터 가중치: {info['vector_weight']}")
    print(f"   BM25 가중치: {info['bm25_weight']}")
    print(f"   상품 수: {info['total_products']}")
    print(f"   인덱스 상태: {info['index_status']}")

    # 테스트 페르소나
    test_persona = personas[0]  # 민지(25세)

    print(f"\n📌 테스트 페르소나: {test_persona['name']}")
    print(f"   피부타입: {test_persona['skin_type']}")
    print(f"   피부고민: {', '.join(test_persona['concerns'])}")
    print(f"   관심사: {', '.join(test_persona['interests'])}")

    # 각 브랜드별 상품 검색
    for brand in ["설화수", "라네즈", "이니스프리"]:
        print(f"\n🎯 [{brand}] 추천 상품:")
        results = rag.retrieve_products(test_persona, brand=brand, k=2)
        for p in results:
            print(f"   - {p['name']} ({p['price']:,}원)")

    # 자유 쿼리 검색 테스트
    print(f"\n🔍 자유 검색 테스트: '주름 탄력 안티에이징'")
    query_results = rag.search_by_query("주름 탄력 안티에이징", k=3)
    for p in query_results:
        print(f"   - {p['name']} ({p['brand']}, {p['price']:,}원)")
