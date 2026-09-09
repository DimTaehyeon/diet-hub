"""EfficientNet-B0 전이학습 (CPU/GPU 자동)"""
import argparse
import csv
import json
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
from tqdm import tqdm

from dataset import FoodImageDataset, get_transforms


def build_model(num_classes):
    weights = EfficientNet_B0_Weights.DEFAULT
    model = efficientnet_b0(weights=weights)
    in_f = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_f, num_classes)
    return model


def main():
    ap = argparse.ArgumentParser(description="한식 20종 분류 학습")
    ap.add_argument("--datasets", default="../datasets", help="datasets/ 루트 (train/, val/ 포함)")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--img-size", type=int, default=224)
    ap.add_argument("--out", default="../models/best.pt")
    ap.add_argument("--num-workers", type=int, default=0)
    args = ap.parse_args()

    base = Path(__file__).resolve().parent
    ds_root = (base / args.datasets).resolve()
    train_dir, val_dir = ds_root / "train", ds_root / "val"
    out_path = (base / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[device] {device}")

    train_ds = FoodImageDataset(str(train_dir), get_transforms(args.img_size, True))
    val_ds = FoodImageDataset(str(val_dir), get_transforms(args.img_size, False))
    num_classes = len(train_ds.classes)
    print(f"[classes] {num_classes}개: {train_ds.classes}")
    print(f"[data] train {len(train_ds)} / val {len(val_ds)}")

    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True, num_workers=args.num_workers)
    val_loader = DataLoader(val_ds, batch_size=args.batch, num_workers=args.num_workers)

    model = build_model(num_classes).to(device)
    crit = nn.CrossEntropyLoss()
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    sched = torch.optim.lr_scheduler.StepLR(opt, step_size=7, gamma=0.5)

    best_acc, log_rows = 0.0, []
    for epoch in range(1, args.epochs + 1):
        model.train()
        total, correct, run_loss = 0, 0, 0.0
        for x, y in tqdm(train_loader, desc=f"epoch {epoch}/{args.epochs} train"):
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            out = model(x)
            loss = crit(out, y)
            loss.backward()
            opt.step()
            run_loss += loss.item() * len(x)
            correct += (out.argmax(1) == y).sum().item()
            total += len(x)
        sched.step()

        model.eval()
        vt, vc = 0, 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                vc += (model(x).argmax(1) == y).sum().item()
                vt += len(x)
        val_acc = vc / max(vt, 1)
        print(f"[epoch {epoch}] loss={run_loss/max(total,1):.4f} train_acc={correct/max(total,1):.3f} val_acc={val_acc:.3f}")
        log_rows.append([epoch, round(run_loss/max(total,1), 4), round(correct/max(total,1), 4), round(val_acc, 4)])

        torch.save(model.state_dict(), str(out_path.parent / "last.pt"))
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), str(out_path))
            (out_path.parent / "labels.json").write_text(
                json.dumps(train_ds.classes, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  -> best 갱신 ({best_acc:.3f}): {out_path}")

    with open(out_path.parent / "training_log.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["epoch", "loss", "train_acc", "val_acc"], *log_rows])
    print(f"완료. best val_acc={best_acc:.3f} -> {out_path}")


if __name__ == "__main__":
    main()
