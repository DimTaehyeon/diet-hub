"""추론 함수: predict(image_path) -> [{label, confidence, kcal}]
가중치 없으면 '직접입력 필요' 폴백 반환 (P3 백엔드 연동용).
"""
import argparse
import csv
from pathlib import Path

try:
    import torch
    import torch.nn.functional as F
    from PIL import Image
    from torchvision.models import efficientnet_b0
    from dataset import get_transforms
    from train import build_model
    _TORCH_OK = True
except Exception:
    _TORCH_OK = False

BASE = Path(__file__).resolve().parent
MODELS = BASE.parent / "models"

# calories.csv 로드 (backend DB 시드와 동일 20종)
CAL_MAP, CAT_MAP = {}, {}
_cal = BASE / "calories.csv"
if _cal.exists():
    with open(_cal, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            CAL_MAP[row["name_ko"]] = int(row["kcal_per_serving"])
            CAT_MAP[row["name_ko"]] = row.get("category", "")


def _classes():
    p = MODELS / "classes.txt"
    if p.exists():
        return [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    return []


def _load_model(weights: Path, num_classes: int, device: str):
    model = build_model(num_classes)
    model.load_state_dict(torch.load(str(weights), map_location=device))
    model.to(device).eval()
    return model


def predict(image_path: str, weights: str = "../models/best.pt", topk: int = 3):
    """백엔드에서 import해서 사용: from predict import predict"""
    w = (BASE / weights).resolve() if not Path(weights).is_absolute() else Path(weights)
    if (not _TORCH_OK) or (not w.exists()) or (not Path(image_path).exists()):
        return [{"label": "직접입력 필요", "confidence": 0.0, "kcal": 0,
                 "reason": "모델/이미지 없음" if not w.exists() else "torch 미설치"}]
    classes = _classes()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = _load_model(w, len(classes), device)
    tf = get_transforms(224, False)
    img = Image.open(image_path).convert("RGB")
    x = tf(img).unsqueeze(0).to(device)
    with torch.no_grad():
        probs = F.softmax(model(x)[0], dim=0)
    vals, idx = probs.topk(min(topk, len(classes)))
    out = []
    for v, i in zip(vals.tolist(), idx.tolist()):
        name = classes[i]
        out.append({"label": name, "confidence": round(float(v), 4),
                    "kcal": CAL_MAP.get(name, 0), "category": CAT_MAP.get(name, "")})
    # P3 스펙: confidence < 0.5면 직접입력 플래그
    for o in out:
        o["need_manual_input"] = o["confidence"] < 0.5
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--weights", default="../models/best.pt")
    ap.add_argument("--topk", type=int, default=3)
    a = ap.parse_args()
    import json
    print(json.dumps(predict(a.image, a.weights, a.topk), ensure_ascii=False, indent=2))
