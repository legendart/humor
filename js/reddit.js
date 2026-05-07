/* reddit.js — fetch posts from Reddit JSON API (no auth needed) */

const SUBREDDITS = ['funny', 'memes', 'HumansBeingBros', 'Unexpected', 'nextfuckinglevel'];

const SUBREDDIT_LABELS = {
  funny:             'r/funny',
  memes:             'r/memes',
  HumansBeingBros:   'r/HumansBeingBros',
  Unexpected:        'r/Unexpected',
  nextfuckinglevel:  'r/nextfuckinglevel',
};

function formatRedditThumb(post) {
  const p = post.data;
  if (p.preview?.images?.[0]?.source?.url) {
    return p.preview.images[0].source.url.replace(/&amp;/g, '&');
  }
  if (p.thumbnail && p.thumbnail.startsWith('http')) return p.thumbnail;
  return null;
}

function redditTimeAgo(utc) {
  const sec = Math.floor(Date.now() / 1000) - utc;
  if (sec < 60)   return `${sec}s ago`;
  if (sec < 3600) return `${Math.floor(sec/60)}m ago`;
  if (sec < 86400) return `${Math.floor(sec/3600)}h ago`;
  return `${Math.floor(sec/86400)}d ago`;
}

function formatScore(n) {
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return String(n);
}

const CORS_PROXY = 'https://corsproxy.io/?';

async function fetchSubreddit(sub, sort = 'hot', limit = 25) {
  const target = `https://www.reddit.com/r/${sub}/${sort}.json?limit=${limit}&raw_json=1`;
  const url = CORS_PROXY + encodeURIComponent(target);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Reddit ${sub}: ${res.status}`);
  const json = await res.json();
  return json.data.children
    .filter(p => !p.data.stickied)
    .map(p => ({
      id:        `reddit-${p.data.id}`,
      title:     p.data.title,
      url:       `https://www.reddit.com${p.data.permalink}`,
      thumb:     formatRedditThumb(p),
      source:    SUBREDDIT_LABELS[sub] || `r/${sub}`,
      sub:       sub,
      score:     p.data.score,
      views:     null,
      timeAgo:   redditTimeAgo(p.data.created_utc),
      createdUtc:p.data.created_utc,
      nsfw:      p.data.over_18,
      flair:     p.data.link_flair_text || null,
      lang:      'en',
    }));
}

async function fetchAllSubreddits(activeSubs = SUBREDDITS, sort = 'hot') {
  const results = await Promise.allSettled(
    activeSubs.map(sub => fetchSubreddit(sub, sort))
  );
  const posts = [];
  results.forEach(r => {
    if (r.status === 'fulfilled') posts.push(...r.value);
  });
  return posts;
}

export { SUBREDDITS, SUBREDDIT_LABELS, fetchAllSubreddits, fetchSubreddit, formatScore };
