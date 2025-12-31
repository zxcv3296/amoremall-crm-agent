# -*- coding: utf-8 -*-
"""학습 실행 및 로그 파일 저장"""
import sys
import os

# stdout/stderr를 파일로 리디렉션
log_path = os.path.join(os.path.dirname(__file__), "training_log.txt")
sys.stdout = open(log_path, 'w', encoding='utf-8')
sys.stderr = sys.stdout

try:
    print("=" * 60)
    print("ML 학습 시작")
    print("=" * 60)

    # sklearn 확인
    try:
        import sklearn
        print(f"sklearn version: {sklearn.__version__}")
    except ImportError as e:
        print(f"sklearn 설치 필요: {e}")
        print("pip install scikit-learn 실행 후 다시 시도하세요")
        sys.exit(1)

    # numpy 확인
    import numpy as np
    print(f"numpy version: {np.__version__}")

    # 경로 설정
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, r'c:\Users\MSI\AISystem-2402')

    # 데이터 로드 테스트
    print("\n데이터 로드 테스트...")
    from ml_personas import ml_personas
    print(f"ml_personas: {len(ml_personas)}개")

    from ml_answer_key import ML_ANSWER_KEY
    print(f"ML_ANSWER_KEY: {len(ML_ANSWER_KEY)}개")

    # 학습 실행
    print("\n학습 시작...")
    from ml_trainer import PurposeModelTrainer

    trainer = PurposeModelTrainer()
    result = trainer.train(n_estimators=100, max_depth=8)

    print("\n" + "=" * 60)
    print("학습 완료!")
    print(f"CV 정확도: {result['cv_accuracy']*100:.1f}%")
    print("=" * 60)

    # 평가
    trainer.evaluate_on_training_data()

except Exception as e:
    import traceback
    print(f"\n오류 발생: {e}")
    traceback.print_exc()

finally:
    sys.stdout.close()
