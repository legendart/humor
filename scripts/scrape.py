#!/usr/bin/env python3
"""Scrape Korean humor communities and write data/ko.json."""

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.co.kr/",
}

MAX_PER_SITE = 20
NOW = datetime.now(timezone.utc).isoformat()

NOTICE_KEYWORDS = ["공지", "📢", "◤", "◢", "이용 규칙", "비밀번호", "모바일에서"]


def get_html(url: str, extra_headers=None) -> requests.Response:
    headers = {**HEADERS, **(extra_headers or {})}
    return requests.get(url, headers=headers, timeout=15)


# ── FMKorea ──────────────────────────────────────────────────────────────────

def scrape_fmkorea() -> list[dict]:
    posts = []
    try:
        res = get_html("https://www.fmkorea.com/humor")
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "lxml")

        for tr in soup.select("table tr"):
            cate_el = tr.select_one("td.cate")
            title_td = tr.select_one("td.title")
            if not cate_el or not title_td:
                continue
            if "공지" in cate_el.get_text():
                continue

            a = title_td.select_one("a")
            if not a:
                continue

            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not href.startswith("/"):
                continue
            href = "https://www.fmkorea.com" + href

            score = 0
            vote_el = tr.select_one(".voted_count")
            if vote_el:
                try:
                    score = int(vote_el.get_text(strip=True))
                except ValueError:
                    pass

            views = None
            view_el = tr.select_one(".count")
            if view_el:
                try:
                    views = int(view_el.get_text(strip=True).replace(",", ""))
                except ValueError:
                    pass

            post_id = re.search(r"/(\d+)", href)
            posts.append({
                "id":         post_id.group(1) if post_id else href,
                "site":       "fmkorea",
                "title":      title,
                "url":        href,
                "thumb":      None,
                "score":      score,
                "views":      views,
                "crawled_at": NOW,
            })
            if len(posts) >= MAX_PER_SITE:
                break

        print(f"[fmkorea] {len(posts)} posts")
    except Exception as e:
        print(f"[fmkorea] FAILED: {e}", file=sys.stderr)
    return posts


# ── Ruliweb ───────────────────────────────────────────────────────────────────

def scrape_ruliweb() -> list[dict]:
    posts = []
    try:
        # Board 300143 is the Ruliweb humor community board
        url = "https://bbs.ruliweb.com/community/board/300143"
        res = get_html(url, {"Referer": "https://bbs.ruliweb.com/"})
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "lxml")

        for row in soup.select("tr.table_body"):
            a = row.select_one("a.deco") or row.select_one("td.subject a")
            if not a:
                continue

            title = a.get_text(strip=True)
            if not title or any(k in title for k in NOTICE_KEYWORDS):
                continue

            href = a.get("href", "")
            if not href.startswith("http"):
                href = "https://bbs.ruliweb.com" + href

            score = 0
            score_el = row.select_one("td.recomd")
            if score_el:
                try:
                    score = int(score_el.get_text(strip=True).replace(",", ""))
                except ValueError:
                    pass

            views = None
            view_el = row.select_one("td.hit")
            if view_el:
                try:
                    views = int(view_el.get_text(strip=True).replace(",", ""))
                except ValueError:
                    pass

            post_id = re.search(r"/(\d+)", href)
            posts.append({
                "id":         post_id.group(1) if post_id else href,
                "site":       "ruliweb",
                "title":      title,
                "url":        href,
                "thumb":      None,
                "score":      score,
                "views":      views,
                "crawled_at": NOW,
            })
            if len(posts) >= MAX_PER_SITE:
                break

        print(f"[ruliweb] {len(posts)} posts")
    except Exception as e:
        print(f"[ruliweb] FAILED: {e}", file=sys.stderr)
    return posts


# ── Theqoo (더쿠) ─────────────────────────────────────────────────────────────

