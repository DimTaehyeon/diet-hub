"""메뉴별 이미지 크롤링: python crawl.py --menu 라면 --num 120 [--engine naver]
- naver: 셀레니움 헤드리스 크롬으로 네이버 이미지 수집 (기본값, 한식 품질 양호)
- google: 자동화 차단(/sorry)으로 현재 동작 안 함. 실브라우저 수동 저장만 가능
- bing: icrawler (예비용)
- ai/raw/{메뉴}/ 에 저장 후 review.py로 검수.
- 라면은 일식 라멘 제외를 위해 한국 라면 쿼리만 사용 (잔여물은 검수에서 제거).
"""
import argparse
import hashlib
from pathlib import Path
from urllib.parse import quote_plus

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "raw"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# 메뉴별 검색어 (쿼리당 균등 분배). 일식 라멘 계열 단어는 넣지 않는다.
QUERY_PRESETS = {
    "라면": ["집에서 끓인 라면 한그릇", "라면 먹방 그릇", "냄비째 먹는 라면"],
    "탕수육": ["탕수육", "찹쌀탕수육 접시"],
    "후라이드치킨": ["후라이드치킨 한마리", "바삭한 후라이드치킨"],
    "양념치킨": ["양념치킨", "매운 양념치킨"],
    "피자": ["페퍼로니피자 한판", "치즈피자"],
}


def queries_for(menu: str):
    return QUERY_PRESETS.get(menu, [menu])


def valid_menu(menu: str) -> bool:
    p = BASE / "models" / "classes.txt"
    return menu in [l.strip() for l in p.read_text(encoding="utf-8").splitlines()]


def _download(url: str, outdir: Path) -> bool:
    import requests
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": UA})
        if r.status_code != 200 or len(r.content) < 15000:
            return False
        ct = r.headers.get("Content-Type", "")
        ext = ".jpg"
        if "png" in ct:
            ext = ".png"
        elif "webp" in ct:
            ext = ".webp"
        name = f"g_{hashlib.md5(r.content).hexdigest()[:10]}{ext}"
        if (outdir / name).exists():
            return False  # 중복
        (outdir / name).write_bytes(r.content)
        return True
    except Exception:
        return False


def _make_driver():
    import tempfile
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    # 기본 크롬 프로필 잠금 회피용 임시 프로필
    opts.add_argument("--user-data-dir=" + tempfile.mkdtemp(prefix="ch_"))
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(f"--user-agent={UA}")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)


def crawl_naver(keyword: str, max_num: int, outdir: Path) -> int:
    """네이버 이미지검색 썸네일 수집. 반환: 저장 장수."""
    import time
    from selenium.webdriver.common.by import By

    driver = _make_driver()
    saved, seen = 0, set()
    try:
        driver.get(f"https://search.naver.com/search.naver?where=image&query={quote_plus(keyword)}")
        time.sleep(3)
        scrolls = 0
        while saved < max_num and scrolls < 40:
            for im in driver.find_elements(By.CSS_SELECTOR, "img._fe_image_tab_content_thumbnail_image"):
                if saved >= max_num:
                    break
                src = im.get_attribute("src") or ""
                if src.startswith("http") and src not in seen:
                    seen.add(src)
                    if _download(src, outdir):
                        saved += 1
            driver.execute_script("window.scrollBy(0, 2500);")
            time.sleep(1.2)
            scrolls += 1
    finally:
        driver.quit()
    return saved


def crawl_bing(keyword: str, max_num: int, outdir: Path):
    from icrawler.builtin import BingImageCrawler
    crawler = BingImageCrawler(storage={"root_dir": str(outdir)})
    crawler.crawl(keyword=keyword, max_num=max_num, min_size=(300, 300),
                  file_idx_offset="auto")


def crawl(menu: str, num: int, engine: str = "naver"):
    if not valid_menu(menu):
        raise ValueError(f"classes.txt에 없는 메뉴: {menu}")
    out = RAW / menu
    out.mkdir(parents=True, exist_ok=True)
    start = len([p for p in out.iterdir() if p.is_file() and not p.name.startswith("_")])

    queries = queries_for(menu)
    remain = num - start
    base, extra = divmod(max(remain, 0), len(queries))
    for i, q in enumerate(queries):
        per_q = base + (1 if i < extra else 0)
        if per_q <= 0:
            break
        if engine == "naver":
            got = crawl_naver(q, per_q, out)
            print(f"  [{q}] {got}/{per_q}장 저장")
        else:
            crawl_bing(q, per_q, out)
    total = len([p for p in out.iterdir() if p.is_file() and not p.name.startswith("_")])
    print(f"[완료] ai/raw/{menu}/ : 총 {total}장 (목표 {num}장)")
    print(f"다음: python review.py --menu {menu}")


def main():
    ap = argparse.ArgumentParser(description="메뉴 이미지 크롤링")
    ap.add_argument("--menu", required=True, help="예: 라면 (일식라멘 제외 쿼리 자동)")
    ap.add_argument("--num", type=int, default=120)
    ap.add_argument("--engine", default="naver", choices=["naver", "bing"])
    a = ap.parse_args()
    crawl(a.menu, a.num, a.engine)


if __name__ == "__main__":
    main()
