/* korean.js — load pre-scraped Korean humor posts from data/ko.json */

const KO_SITE_LABELS = {
  fmkorea:  '에펨코리아',
  ruliweb:  '루리웹',
  theqoo:   '더쿠',
  ppomppu:  '뽐뿌',
};

function koTimeAgo(isoStr) {
  if (!isoStr) return '';
  const sec = Math.floor((Date.now() - new Date(isoStr).getTime()) / 1000);
  if (sec < 60)    return `${sec}초 전`;
  if (sec < 3600)  return `${Math.floor(sec/60)}분 전`;
  if (sec < 86400) return `${Math.floor(sec/3600)}시간 전`;
  return `${Math.floor(sec/86400)}일 전`;
}

async function fetchKoreanPosts() {
  const res = await fetch('./data/ko.json', { cache: 'no-cache' });
  if (!res.ok) throw new Error(`ko.json fetch failed: ${res.status}`);
  const raw = await res.json();
  return raw.map(item => ({
    id:        `ko-${item.site}-${item.id || Math.random()}`,
    title:     item.title,
    url:       item.url,
    thumb:     item.thumb || null,
    source:    KO_SITE_LABELS[item.site] || item.site,
    site:      item.site,
    score:     item.score ?? item.recommend ?? 0,
    views:     item.views ?? null,
    timeAgo:   koTimeAgo(item.crawled_at || item.date),
    createdAt: item.crawled_at || item.date || null,
    nsfw:      false,
    lang:      'ko',
  }));
}

export { fetchKoreanPosts, KO_SITE_LABELS };
