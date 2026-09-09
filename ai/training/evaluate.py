"""학습된 모델 평가: 정확도 + 클래스별 정확도 -> metrics.json"""
import argparse
import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torchvision.models import efficientnet_b0

from dataset import FoodImageDataset, get_transforms
from train import build_model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default="../models/best.pt")
    ap.add_argument("--datasets", default="../datasets")
    ap.add_argument("--split", default="val", choices=["train", "val"])
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--img-size", type=int, default=224)
    args = ap.parse_args()

    base = Path(__file__).resolve().parent
    w = (base / args.weights).resolve()
    ds_dir = (base / args.datasets).resolve() / args.split
    if not w.exists():
        raise FileNotFoundError(f"가중치 없음: {w} (먼저 train.py 실행)")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    ds = FoodImageDataset(str(ds_dir), get_transforms(args.img_size, False))
    loader = DataLoader(ds, batch_size=args.batch)
    model = build_model(len(ds.classes))
    model.load_state_dict(torch.load(str(w), map_location=device))
    model.to(device).eval()

    total, top1, top3 = 0, 0, 0
    per_cls_ok = [0] * len(ds.classes)
    per_cls_n = [0] * len(ds.classes)
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            out = model(x)
            top1 += (out.argmax(1).cpu() == y).sum().item()
            top3 += sum(y[i].item() in out[i].topk(3).indices.tolist() for i in range(len(y)))
            for i in range(len(y)):
                per_cls_n[y[i]] += 1
                if out[i].argmax().item() == y[i].item():
                    per_cls_ok[y[i]] += 1
            total += len(y)

    metrics = {
        "weights": str(w),
        "split": args.split,
        "n": total,
        "top1_acc": round(top1 / max(total, 1), 4),
        "top3_acc": round(top3 / max(total, 1), 4),
        "per_class_acc": {ds.classes[i]: round(per_cls_ok[i]/max(per_cls_n[i],1), 4) for i in range(len(ds.classes))},
    }
    out = (base / "../models/metrics.json").resolve()
    out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"저장: {out} (목표: top1 >= 0.80)")


if __name__ == "__main__":
    # efficientnet_b0 임포트 유지용 (미사용 경고 방지)
    _ = efficientnet_b0
    main()
