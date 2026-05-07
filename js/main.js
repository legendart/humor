import { SUBREDDITS, SUBREDDIT_LABELS, fetchAllSubreddits, formatScore } from './reddit.js';
import { fetchKoreanPosts } from './korean.js';

/* ── State ─────────────────────────────────────────────────────────────── */
let lang        = 'en';
let activeSubs  = [...SUBREDDITS];
let allPosts    = [];
let displayed   = 0;
const PAGE_SIZE = 30;

/* ── DOM refs ───────────────────────────────────────────────────────────── */
const gridEl        = document.getElementById('grid');
const statusDot     = document.getElementById('statusDot');
const statusText    = document.getElementById('statusText');
const filtersWrap   = document.getElementById('filtersWrap');
const sortSelect    = document.getElementById('sortSelect');
const loadMoreWrap  = document.getElementById('loadMoreWrap');
const loadMoreBtn   = document.getElementById('loadMoreBtn');

/* ── Lang toggle ────────────────────────────────────────────────────────── */
document.querySelectorAll('.lang-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    lang = btn.dataset.lang;
    document.querySelectorAll('.lang-btn').forEach(b => b.classList.toggle('active', b.dataset.lang === lang));
    renderFilters();
    loadPosts();
  });
});

/* ── Subreddit filters ──────────────────────────────────────────────────── */
function renderFilters() {
  filtersWrap.innerHTML = '';
  if (lang !== 'en') return;

  const allBtn = makeFilterBtn('All', null);
  filtersWrap.appendChild(allBtn);

  SUBREDDITS.forEach(sub => {
    filtersWrap.appendChild(makeFilterBtn(SUBREDDIT_LABELS[sub], sub));
  });
  updateFilterActive();
}

function makeFilterBtn(label, sub) {
  const btn = document.createElement('button');
  btn.className = 'filter-btn';
  btn.textContent = label;
  btn.dataset.sub = sub ?? '';
  btn.addEventListener('click', () => {
    if (!sub) {
      activeSubs = [...SUBREDDITS];
    } else {
      activeSubs = activeSubs.includes(sub)
        ? activeSubs.filter(s => s !== sub)
        : [...activeSubs, sub];
      if (activeSubs.length === 0) activeSubs = [...SUBREDDITS];
    }
    updateFilterActive();
    sortAndRender();
  });
  return btn;
}

function updateFilterActive() {
  filtersWrap.querySelectorAll('.filter-btn').forEach(btn => {
    const sub = btn.dataset.sub;
    if (!sub) {
      btn.classList.toggle('active', activeSubs.length === SUBREDDITS.length);
    } else {
      btn.classList.toggle('active', activeSubs.includes(sub));
    }
  });
}

/* ── Sort ────────────────────────────────────────────────────────────────── */
sortSelect.addEventListener('change', sortAndRender);

function sortPosts(posts) {
  const v = sortSelect.value;
  const arr = [...posts];
  if (v === 'hot')  return arr.sort((a, b) => b.score - a.score);
  if (v === 'new')  return arr.sort((a, b) => {
    const at = a.createdAt || a.createdUtc * 1000 || 0;
    const bt = b.createdAt || b.createdUtc * 1000 || 0;
    return bt - at;
  });
  if (v === 'views') return arr.sort((a, b) => (b.views || 0) - (a.views || 0));
  return arr;
}

/* ── Load ────────────────────────────────────────────────────────────────── */
async function loadPosts() {
  setStatus('loading', lang === 'en' ? 'Reddit에서 불러오는 중...' : '한국 커뮤니티 데이터 로드 중...');
  showSkeletons();
  allPosts = [];
  displayed = 0;

  try {
    if (lang === 'en') {
      allPosts = await fetchAllSubreddits(activeSubs, 'hot');
    } else {
      allPosts = await fetchKoreanPosts();
    }
    sortAndRender();
    setStatus('ok', `${allPosts.length}개 게시물 로드됨`);
  } catch (err) {
    console.error(err);
    setStatus('error', '로드 실패 — 새로고침해 주세요');
    showError();
  }
}

function sortAndRender() {
  const sorted = sortPosts(
    lang === 'en'
      ? allPosts.filter(p => activeSubs.includes(p.sub))
      : allPosts
  );
  allPosts = sorted; // keep sorted order
  displayed = 0;
  gridEl.innerHTML = '';
  appendCards(PAGE_SIZE);
  updateLoadMore();
}

function appendCards(n) {
  const slice = allPosts.slice(displayed, displayed + n);
  slice.forEach(post => gridEl.appendChild(makeCard(post)));
  displayed += slice.length;
}

function updateLoadMore() {
  const hasMore = displayed < allPosts.length;
  loadMoreWrap.hidden = !hasMore;
}

loadMoreBtn.addEventListener('click', () => {
  appendCards(PAGE_SIZE);
  updateLoadMore();
});

/* ── Card ─────────────────────────────────────────────────────────────────  */
function makeCard(post) {
  const a = document.createElement('a');
  a.className = 'card';
  a.href = post.url;
  a.target = '_blank';
  a.rel = 'noopener noreferrer';

  const thumbHtml = post.thumb
    ? `<img src="${escHtml(post.thumb)}" alt="" loading="lazy" onerror="this.parentNode.innerHTML='<span class=card-thumb-placeholder>😂</span>'">`
    : `<span class="card-thumb-placeholder">😂</span>`;

  const nsfwBadge = post.nsfw ? `<span class="card-nsfw-badge">NSFW</span>` : '';

  const scoreHtml = `
    <span class="card-score">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/>
        <path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>
      </svg>
      ${formatScore(post.score)}
    </span>`;

  const viewsHtml = post.views != null ? `
    <span class="card-views">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
        <circle cx="12" cy="12" r="3"/>
      </svg>
      ${formatScore(post.views)}
    </span>` : '';

  const sourceLabel = post.lang === 'ko'
    ? `<span class="ko-site-badge">${escHtml(post.source)}</span>`
    : `<span>${escHtml(post.source)}</span>`;

  a.innerHTML = `
    <div class="card-thumb">
      ${thumbHtml}
      ${nsfwBadge}
    </div>
    <div class="card-body">
      <div class="card-source">
        <span class="card-source-dot"></span>
        ${sourceLabel}
      </div>
      <p class="card-title">${escHtml(post.title)}</p>
      <div class="card-meta">
        ${scoreHtml}
        ${viewsHtml}
        <span class="card-time">${escHtml(post.timeAgo)}</span>
      </div>
    </div>`;

  return a;
}

/* ── Helpers ──────────────────────────────────────────────────────────────  */
function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function setStatus(state, text) {
  statusDot.className = 'status-dot' + (state !== 'ok' ? ` ${state}` : '');
  statusText.textContent = text;
}

function showSkeletons(n = 12) {
  gridEl.innerHTML = Array.from({length: n}, () => `
    <div class="skeleton">
      <div class="skel-thumb"></div>
      <div class="skel-line"></div>
      <div class="skel-line short"></div>
    </div>`).join('');
}

function showError() {
  gridEl.innerHTML = `
    <div class="empty-state">
      <div class="icon">😵</div>
      <h3>데이터를 불러올 수 없습니다</h3>
      <p>잠시 후 다시 시도해 주세요</p>
    </div>`;
}

/* ── Init ─────────────────────────────────────────────────────────────────  */
renderFilters();
loadPosts();
