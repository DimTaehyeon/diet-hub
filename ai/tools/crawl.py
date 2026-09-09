"""메뉴별 이미지 크롤링: python crawl.py --menu 라면 --num 120 [--engine bing]
- ai/raw/{메뉴}/ 에 저장 후 review.py로 검수.
- 라면은 일식 라멘 제외를 위해 한국 라면 쿼리만 사용 (잔여물은 검수에서 제거).
"""
import argparse
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "raw"

# 메뉴별 검색어 (쿼리당 균등 분배). 일식 라멘 계열 단어는 넣지 않는다.
QUERY_PRESETS = {
    "라면": ["집에서 끓인 라면 한그릇", "라면 먹방 그릇", "냄비째 먹는 라면"],
    "탕수육": ["탕수육", "찹쌀탕수육 접시"],
    "치킨": ["양념치킨", "후라이드치킨 한마리"],
    "피자": ["페퍼로니피자 한판", "치즈피자"],
}


def queries_for(menu: str):
    return QUERY_PRESETS.get(menu, [menu])


def valid_menu(menu: str) -> bool:
    p = BASE / "models" / "classes.txt"
    return menu in [l.strip() for l in p.read_text(encoding="utf-8").splitlines()]


def crawl(menu: str, num: int, engine: str = "bing"):
    if not valid_menu(menu):
        raise ValueError(f"classes.txt에 없는 메뉴: {menu}")
    out = RAW / menu
    out.mkdir(parents=True, exist_ok=True)
    start = len([p for p in out.iterdir() if p.is_file() and not p.name.startswith("_")])

    if engine == "google":
        from icrawler.builtin import GoogleImageCrawler as Crawler
    else:
        from icrawler.builtin import BingImageCrawler as Crawler

    queries = queries_for(menu)
    remain = num - start
    base, extra = divmod(max(remain, 0), len(queries))
    for i, q in enumerate(queries):
        per_q = base + (1 if i < extra else 0)
        if per_q <= 0:
            break
        crawler = Crawler(storage={"root_dir": str(out)})
        # 파일명 충돌 방지: 기존 파일 다음 번호부터 자동 부여
        crawler.crawl(keyword=q, max_num=per_q, min_size=(300, 300),
                      file_idx_offset="auto")
    total = len([p for p in out.iterdir() if p.is_file() and not p.name.startswith("_")])
    print(f"[완료] ai/raw/{menu}/ : 총 {total}장 (목표 {num}장)")
    print(f"다음: python review.py --menu {menu}")


def main():
    ap = argparse.ArgumentParser(description="메뉴 이미지 크롤링")
    ap.add_argument("--menu", required=True, help="예: 라면 (일식라멘 제외 쿼리 자동)")
    ap.add_argument("--num", type=int, default=120)
    ap.add_argument("--engine", default="bing", choices=["bing", "google"])
    a = ap.parse_args()
    crawl(a.menu, a.num, a.engine)


if __name__ == "__main__":
    main()
