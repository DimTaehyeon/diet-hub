"""데이터셋 준비도 검사: python check_dataset.py
- 폴더 구조/파일 수/클래스 일치 여부를 보고하고 학습 가능 여부를 판정.
- torch 불필요 (표준라이브러리만).
"""
import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE = Path(__file__).resolve().parent
DS = BASE / "datasets"
CLASSES_TXT = BASE / "models" / "classes.txt"
CAL_CSV = BASE / "training" / "calories.csv"
EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MIN_TRAIN, MIN_VAL = 240, 60  # 클래스당 권장 최소


def main():
    classes = [l.strip() for l in CLASSES_TXT.read_text(encoding="utf-8").splitlines() if l.strip()]
    cal_names = set()
    if CAL_CSV.exists():
        with open(CAL_CSV, encoding="utf-8") as f:
            cal_names = {r["name_ko"] for r in csv.DictReader(f)}
    print(f"[클래스] {len(classes)}종")
    ok_all, total_tr, total_va = True, 0, 0
    print(f"{'클래스':10s} {'train':>6s} {'val':>5s}  판정")
    for c in classes:
        tr = [p for p in (DS / "train" / c).glob("*") if p.suffix.lower() in EXT] if (DS / "train" / c).is_dir() else []
        va = [p for p in (DS / "val" / c).glob("*") if p.suffix.lower() in EXT] if (DS / "val" / c).is_dir() else []
        total_tr += len(tr)
        total_va += len(va)
        ok = len(tr) >= MIN_TRAIN and len(va) >= MIN_VAL and c in cal_names
        ok_all &= ok
        print(f"{c:10s} {len(tr):>6d} {len(va):>5d}  {'OK' if ok else '부족'}")
    print(f"[합계] train {total_tr} / val {total_va}")
    print(f"[calories.csv 매칭] {'OK' if set(classes) == cal_names else '불일치(확인 필요)'}")
    if ok_all:
        print("결과: 학습 가능 -> python train.py --epochs 15 --batch 32")
    else:
        print(f"결과: 수집 계속 (목표: 클래스당 train {MIN_TRAIN}+ / val {MIN_VAL}+)")


if __name__ == "__main__":
    main()
