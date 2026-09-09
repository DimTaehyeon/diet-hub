"""검수 도구(갤러리): python review.py --menu 라면 [--val-ratio 0.2]
- ai/raw/{메뉴}/ 사진을 바둑판으로 보여줌. 클릭=선택/해제.
- [선택 저장]을 누르면 선택분만 datasets/train|val/{메뉴}/ 로 이동,
  나머지는 raw/_reject/ 로 이동.
- val 비율만큼 앞에서부터 val로 배정 (예: 20%면 5개 중 1장이 val).
"""
import argparse
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
TILE = 150


def list_images(menu: str):
    d = BASE / "raw" / menu
    if not d.is_dir():
        return []
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


def _next_seq(menu: str) -> int:
    """train/val 기존 번호 다음부터 시작 (덮어쓰기 방지)."""
    mx = 0
    for dest in ("train", "val"):
        d = BASE / "datasets" / dest / menu
        if not d.is_dir():
            continue
        for p in d.iterdir():
            stem = p.stem
            if stem.startswith(f"{menu}_") and stem[len(menu) + 1:].isdigit():
                mx = max(mx, int(stem[len(menu) + 1:]))
    return mx + 1


def save_selection(menu: str, selected: list, val_ratio: float) -> int:
    """선택 리스트를 datasets로 이동. 반환: 저장 장수."""
    seq = _next_seq(menu)
    for p in selected:
        dest = plan_destination(seq, val_ratio)
        store(p, menu, dest, seq)
        seq += 1
    return len(selected)


def run_gui(menu: str, val_ratio: float):
    import tkinter as tk
    from tkinter import messagebox
    from PIL import Image, ImageTk

    images = list_images(menu)
    if not images:
        print(f"검수할 사진 없음: ai/raw/{menu}/ (먼저 crawl.py 실행)")
        return

    root = tk.Tk()
    root.title(f"검수: {menu} (클릭=선택/해제)")
    root.geometry("1000x700")
    selected = [False] * len(images)
    thumbs, labels = [], []

    top = tk.Frame(root)
    top.pack(fill="x", padx=8, pady=6)
    cnt = tk.Label(top, text="", font=("맑은고딕", 13, "bold"))
    cnt.pack(side="left")

    def refresh():
        n = sum(selected)
        cnt.config(text=f"{menu}: {len(images)}장 중 {n}장 선택")

    # 스크롤 그리드
    canvas = tk.Canvas(root)
    scroll = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    grid = tk.Frame(canvas)
    grid.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=grid, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    def on_wheel(e):
        canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")

    canvas.bind_all("<MouseWheel>", on_wheel)

    for i, p in enumerate(images):
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((TILE, TILE))
            ph = ImageTk.PhotoImage(im)
        except Exception:
            continue
        thumbs.append(ph)  # GC 방지
        lb = tk.Label(grid, image=ph, borderwidth=4, relief="flat",
                      width=TILE + 8, height=TILE + 8)
        lb.grid(row=i // 6, column=i % 6, padx=3, pady=3)

        def toggle(e, idx=i, lab=lb):
            selected[idx] = not selected[idx]
            lab.config(relief="solid" if selected[idx] else "flat",
                       highlightbackground="green", highlightthickness=0,
                       borderwidth=4 if selected[idx] else 4,
                       bg="#C8E6C9" if selected[idx] else "SystemButtonFace")
            refresh()

        lb.bind("<Button-1>", toggle)
        labels.append(lb)

    def select_all(v: bool):
        for i in range(len(selected)):
            selected[i] = v
            labels[i].config(relief="solid" if v else "flat",
                             bg="#C8E6C9" if v else "SystemButtonFace")
        refresh()

    def save():
        chosen = [p for p, s in zip(images, selected) if s]
        if not chosen:
            messagebox.showwarning("알림", "선택된 사진이 없습니다.")
            return
        for p, s in zip(images, selected):
            if not s:
                try:
                    reject(p)
                except FileNotFoundError:
                    pass
        n = save_selection(menu, chosen, val_ratio)
        messagebox.showinfo("완료", f"{n}장 저장 -> datasets/")
        root.destroy()
        print(f"[완료] {menu}: 채택 {n}장 -> datasets/ (val비율 {val_ratio})")
        print("다음: cd .. && python check_dataset.py")

    bar = tk.Frame(root)
    bar.pack(fill="x", padx=8, pady=6)
    tk.Button(bar, text="전체선택", command=lambda: select_all(True)).pack(side="left")
    tk.Button(bar, text="전체해제", command=lambda: select_all(False)).pack(side="left", padx=6)
    tk.Button(bar, text="선택 저장", bg="#A5D6A7",
              font=("맑은고딕", 12, "bold"), command=save).pack(side="right")

    refresh()
    root.mainloop()


def main():
    ap = argparse.ArgumentParser(description="수집 이미지 검수(갤러리)")
    ap.add_argument("--menu", required=True)
    ap.add_argument("--val-ratio", type=float, default=0.2)
    a = ap.parse_args()
    run_gui(a.menu, a.val_ratio)


if __name__ == "__main__":
    main()
