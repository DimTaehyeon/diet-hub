"""식단 데이터 스튜디오: python studio.py
- 수집/현황 (병합): 클래스별 train/val/raw 현황 + 행별 수집·검수·삭제 + 클래스 추가
- 검수: 메뉴 선택 후 갤러리 검수 실행
- 수집은 스레드로 병렬 실행 (여러 메뉴 동시 가능)
"""
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import registry as R
from crawl import crawl as do_crawl

TRAIN_OK, VAL_OK = 240, 60


class Studio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("식단 데이터 스튜디오")
        self.geometry("1080x720")
        self.running: dict = {}  # menu -> thread
        self.msgq: queue.Queue = queue.Queue()

        side = tk.Frame(self, width=130)
        side.pack(side="left", fill="y", padx=6, pady=6)
        tk.Button(side, text="수집/현황", font=("맑은고딕", 12, "bold"),
                  command=self.show_collect).pack(fill="x", pady=4)
        tk.Button(side, text="검수", font=("맑은고딕", 12, "bold"),
                  command=self.show_review).pack(fill="x", pady=4)

        self.pages = {}
        self.pages["collect"] = self._page_collect()
        self.pages["review"] = self._page_review()
        self.show_collect()
        self.after(1000, self._poll)

    # ---------- 공통 ----------
    def show_collect(self):
        self.pages["review"].pack_forget()
        self.pages["collect"].pack(side="right", fill="both", expand=True)
        self.refresh_table()

    def show_review(self):
        self.pages["collect"].pack_forget()
        self.pages["review"].pack(side="right", fill="both", expand=True)
        self._reload_review_list()

    def _poll(self):
        """워커 스레드 완료 감시 → 버튼 복구 + 현황 갱신."""
        try:
            while True:
                item = self.msgq.get_nowait()
                if item.startswith("__ERR__"):
                    messagebox.showerror("수집 실패", item[len("__ERR__"):])
                else:
                    self.running.pop(item, None)
                self.refresh_table()
        except queue.Empty:
            pass
        self.after(1000, self._poll)

    # ---------- 수집/현황 (병합 페이지) ----------
    def _page_collect(self):
        pg = tk.Frame(self)
        bar = tk.Frame(pg)
        bar.pack(fill="x", padx=8, pady=6)
        tk.Label(bar, text="수집 장수:", font=("맑은고딕", 11)).pack(side="left")
        self.num_e = tk.Entry(bar, width=6, font=("맑은고딕", 11))
        self.num_e.insert(0, "150")
        self.num_e.pack(side="left", padx=4)
        self.eng_v = tk.StringVar(value="naver")
        tk.OptionMenu(bar, self.eng_v, "naver", "bing").pack(side="left", padx=4)
        tk.Button(bar, text="새로고침", command=self.refresh_table).pack(side="left", padx=8)
        self.status_l = tk.Label(bar, text="", fg="green", font=("맑은고딕", 11))
        self.status_l.pack(side="left", padx=8)

        head = ["메뉴", "train", "val", "raw", "상태", "수집", "검수", "삭제"]
        for j, h in enumerate(head):
            tk.Label(pg, text=h, font=("맑은고딕", 11, "bold"),
                     width=10 if j else 14).grid(row=1, column=j, padx=2, pady=2)
        self.rows_f = tk.Frame(pg)
        self.rows_f.grid(row=2, column=0, columnspan=8, sticky="nsew")

        add = tk.Frame(pg)
        add.grid(row=3, column=0, columnspan=8, pady=10)
        tk.Label(add, text="새 메뉴:", font=("맑은고딕", 11, "bold")).pack(side="left")
        self.n_name = tk.Entry(add, width=12, font=("맑은고딕", 11))
        self.n_name.pack(side="left", padx=2)
        tk.Label(add, text="분류:", font=("맑은고딕", 11)).pack(side="left")
        self.n_cat = tk.Entry(add, width=8, font=("맑은고딕", 11))
        self.n_cat.insert(0, "한식")
        self.n_cat.pack(side="left", padx=2)
        tk.Label(add, text="kcal:", font=("맑은고딕", 11)).pack(side="left")
        self.n_kcal = tk.Entry(add, width=7, font=("맑은고딕", 11))
        self.n_kcal.insert(0, "500")
        self.n_kcal.pack(side="left", padx=2)
        tk.Button(add, text="추가", bg="#A5D6A7", font=("맑은고딕", 11, "bold"),
                  command=self._add).pack(side="left", padx=6)
        return pg

    def refresh_table(self):
        for w in self.rows_f.winfo_children():
            w.destroy()
        data = R.counts(BASE)
        for i, (m, c) in enumerate(data.items()):
            ok = c["train"] >= TRAIN_OK and c["val"] >= VAL_OK
            st = "OK" if ok else "부족"
            vals = [m, c["train"], c["val"], c["raw"], st]
            for j, v in enumerate(vals):
                fg = "green" if (j == 4 and ok) else ("red" if j == 4 else "black")
                tk.Label(self.rows_f, text=v, width=10 if j else 14,
                         font=("맑은고딕", 11), fg=fg).grid(row=i, column=j, padx=2, pady=2)
            b1 = tk.Button(self.rows_f, text="수집시작" if m not in self.running else "수집중..",
                           state="disabled" if m in self.running else "normal",
                           command=lambda m=m: self._start_crawl(m))
            b1.grid(row=i, column=5, padx=2)
            tk.Button(self.rows_f, text="검수",
                      command=lambda m=m: self._open_review(m)).grid(row=i, column=6, padx=2)
            tk.Button(self.rows_f, text="삭제", fg="red",
                      command=lambda m=m: self._delete(m)).grid(row=i, column=7, padx=2)
        run = f"수집중: {len(self.running)}건" if self.running else ""
        self.status_l.config(text=run)

    def _start_crawl(self, menu: str):
        try:
            num = int(self.num_e.get())
        except ValueError:
            messagebox.showwarning("알림", "수집 장수는 숫자입니다.")
            return
        eng = self.eng_v.get()
        th = threading.Thread(target=self._worker, args=(menu, num, eng), daemon=True)
        self.running[menu] = th
        th.start()
        self.refresh_table()

    def _worker(self, menu: str, num: int, eng: str):
        try:
            do_crawl(menu, num, eng)
        except Exception as e:  # 실패해도 UI는 살아있게
            self.msgq.put(menu)
            self.msgq.put("__ERR__" + menu + ": " + str(e)[:100])
            return
        self.msgq.put(menu)

    def _open_review(self, menu: str):
        subprocess.Popen([sys.executable, "review.py", "--menu", menu],
                         cwd=str(Path(__file__).resolve().parent))

    def _add(self):
        try:
            kcal = int(self.n_kcal.get())
        except ValueError:
            messagebox.showwarning("알림", "kcal은 숫자입니다.")
            return
        ok, msg = R.add_class(BASE, self.n_name.get(), self.n_cat.get(), kcal)
        (messagebox.showinfo if ok else messagebox.showwarning)("알림", msg)
        if ok:
            self.n_name.delete(0, "end")
        self.refresh_table()

    def _delete(self, menu: str):
        if not messagebox.askokcancel("확인", f"'{menu}' 등록을 해제할까요?\n(사진 파일은 보존됩니다)"):
            return
        ok, msg = R.delete_class(BASE, menu)
        (messagebox.showinfo if ok else messagebox.showwarning)("알림", msg)
        self.refresh_table()

    # ---------- 검수 페이지 ----------
    def _page_review(self):
        pg = tk.Frame(self)
        tk.Label(pg, text="검수할 메뉴를 선택하세요", font=("맑은고딕", 13, "bold")).pack(pady=10)
        self.rev_lb = tk.Listbox(pg, font=("맑은고딕", 12), width=30, height=20)
        self.rev_lb.pack(pady=6)
        tk.Button(pg, text="갤러리 검수 열기", bg="#A5D6A7", font=("맑은고딕", 12, "bold"),
                  command=self._review_selected).pack(pady=6)
        tk.Label(pg, text="클릭으로 선택 → 선택 저장 (O/X 한장씩 방식은 폐기됨)",
                 font=("맑은고딕", 10), fg="gray").pack()
        return pg

    def _reload_review_list(self):
        self.rev_lb.delete(0, "end")
        for m in R.load_classes(BASE):
            self.rev_lb.insert("end", m)

    def _review_selected(self):
        sel = self.rev_lb.curselection()
        if not sel:
            messagebox.showwarning("알림", "메뉴를 선택하세요.")
            return
        self._open_review(self.rev_lb.get(sel[0]))


if __name__ == "__main__":
    Studio().mainloop()
