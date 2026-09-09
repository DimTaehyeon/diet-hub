# AI 학습 파이프라인 (P2, EfficientNet-B0 전이학습)

## 1. 데이터 준비
```
ai/datasets/train/김치찌개/xxx.jpg
ai/datasets/train/비빔밥/xxx.jpg
ai/datasets/val/김치찌개/xxx.jpg
... 20개 클래스, 클래스당 최소 300장 권장
```
- `data.yaml`의 names 순서 == `../models/classes.txt` 순서 (고정)
- 출처: AI-Hub 한식이미지 / Kaggle Food-101 + 직접 촬영 보충

## 2. 설치 (CPU 기준, 1회)
```powershell
cd ai
pip install -r requirements.txt
```

## 3. 학습
```powershell
cd ai/training
python train.py --epochs 15 --batch 32 --lr 0.001
# 결과: ../models/best.pt, labels.json, training_log.csv
```

## 4. 평가
```powershell
python evaluate.py --weights ../models/best.pt --split val
# 결과: ../models/metrics.json (목표 top1 >= 0.80)
```

## 5. 단건 추론 테스트
```powershell
python predict.py --image 테스트사진.jpg --topk 3
```

## 6. 백엔드 연동 (P3)
`predict(image_path)`를 import해서 사용. `best.pt` 없으면
`[{"label":"직접입력 필요",...}]` 폴백 반환 → 앱에서 수동입력 유도.
