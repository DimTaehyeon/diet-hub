"""검수 도구: python review.py --menu 라면 [--val-ratio 0.2]
- ai/raw/{메뉴}/ 사진을 한 장씩 보여줌. O=채택, X=버림, Q=종료.
- 채택분은 datasets/train|val/{메뉴}/ 로 자동 이동, 버린 건 raw/_reject/ 보관.
- val 비율만큼 앞에서부터 val로 배정 (예: 20%면 채택 1~5번째 중 1장이 val).
"""
import argparse
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def list_images(menu: str):
    d = BASE / "raw" / menu
    return sorted([p for p in d.iterdir()
                   if p.is_file() and p.suffix.lower() in EXT and not p.name.startswith("_")])


def plan_destination(kept_count: int, val_ratio: float) -> str:
    """kept_count번째(1부터) 채택의 행선지. val을 고르게 분산."""
    if val_ratio <= 0:
        return "train"
    period = max(1, round(1 / val_ratio))
    return "val" if kept_count % period == 0 else "train"


def store(kept_path: Path, menu: str, dest: str, seq: int):
    target = BASE / "datasets" / dest / menu
    target.mkdir(parents=True, exist_ok=True)
    name = f"{menu}_{seq:04d}{kept_path.suffix.lower()}"
    shutil.move(str(kept_path), str(target / name))
    return name


def reject(path: Path):
    rej = path.parent / "_reject"
    rej.mkdir(exist_ok=True)
    shutil.move(str(path), str(rej / path.name))


def run_gui(menu: str, val_ratio: float):
    import tkinter as tk
    from PIL import Image, ImageTk

    images = list_images(menu)
    if not images:
        print(f"검수할 사진 없음: ai/raw/{menu}/ (먼저 crawl.py 실행)")
        return

    root = tk.Tk()
    root.title(f"검수: {menu} (O=채택 X=버림 Q=종료)")
    img_label = tk.Label(root)
    img_label.pack()
    info = tk.Label(root, font=("맑은고딕", 14))
    info.pack()
    state = {"i": 0, "kept": 0, "seq": 1, "photo": None}

    def show():
        if state["i"] >= len(images):
            info.config(text=f"완료! 채택 {state['kept']}장")
            root.after(1500, root.destroy)
            return
        p = images[state["i"]]
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((800, 600))
            state["photo"] = ImageTk.PhotoImage(im)
            img_label.config(image=state["photo"])
        except Exception as e:
            info.config(text=f"열기 실패, 건너뜀: {p.name}")
            state["i"] += 1
            root.after(300, show)
            return
        info.config(text=f"[{state['i']+1}/{len(images)}] {p.name}  (채택 {state['kept']})")

    def decide(keep: bool):
        if state["i"] >= len(images):
            return
        p = images[state["i"]]
        if keep:
            state["kept"] += 1
            dest = plan_destination(state["kept"], val_ratio)
            store(p, menu, dest, state["seq"])
            state["seq"] += 1
        else:
            reject(p)
        state["i"] += 1
        show()

    root.bind("o", lambda e: decide(True))
    root.bind("O", lambda e: decide(True))
    root.bind("x", lambda e: decide(False))
    root.bind("X", lambda e: decide(False))
    root.bind("q", lambda e: root.destroy())
    root.bind("Q", lambda e: root.destroy())
    show()
    root.mainloop()
    print(f"[완료] {menu}: 채택 {state['kept']}장 -> datasets/ (val비율 {val_ratio})")
    print("다음: cd .. && python ai/check_dataset.py")


def main():
    ap = argparse.ArgumentParser(description="수집 이미지 검수")
    ap.add_argument("--menu", required=True)
    ap.add_argument("--val-ratio", type=float, default=0.2)
    a = ap.parse_args()
    run_gui(a.menu, a.val_ratio)


if __name__ == "__main__":
    main()
