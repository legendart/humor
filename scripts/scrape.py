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
}

MAX_PER_SITE = 20
NOW = datetime.now(timezone.utc).isoformat()


def get(url: str, **kwargs) -> requests.Response:
    return requests.get(url, headers=HEADERS, timeout=15, **kwargs)


# ── FMKorea ──────────────────────────────────────────────────────────────────

def scrape_fmkorea() -> list[dict]:
    posts = []
    try:
        url = "https://www.fmkorea.com/humor"
        res = get(url)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "lxml")

        items = soup.select("ul.content_list li.li_br_n")
        if not items:
            items = soup.select("ul.content_list li")

        for item in items[:MAX_PER_SITE]:
            try:
                a_tag = item.select_one("h3.title a, .title a")
                if not a_tag:
                    continue
                title = a_tag.get_text(strip=True)
                href  = a_tag.get("href", "")
                if href.startswith("/"):
                    href = "https://www.fmkorea.com" + href

                # score / recommend
                score_el = item.select_one(".voted_count, .recommend")
                score = 0
                if score_el:
                    try:
                        score = int(score_el.get_text(strip=True).replace(",", ""))
                    except ValueError:
                        pass

                # views
                view_el = item.select_one(".read_count, .view_count")
                views = None
                if view_el:
                    try:
                        views = int(view_el.get_text(strip=True).replace(",", ""))
                    except ValueError:
                        pass

                # thumbnail
                thumb = None
                img = item.select_one("img")
                if img:
                    thumb = img.get("src") or img.get("data-src")
                    if thumb and thumb.startswith("//"):
                        thumb = "https:" + thumb

                post_id = re.search(r"/(\d+)", href)
                posts.append({
                    "id":         post_id.group(1) if post_id else href,
                    "site":       "fmkorea",
                    "title":      title,
                    "url":        href,
                    "thumb":      thumb,
                    "score":      score,
                    "views":      views,
                    "crawled_at": NOW,
                })
            except Exception as e:
                print(f"  [fmkorea] item error: {e}", file=sys.stderr)
                continue

        print(f"[fmkorea] {len(posts)} posts")
    except Exception as e:
        print(f"[fmkorea] FAILED: {e}", file=sys.stderr)
    return posts


# ── Ruliweb ───────────────────────────────────────────────────────────────────

def scrape_ruliweb() -> list[dict]:
    posts = []
    try:
        url = "https://bbs.ruliweb.com/humor"
        res = get(url, headers={**HEADERS, "Referer": "https://bbs.ruliweb.com/"})
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "lxml")

        rows = soup.select("table.board_list_table tbody tr.table_body")
        if not rows:
            rows = soup.select("tr.item.normal")

        for row in rows[:MAX_PER_SITE]:
            try:
                a_tag = row.select_one("a.deco")
                if not a_tag:
                    a_tag = row.select_one("td.subject a")
                if not a_tag:
                    continue

                title = a_tag.get_text(strip=True)
                href  = a_tag.get("href", "")

                # score
                score_el = row.select_one("td.recomd, td.like_count")
                score = 0
                if score_el:
                    try:
                        score = int(score_el.get_text(strip=True).replace(",", ""))
                    except ValueError:
                        pass

                # views
                view_el = row.select_one("td.hit")
                views = None
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
            except Exception as e:
                print(f"  [ruliweb] item error: {e}", file=sys.stderr)
                continue

        print(f"[ruliweb] {len(posts)} posts")
    except Exception as e:
        print(f"[ruliweb] FAILED: {e}", file=sys.stderr)
    return posts


# ── 웃긴대학 ────────────────────────────────────────────────────────────────

def scrape_humoruniv() -> list[dict]:
    posts = []
    try:
        url = "https://web.humoruniv.com/board/humor/list.html"
        res = get(url)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "lxml")

        rows = soup.select("table tr")
        count = 0
        for row in rows:
            if count >= MAX_PER_SITE:
                break
            try:
                a_tag = row.select_one("a[href*='read']")
                if not a_tag:
                    continue
                title = a_tag.get_text(strip=True)
                if not title:
                    continue

                href = a_tag.get("href", "")
                if href.startswith("/"):
                    href = "https://web.humoruniv.com" + href
                elif not href.startswith("http"):
                    href = "https://web.humoruniv.com/" + href.lstrip("./")

                # score — look for td containing vote/like patterns
                score = 0
                for td in row.select("td"):
                    txt = td.get_text(strip=True)
                    if txt.isdigit() and int(txt) > score:
                        score = int(txt)  # rough heuristic

                # thumbnail
                thumb = None
                img = row.select_one("img")
                if img:
                    src = img.get("src", "")
                    if src and "thumb" in src.lower():
                        thumb = src if src.startswith("http") else "https://web.humoruniv.com" + src

                post_id = re.search(r"num=(\d+)", href)
                posts.append({
                    "id":         post_id.group(1) if post_id else href,
                    "site":       "humoruniv",
                    "title":      title,
                    "url":        href,
                    "thumb":      thumb,
                    "score":      score,
                    "views":      None,
                    "crawled_at": NOW,
                })
                count += 1
            except Exception as e:
                print(f"  [humoruniv] item error: {e}", file=sys.stderr)
                continue

        print(f"[humoruniv] {len(posts)} posts")
    except Exception as e:
        print(f"[humoruniv] FAILED: {e}", file=sys.stderr)
    return posts


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    out_path = Path(__file__).parent.parent / "data" / "ko.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_posts: list[dict] = []

    for scraper in [scrape_fmkorea, scrape_ruliweb, scrape_humoruniv]:
        all_posts.extend(scraper())
        time.sleep(1)  # polite delay between sites

    # sort by score descending
    all_posts.sort(key=lambda p: p.get("score", 0), reverse=True)

    out_path.write_text(json.dumps(all_posts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Saved {len(all_posts)} posts to {out_path}")


if __name__ == "__main__":
    main()
