"""데이터셋 로더 (torchvision ImageFolder 기반, 한글 클래스명 지원)"""
from pathlib import Path
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms


def get_transforms(img_size=224, train=True):
    if train:
        return transforms.Compose([
            transforms.RandomResizedCrop(img_size, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(20),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


class FoodImageDataset(Dataset):
    """datasets/{split}/{클래스명}/*.jpg 구조를 읽는다."""

    EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

    def __init__(self, root: str, transform=None):
        self.root = Path(root)
        self.transform = transform
        # 클래스 목록: 기본 classes.txt, 미니 학습時は DIET_CLASSES 환경변수로 교체
        # 예: $env:DIET_CLASSES='models/classes_mini.txt'; python train.py --out ../models/mini.pt
        import os
        override = os.environ.get("DIET_CLASSES", "")
        models_dir = Path(__file__).resolve().parent.parent / "models"
        classes_path = (Path(override) if Path(override).is_absolute()
                        else models_dir.parent / override) if override else models_dir / "classes.txt"
        if classes_path.exists():
            self.classes = [l.strip() for l in classes_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        else:
            self.classes = sorted([d.name for d in self.root.iterdir() if d.is_dir()])
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
        self.samples = []
        for cls in self.classes:
            cdir = self.root / cls
            if not cdir.is_dir():
                continue
            for p in cdir.iterdir():
                if p.suffix.lower() in self.EXT:
                    self.samples.append((str(p), self.class_to_idx[cls]))
        if not self.samples:
            raise RuntimeError(f"이미지가 없습니다: {self.root} (구조: {self.root}/김치찌개/xxx.jpg)")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, i):
        path, label = self.samples[i]
        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label
