const state = {
  keywords: [],
  selectedKeywordId: null,
  suggestions: [],
};

async function api(path, options) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 401) {
    showLoginOverlay();
    throw new Error("로그인이 필요합니다.");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `요청 실패 (${res.status})`);
  }
  if (res.status === 204) return null;
  return res.json();
}

function showLoginOverlay() {
  document.getElementById("login-overlay").hidden = false;
  document.getElementById("login-password").focus();
}

function hideLoginOverlay() {
  document.getElementById("login-overlay").hidden = true;
}

async function checkAuthAndInit() {
  const status = await api("/api/me").catch(() => ({ authenticated: false }));
  if (status.authenticated) {
    hideLoginOverlay();
    loadKeywords();
    loadLastSync();
  } else {
    showLoginOverlay();
  }
}

async function submitLogin(event) {
  event.preventDefault();
  const input = document.getElementById("login-password");
  const errorEl = document.getElementById("login-error");
  errorEl.textContent = "";

  try {
    await api("/api/login", {
      method: "POST",
      body: JSON.stringify({ password: input.value }),
    });
    input.value = "";
    hideLoginOverlay();
    loadKeywords();
    loadLastSync();
  } catch (e) {
    errorEl.textContent = "비밀번호가 올바르지 않습니다.";
  }
}

async function loadKeywords() {
  state.keywords = await api("/api/keywords");
  renderKeywordList();
  renderTabs();
}

function renderKeywordList() {
  const list = document.getElementById("keyword-list");
  list.innerHTML = "";
  if (state.keywords.length === 0) {
    list.innerHTML = '<li class="muted">등록된 키워드가 없습니다.</li>';
    return;
  }
  for (const kw of state.keywords) {
    const li = document.createElement("li");
    li.innerHTML = `<span>${escapeHtml(kw.keyword)}</span>`;
    const delBtn = document.createElement("button");
    delBtn.className = "delete";
    delBtn.textContent = "삭제";
    delBtn.onclick = () => deleteKeyword(kw.id);
    li.appendChild(delBtn);
    list.appendChild(li);
  }
}

function renderTabs() {
  const tabs = document.getElementById("keyword-tabs");
  tabs.innerHTML = "";

  if (state.keywords.length === 0) {
    state.selectedKeywordId = null;
    document.getElementById("article-list").innerHTML =
      '<p class="muted">키워드를 추가하면 관련 뉴스가 표시됩니다.</p>';
    const panel = document.getElementById("stock-panel");
    panel.hidden = true;
    panel.innerHTML = "";
    return;
  }

  if (!state.keywords.some((kw) => kw.id === state.selectedKeywordId)) {
    state.selectedKeywordId = state.keywords[0].id;
  }

  for (const kw of state.keywords) {
    const btn = document.createElement("button");
    btn.textContent = kw.keyword;
    btn.className = kw.id === state.selectedKeywordId ? "active" : "";
    btn.onclick = () => selectKeyword(kw.id);
    tabs.appendChild(btn);
  }

  loadStockPanel();
  loadArticles();
}

function selectKeyword(id) {
  state.selectedKeywordId = id;
  renderTabs();
}

