// 로컬 관리자 페이지 프론트엔드. 빌드 도구 없이 순수 JS, fetch API만 사용.

let allArticles = [];
let validIndustries = [];
let selectedIndex = null;

const listEl = document.getElementById("article-list");
const editorEl = document.getElementById("editor-panel");
const summaryBarEl = document.getElementById("summary-bar");
const filterIndustryEl = document.getElementById("filter-industry");
const filterStatusEl = document.getElementById("filter-status");
const sortByEl = document.getElementById("sort-by");

async function loadArticles() {
  summaryBarEl.textContent = "불러오는 중...";
  const res = await fetch("/api/articles");
  const data = await res.json();
  allArticles = data.articles;
  validIndustries = data.valid_industries;
  populateIndustryFilter();
  renderSummary();
  renderList();
}

function populateIndustryFilter() {
  const current = filterIndustryEl.value;
  filterIndustryEl.innerHTML = '<option value="">전체</option>' +
    validIndustries.map(id => `<option value="${id}">${id}</option>`).join("");
  filterIndustryEl.value = current;
}

function renderSummary() {
  const total = allArticles.length;
  const approved = allArticles.filter(a => a.approved).length;
  const invalid = allArticles.filter(a => a.invalid_industries.length > 0).length;
  summaryBarEl.textContent =
    `전체 ${total}건 / 승인 ${approved}건 / 미승인 ${total - approved}건 / industries 오류 ${invalid}건`;
}

function getFilteredSorted() {
  let items = [...allArticles];

  const indFilter = filterIndustryEl.value;
  if (indFilter) {
    items = items.filter(a => (a.tagged.industries || []).includes(indFilter));
  }

  const statusFilter = filterStatusEl.value;
  if (statusFilter === "approved") items = items.filter(a => a.approved);
  else if (statusFilter === "unapproved") items = items.filter(a => !a.approved);
  else if (statusFilter === "invalid") items = items.filter(a => a.invalid_industries.length > 0);

  const sortBy = sortByEl.value;
  if (sortBy === "impact_desc") {
    items.sort((a, b) => (b.tagged.impact_score || 0) - (a.tagged.impact_score || 0));
  } else if (sortBy === "impact_asc") {
    items.sort((a, b) => (a.tagged.impact_score || 0) - (b.tagged.impact_score || 0));
  } else if (sortBy === "index_desc") {
    items.sort((a, b) => b.index - a.index);
  }

  return items;
}

function renderList() {
  const items = getFilteredSorted();
  listEl.innerHTML = "";

  for (const a of items) {
    const li = document.createElement("li");
    li.className = "article-item" + (a.index === selectedIndex ? " selected" : "");
    li.dataset.index = a.index;

    const badges = [];
    badges.push(`<span class="badge ${a.approved ? "approved" : "unapproved"}">${a.approved ? "승인됨" : "미승인"}</span>`);
    if (a.invalid_industries.length > 0) {
      badges.push(`<span class="badge invalid">industries 오류: ${a.invalid_industries.join(", ")}</span>`);
    }

    li.innerHTML = `
      <div class="title">${escapeHtml(a.title)}</div>
      <div class="meta">
        <span>${escapeHtml((a.tagged.industries || []).join(", ") || "(없음)")}</span>
        <span>impact ${a.tagged.impact_score ?? "-"}</span>
        <span>${escapeHtml(a.source || "")}</span>
        ${badges.join("")}
      </div>
    `;
    li.addEventListener("click", () => selectArticle(a.index));
    listEl.appendChild(li);
  }
}

function selectArticle(index) {
  selectedIndex = index;
  renderList();
  renderEditor();
}

function renderEditor() {
  const article = allArticles.find(a => a.index === selectedIndex);
  if (!article) {
    editorEl.innerHTML = '<p class="placeholder">왼쪽에서 기사를 선택하세요.</p>';
    return;
  }

  const t = article.tagged;
  const invalidWarning = article.invalid_industries.length > 0
    ? `<p class="warning">⚠ 유효하지 않은 industry id: ${article.invalid_industries.join(", ")}
       (config/industries.json의 id와 다름 -- group_by_industry()에서 조용히 누락됩니다. 아래에서 고쳐주세요.)</p>`
    : "";

  editorEl.innerHTML = `
    <h2>${escapeHtml(article.title)}</h2>
    <div class="readonly-block">
      출처: ${escapeHtml(article.source || "")} /
      발행: ${escapeHtml(article.published_at || "-")} /
      수집: ${escapeHtml(article.collected_at || "-")}<br/>
      <a href="${escapeAttr(article.link)}" target="_blank" rel="noopener">원문 링크 열기</a>
    </div>

    <div class="approve-row">
      <input type="checkbox" id="approved-checkbox" ${article.approved ? "checked" : ""} />
      <label for="approved-checkbox"><strong>승인 (approved)</strong> -- 체크해야 news.json/뉴스레터 초안에 포함됩니다.</label>
    </div>

    <div class="field">
      <label for="industries-input">industries (쉼표로 구분, config/industries.json의 id만 유효)</label>
      <input type="text" id="industries-input" value="${escapeAttr((t.industries || []).join(", "))}" />
      ${invalidWarning}
    </div>

    <div class="field">
      <label for="summary-input">summary</label>
      <textarea id="summary-input">${escapeHtml(t.summary || "")}</textarea>
    </div>

    <div class="field">
      <label for="why-input">why_it_matters</label>
      <textarea id="why-input">${escapeHtml(t.why_it_matters || "")}</textarea>
    </div>

    <div class="readonly-block">
      event_type: ${escapeHtml(t.event_type || "-")} /
      sentiment: ${escapeHtml(t.sentiment || "-")} /
      impact_score: ${t.impact_score ?? "-"} /
      companies: ${escapeHtml((t.companies || []).join(", ") || "-")}
    </div>

    <div class="actions">
      <button id="save-btn">저장</button>
      <span id="save-status"></span>
    </div>
  `;

  document.getElementById("save-btn").addEventListener("click", () => saveArticle(article.index));
}

async function saveArticle(index) {
  const statusEl = document.getElementById("save-status");
  const industries = document.getElementById("industries-input").value
    .split(",").map(s => s.trim()).filter(Boolean);
  const summary = document.getElementById("summary-input").value;
  const whyItMatters = document.getElementById("why-input").value;
  const approved = document.getElementById("approved-checkbox").checked;

  statusEl.textContent = "저장 중...";

  const res = await fetch(`/api/articles/${index}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      industries,
      summary,
      why_it_matters: whyItMatters,
      approved,
    }),
  });

  if (!res.ok) {
    statusEl.textContent = "저장 실패";
    return;
  }

  const result = await res.json();
  statusEl.textContent = "저장됨";
  if (result.invalid_industries && result.invalid_industries.length > 0) {
    statusEl.textContent += ` (여전히 유효하지 않은 industries: ${result.invalid_industries.join(", ")})`;
  }

  await loadArticles();
  selectArticle(index);
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function escapeAttr(str) {
  return (str ?? "").replace(/"/g, "&quot;");
}

filterIndustryEl.addEventListener("change", renderList);
filterStatusEl.addEventListener("change", renderList);
sortByEl.addEventListener("change", renderList);
document.getElementById("refresh-btn").addEventListener("click", loadArticles);

loadArticles();
