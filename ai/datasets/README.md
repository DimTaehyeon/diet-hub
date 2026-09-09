# datasets (로컬 전용, git 제외)

사진을 아래 구조에 넣으세요. 폴더명은 절대 바꾸지 마세요
(`classes.txt` 순서와 1:1 대응).

```
datasets/train/김치찌개/xxx.jpg
datasets/train/비빔밥/xxx.jpg
datasets/val/김치찌개/xxx.jpg
```

- 준비도 확인: `cd ai && python check_dataset.py`
- 목표: 클래스당 train 240장+ / val 60장+
- 사진 규칙: 한 사진에 한 메뉴, 224px 이상, 각도·조명 다양하게