async function loadStockPanel() {
  const panel = document.getElementById("stock-panel");
  const selected = state.keywords.find((kw) => kw.id === state.selectedKeywordId);

  if (!selected || !selected.stock_code) {
    panel.hidden = true;
    panel.innerHTML = "";
    return;
  }

  panel.hidden = false;
  panel.innerHTML = '<p class="muted">시세 불러오는 중...</p>';

  try {
    const stock = await api(`/api/keywords/${selected.id}/stock`);
    const directionClass =
      stock.direction === "RISING" ? "rising" : stock.direction === "FALLING" ? "falling" : "unchanged";
    const sign = stock.direction === "RISING" ? "+" : stock.direction === "FALLING" ? "-" : "";
    const displayName = selected.stock_name || selected.keyword;
    panel.innerHTML = `
      <a href="${stock.item_page_url}" target="_blank" rel="noopener noreferrer" class="stock-chart-link">
        <img src="${stock.chart_url}" alt="${escapeHtml(displayName)} 차트 (네이버 증권에서 크게 보기)" />
      </a>
      <div class="stock-info">
        <span class="stock-name">${escapeHtml(displayName)} (${escapeHtml(selected.stock_code)})</span>
        <span class="stock-price">${escapeHtml(stock.price || "-")}원</span>
        <span class="stock-change ${directionClass}">${sign}${escapeHtml(stock.change || "-")} (${escapeHtml(stock.change_ratio || "-")}%)</span>
      </div>
    `;
  } catch (e) {
    panel.innerHTML = `<p class="error">${escapeHtml(e.message)}</p>`;
  }
}

async function loadArticles() {
  const container = document.getElementById("article-list");
  if (!state.selectedKeywordId) return;
  container.innerHTML = '<p class="muted">불러오는 중...</p>';

  const url = `/api/articles?keyword_id=${state.selectedKeywordId}`;

  try {
    const articles = await api(url);
    renderArticles(articles);
  } catch (e) {
    container.innerHTML = `<p class="error">${escapeHtml(e.message)}</p>`;
  }
}

const RECENCY_BUCKETS = ["1시간 이내", "3시간 이내", "오늘", "어제 이전"];
const ONE_HOUR_MS = 60 * 60 * 1000;
const THREE_HOURS_MS = 3 * 60 * 60 * 1000;

function groupArticlesByRecency(articles) {
  // articles는 백엔드에서 이미 pub_date 최신순으로 정렬되어 오므로,
  // 버킷 내 삽입 순서를 그대로 유지하면 재정렬 없이 최신 기사가 먼저 온다.
  const now = new Date();
  const buckets = new Map(RECENCY_BUCKETS.map((label) => [label, []]));

  for (const article of articles) {
    const date = new Date(article.pub_date);
    if (isNaN(date.getTime())) continue;

    const diffMs = now - date;
    const isToday = date.toDateString() === now.toDateString();

    let label;
    if (diffMs <= ONE_HOUR_MS) label = "1시간 이내";
    else if (diffMs <= THREE_HOURS_MS) label = "3시간 이내";
    else if (isToday) label = "오늘";
    else label = "어제 이전";

    buckets.get(label).push(article);
  }
  return buckets;
}

function formatTime(pubDate) {
  const date = new Date(pubDate);
  if (isNaN(date.getTime())) return pubDate || "-";
  return date.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
}

function renderArticles(articles) {
  const container = document.getElementById("article-list");
  container.innerHTML = "";
  if (articles.length === 0) {
    container.innerHTML = '<p class="muted">아직 수집된 뉴스가 없습니다. \'지금 업데이트\'를 눌러보세요.</p>';
    return;
  }

  const buckets = groupArticlesByRecency(articles);
  for (const [label, bucketArticles] of buckets) {
    if (bucketArticles.length === 0) continue;

    const timeSection = document.createElement("section");
    timeSection.className = "time-block";

    const timeTitle = document.createElement("h2");
    timeTitle.className = "time-title";
    timeTitle.innerHTML = `${label} <span class="count">${bucketArticles.length}건</span>`;
    timeSection.appendChild(timeTitle);

    const grid = document.createElement("div");
    grid.className = "card-grid";
    for (const a of bucketArticles) {
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML = `
        <a href="${a.link}" target="_blank" rel="noopener noreferrer">${escapeHtml(a.title)}</a>
        <p class="desc">${escapeHtml(a.description || "")}</p>
        <p class="meta">${formatTime(a.pub_date)}</p>
      `;
      grid.appendChild(card);
    }
    timeSection.appendChild(grid);

    container.appendChild(timeSection);
  }
}

