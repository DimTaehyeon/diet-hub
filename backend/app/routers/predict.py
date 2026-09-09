import os
import sys
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from ..schemas import ok

router = APIRouter(prefix="/predict", tags=["predict"])

ROOT = Path(__file__).resolve().parents[3]  # .../인공지능
UPLOAD_DIR = ROOT / "backend" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# 기본 best.pt. 미니 테스트時は MODEL_WEIGHTS=../models/mini.pt + DIET_CLASSES=models/classes_mini.txt
BEST_PT = ROOT / "ai" / "models" / "best.pt"


def weights_path() -> str:
    return os.environ.get("MODEL_WEIGHTS", "../models/best.pt")


def model_file_exists() -> bool:
    w = weights_path()
    p = Path(w)
    base = ROOT / "ai" / "training"
    return (p if p.is_absolute() else base / w).exists()

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_BYTES = 10 * 1024 * 1024


def run_inference(saved_path: str):
    """ai/training/predict.py 재사용. torch/모델 없으면 폴백."""
    try:
        training_dir = str(ROOT / "ai" / "training")
        if training_dir not in sys.path:
            sys.path.insert(0, training_dir)
        from predict import predict as ai_predict  # noqa: E402
        return ai_predict(saved_path, weights=weights_path(), topk=3)
    except Exception as e:
        return [{"label": "직접입력 필요", "confidence": 0.0, "kcal": 0,
                 "reason": f"추론 실패: {str(e)[:200]}"}]


@router.post("")
async def predict_image(request: Request, image: UploadFile = File(...)):
    ext = Path(image.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"이미지 확장자만 가능: {sorted(ALLOWED_EXT)}")
    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="10MB 이하 이미지만 업로드하세요.")

    image_id = f"{uuid.uuid4().hex}{ext}"
    saved = UPLOAD_DIR / image_id
    saved.write_bytes(raw)

    preds = run_inference(str(saved))
    top_conf = float(preds[0].get("confidence", 0.0)) if preds else 0.0
    need_manual = (top_conf < 0.5) or (preds and preds[0].get("label") == "직접입력 필요")

    return ok({
        "predictions": preds,
        "image_id": image_id,
        "image_path": f"uploads/{image_id}",
        "need_manual_input": need_manual,
        "model_loaded": getattr(request.app.state, "model_loaded", False),
    })
