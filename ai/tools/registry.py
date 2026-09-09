"""클래스 레지스트리: 5곳(classes.txt/data.yaml/calories.csv/폴더/백엔드 seed) 동기화.
- GUI(studio.py)와 단위테스트가 함께 사용. base 경로 주입으로 테스트 가능.
"""
import csv
import re
import shutil
from pathlib import Path

EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _p(base: Path, *parts) -> Path:
    return base.joinpath(*parts)


def load_classes(base: Path) -> list:
    p = _p(base, "models", "classes.txt")
    if not p.exists():
        return []
    return [l.strip() for l in p.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.strip().startswith("#")]


def _write_data_yaml(base: Path, classes: list):
    """names 블록만 번호 매겨 재생성, 나머지 주석/설정은 보존."""
    p = _p(base, "training", "data.yaml")
    lines = p.read_text(encoding="utf-8").splitlines()
    out, i, in_names = [], 0, False
    while i < len(lines):
        if re.match(r"^names:\s*$", lines[i]):
            in_names = True
            out.append(lines[i])
            i += 1
            continue
        if in_names and re.match(r"^\s+\d+:\s*\S+", lines[i]):
            i += 1
            continue
        if in_names and lines[i] and not lines[i].startswith(" ") and not lines[i].startswith("#"):
            in_names = False
        out.append(lines[i])
        i += 1
    # names: 바로 뒤에 번호 블록 삽입
    idx = out.index("names:")
    block = [f"  {n}: {c}" for n, c in enumerate(classes)]
    out[idx + 1:idx + 1] = block
    p.write_text("\n".join(out) + "\n", encoding="utf-8")


def _sync_calories(base: Path, classes: list, kcal: dict | None = None,
                   cats: dict | None = None):
    """classes 순서대로 calories.csv 재작성. 신규는 kcal/cats에서, 없으면 0/기타."""
    kcal, cats = kcal or {}, cats or {}
    p = _p(base, "training", "calories.csv")
    old = {}
    if p.exists():
        with open(p, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                old[r["name_ko"]] = (r.get("category", ""), r.get("kcal_per_serving", "0"))
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name_ko", "category", "kcal_per_serving"])
        for c in classes:
            if c in (kcal or {}):
                w.writerow([c, cats.get(c, "기타"), kcal[c]])
            elif c in old:
                w.writerow([c, old[c][0], old[c][1]])
            else:
                w.writerow([c, "기타", 0])


def _ensure_folders(base: Path, classes: list):
    for c in classes:
        (_p(base, "datasets", "train", c)).mkdir(parents=True, exist_ok=True)
        (_p(base, "datasets", "val", c)).mkdir(parents=True, exist_ok=True)


def _patch_backend_seed(base: Path, name: str, cat: str, kcal_val: int):
    """backend SEED_FOODS에 신규 메뉴 추가 (중복이면 스킵). repo 루트 기준."""
    seed = base.parent / "backend" / "app" / "main.py"
    if not seed.exists():
        return False
    t = seed.read_text(encoding="utf-8")
    if f'("{name}"' in t:
        return False
    m = re.search(r"SEED_FOODS\s*=\s*\[", t)
    if not m:
        return False
    close = t.find("\n]", m.end())
    if close < 0:
        return False
    ins = f',\n    ("{name}", "{cat}", {kcal_val})'
    seed.write_text(t[:close] + ins + t[close:], encoding="utf-8")
    return True


def save_all(base: Path, classes: list, kcal: dict | None = None,
             cats: dict | None = None):
    _p(base, "models", "classes.txt").write_text("\n".join(classes) + "\n", encoding="utf-8")
    _write_data_yaml(base, classes)
    _sync_calories(base, classes, kcal, cats)
    _ensure_folders(base, classes)


def add_class(base: Path, name: str, cat: str, kcal_val: int) -> tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "이름이 비어 있습니다."
    classes = load_classes(base)
    if name in classes:
        return False, "이미 있는 메뉴입니다."
    classes.append(name)
    save_all(base, classes, {name: kcal_val}, {name: cat})
    synced = _patch_backend_seed(base, name, cat, kcal_val)
    msg = "추가됨" + (" (백엔드 seed 반영)" if synced else " (백엔드는 수동 추가 필요)")
    return True, msg


def delete_class(base: Path, name: str) -> tuple[bool, str]:
    classes = load_classes(base)
    if name not in classes:
        return False, "없는 메뉴입니다."
    classes.remove(name)
    save_all(base, classes)
    # 폴더·백엔드 seed는 보존 (기록/파일 유실 방지)
    return True, "등록 해제됨 (폴더·백엔드 기록은 보존)"


def counts(base: Path) -> dict:
    """{클래스: {train, val, raw}}"""
    out = {}
    for c in load_classes(base):
        def n(d: Path):
            return len([p for p in d.glob("*") if p.is_file()
                        and p.suffix.lower() in EXT and not p.name.startswith("_")]) if d.is_dir() else 0
        out[c] = {"train": n(_p(base, "datasets", "train", c)),
                  "val": n(_p(base, "datasets", "val", c)),
                  "raw": n(_p(base, "raw", c))}
    return out