async function searchStockSuggestions(query) {
  const list = document.getElementById("stock-suggestions");
  if (!query.trim()) {
    state.suggestions = [];
    list.hidden = true;
    list.innerHTML = "";
    return;
  }

  try {
    state.suggestions = await api(`/api/stocks/search?q=${encodeURIComponent(query)}`);
  } catch (e) {
    state.suggestions = [];
  }
  renderStockSuggestions();
}

function renderStockSuggestions() {
  const list = document.getElementById("stock-suggestions");
  list.innerHTML = "";

  if (state.suggestions.length === 0) {
    list.hidden = true;
    return;
  }

  for (const item of state.suggestions) {
    const li = document.createElement("li");
    li.className = "suggestion-row";
    li.title = "더블클릭하면 바로 추가됩니다";

    const info = document.createElement("div");
    info.className = "suggestion-info";
    info.innerHTML = `<span class="suggestion-name">${escapeHtml(item.name)}</span>
      <span class="suggestion-code">${escapeHtml(item.code)} · ${escapeHtml(item.market)}</span>`;

    const addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.className = "suggestion-add";
    addBtn.textContent = "추가";
    addBtn.onclick = (event) => {
      event.stopPropagation();
      addStock(item);
    };

    li.appendChild(info);
    li.appendChild(addBtn);
    li.ondblclick = () => addStock(item);
    list.appendChild(li);
  }
  list.hidden = false;
}

async function addStock(item) {
  const errorEl = document.getElementById("keyword-error");
  errorEl.textContent = "";

  try {
    await api("/api/keywords", {
      method: "POST",
      body: JSON.stringify({ keyword: item.code }),
    });
    await loadKeywords();
  } catch (e) {
    errorEl.textContent = e.message;
  }
}

async function deleteKeyword(id) {
  await api(`/api/keywords/${id}`, { method: "DELETE" });
  if (state.selectedKeywordId === id) {
    state.selectedKeywordId = null;
  }
  await loadKeywords();
}

async function triggerSync() {
  const button = document.getElementById("sync-button");
  const messageEl = document.getElementById("sync-message");
  button.disabled = true;
  messageEl.textContent = "네이버 뉴스를 수집하는 중...";

  try {
    const result = await api("/api/sync", { method: "POST" });
    const summary = Object.entries(result.per_keyword_new_count)
      .map(([kw, count]) => `${kw} ${count}건`)
      .join(", ");
    let message = `업데이트 완료! 신규 뉴스: ${summary || "없음"}`;
    if (result.excluded_by_outlet > 0) {
      message += ` (허용 목록 외 언론사 제외: ${result.excluded_by_outlet}건)`;
    }
    if (result.failed_keywords.length > 0) {
      message += ` (실패: ${result.failed_keywords.join(", ")})`;
    }
    messageEl.textContent = message;
    await loadLastSync();
    await loadStockPanel();
    await loadArticles();
  } catch (e) {
    messageEl.textContent = `업데이트 실패: ${e.message}`;
  } finally {
    button.disabled = false;
  }
}

async function loadLastSync() {
  const status = await api("/api/status");
  const el = document.getElementById("last-sync");
  el.textContent = status.last_sync_at
    ? `마지막 업데이트: ${status.last_sync_at}`
    : "아직 업데이트된 적이 없습니다.";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

document.getElementById("search-button").addEventListener("click", () => {
  searchStockSuggestions(document.getElementById("new-keyword-input").value);
});
document.getElementById("sync-button").addEventListener("click", triggerSync);
document.getElementById("login-form").addEventListener("submit", submitLogin);

document.getElementById("new-keyword-input").addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    searchStockSuggestions(event.target.value);
  }
});

document.addEventListener("click", (event) => {
  const searchForm = document.getElementById("add-keyword-form");
  if (searchForm && !searchForm.contains(event.target)) {
    document.getElementById("stock-suggestions").hidden = true;
  }
});

checkAuthAndInit();
