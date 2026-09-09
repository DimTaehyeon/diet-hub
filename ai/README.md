# AI (직접 학습 모델)

- `training/` : dataset.py, train.py, evaluate.py, predict.py, data.yaml, calories.csv
- `models/` : best.pt, classes.txt, labels.json, metrics.json (학습 후 생성)
- `datasets/` : 직접 생성 (git 제외, 구조는 training/README 참고)
- `raw/` : 크롤링 원본 (git 제외, review.py 검수 전 보관)
- `tools/` : crawl.py (수집), review.py (O/X 검수)
- `requirements.txt` : torch CPU + torchvision

## 수집→검수→학습 한 번에
```powershell
cd ai/tools
python crawl.py --menu 탕수육 --num 120   # Bing에서 수집
python review.py --menu 탕수육            # O=채택 X=버림
cd ..
python check_dataset.py                   # 준비도 확인
```