def scrape_theqoo() -> list[dict]:
    posts = []
    try:
        res = get_html("https://theqoo.net/square")
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "lxml")

        for a in soup.select('a[href*="/square/"]'):
            href = a.get("href", "")
            title = a.get_text(strip=True)

            # Real posts have 8+ digit IDs
            if not re.search(r"/square/\d{8,}", href):
                continue
            if not title or len(title) < 4:
                continue
            if any(k in title for k in NOTICE_KEYWORDS):
                continue

            full_url = "https://theqoo.net" + href if href.startswith("/") else href

            # Try to find score in parent row
            score = 0
            parent = a.find_parent("tr") or a.find_parent("li")
            if parent:
                for el in parent.select("[class*='recommend'], [class*='like'], [class*='count'], td"):
                    txt = el.get_text(strip=True).replace(",", "")
                    if txt.isdigit() and 0 < int(txt) < 100000:
                        score = max(score, int(txt))

            post_id = re.search(r"/square/(\d+)", href)
            posts.append({
                "id":         post_id.group(1) if post_id else href,
                "site":       "theqoo",
                "title":      title,
                "url":        full_url,
                "thumb":      None,
                "score":      score,
                "views":      None,
                "crawled_at": NOW,
            })
            if len(posts) >= MAX_PER_SITE:
                break

        print(f"[theqoo] {len(posts)} posts")
    except Exception as e:
        print(f"[theqoo] FAILED: {e}", file=sys.stderr)
    return posts


# ── 뽐뿌 (Ppomppu) ───────────────────────────────────────────────────────────

def scrape_ppomppu() -> list[dict]:
    posts = []
    try:
        res = get_html("https://www.ppomppu.co.kr/zboard/zboard.php?id=freeboard")
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "lxml")

        for tr in soup.select("tr.baseList"):
            # Title link: a.baseList-title with href containing 'no='
            a = tr.select_one("a.baseList-title")
            if not a:
                continue

            title_el = a.select_one("span") or a
            title = title_el.get_text(strip=True)
            if not title or len(title) < 3:
                continue
            if any(k in title for k in NOTICE_KEYWORDS):
                continue

            href = a.get("href", "")
            if "no=" not in href:
                continue
            if href.startswith("http"):
                full_url = href
            else:
                full_url = "https://www.ppomppu.co.kr/zboard/" + href.lstrip("/")

            # Score: td.baseList-rec
            score = 0
            rec_td = tr.select_one("td.baseList-rec")
            if rec_td:
                try:
                    score = int(rec_td.get_text(strip=True).replace(",", "").split("-")[0] or 0)
                except (ValueError, IndexError):
                    pass

            # Views: td.baseList-hit
            views = None
            hit_td = tr.select_one("td.baseList-hit")
            if hit_td:
                try:
                    views = int(hit_td.get_text(strip=True).replace(",", ""))
                except ValueError:
                    pass

            post_id = re.search(r"no=(\d+)", full_url)
            posts.append({
                "id":         post_id.group(1) if post_id else full_url,
                "site":       "ppomppu",
                "title":      title,
                "url":        full_url,
                "thumb":      None,
                "score":      score,
                "views":      views,
                "crawled_at": NOW,
            })
            if len(posts) >= MAX_PER_SITE:
                break

        print(f"[ppomppu] {len(posts)} posts")
    except Exception as e:
        print(f"[ppomppu] FAILED: {e}", file=sys.stderr)
    return posts


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    out_path = Path(__file__).parent.parent / "data" / "ko.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_posts: list[dict] = []

    for scraper in [scrape_fmkorea, scrape_ruliweb, scrape_theqoo, scrape_ppomppu]:
        all_posts.extend(scraper())
        time.sleep(1)

    all_posts.sort(key=lambda p: p.get("score", 0), reverse=True)

    out_path.write_text(json.dumps(all_posts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Saved {len(all_posts)} posts to {out_path}")


if __name__ == "__main__":
    main()
