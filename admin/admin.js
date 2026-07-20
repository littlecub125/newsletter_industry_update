// 로컬 관리자 페이지 프론트엔드. 빌드 도구 없이 순수 JS, fetch API만 사용.

let allArticles = [];
let validIndustries = [];
let autoApproveRules = {};
let selectedIndex = null;
let selectedIndices = new Set(); // 일괄 승인용 다중 선택 (index 기준)

const listEl = document.getElementById("article-list");
const editorEl = document.getElementById("editor-panel");
const summaryBarEl = document.getElementById("summary-bar");
const filterIndustryEl = document.getElementById("filter-industry");
const filterStatusEl = document.getElementById("filter-status");
const filterInvalidEl = document.getElementById("filter-invalid");
const filterAutoEl = document.getElementById("filter-auto");
const filterImpactMinEl = document.getElementById("filter-impact-min");
const filterImpactMaxEl = document.getElementById("filter-impact-max");
const sortByEl = document.getElementById("sort-by");
const selectAllEl = document.getElementById("select-all-checkbox");
const selectedCountEl = document.getElementById("selected-count");
const bulkStatusEl = document.getElementById("bulk-status");

async function loadArticles() {
  summaryBarEl.textContent = "불러오는 중...";
  const res = await fetch("/api/articles");
  const data = await res.json();
  allArticles = data.articles;
  validIndustries = data.valid_industries;
  autoApproveRules = data.auto_approve_rules || {};
  // 필터 결과에 없는 index는 선택에서 제거 (기사 자체가 사라졌을 수 있으므로)
  const stillExists = new Set(allArticles.map(a => a.index));
  selectedIndices = new Set([...selectedIndices].filter(i => stillExists.has(i)));
  populateIndustryFilter();
  renderSummary();
  renderList();
  updateSelectedCount();
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
  const autoPassed = allArticles.filter(a => a.auto_approve && a.auto_approve.passed).length;
  const manual = allArticles.filter(a => a.approval_source === "manual").length;
  const threshold = autoApproveRules.min_impact_score;
  summaryBarEl.textContent =
    `전체 ${total}건 / 승인 ${approved}건(자동 ${allArticles.filter(a => a.approved && a.approval_source === "auto_rule").length}건 + 수동 ${allArticles.filter(a => a.approved && a.approval_source === "manual").length}건) / ` +
    `미승인 ${total - approved}건 / industries 오류 ${invalid}건 / ` +
    `자동승인 규칙 통과 ${autoPassed}건${threshold !== undefined ? ` (impact_score>=${threshold} 등)` : ""} / 사람이 직접 판단한 건 ${manual}건`;
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

  const invalidFilter = filterInvalidEl.value;
  if (invalidFilter === "yes") items = items.filter(a => a.invalid_industries.length > 0);
  else if (invalidFilter === "no") items = items.filter(a => a.invalid_industries.length === 0);

  const autoFilter = filterAutoEl.value;
  if (autoFilter === "pass") items = items.filter(a => a.auto_approve && a.auto_approve.passed);
  else if (autoFilter === "fail") items = items.filter(a => a.auto_approve && !a.auto_approve.passed);

  const impactMin = filterImpactMinEl.value !== "" ? Number(filterImpactMinEl.value) : null;
  const impactMax = filterImpactMaxEl.value !== "" ? Number(filterImpactMaxEl.value) : null;
  if (impactMin !== null) {
    items = items.filter(a => (a.tagged.impact_score ?? -Infinity) >= impactMin);
  }
  if (impactMax !== null) {
    items = items.filter(a => (a.tagged.impact_score ?? Infinity) <= impactMax);
  }

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
    if (a.approved) {
      badges.push(`<span class="badge source">${a.approval_source === "manual" ? "수동" : "자동"}</span>`);
    }
    if (a.invalid_industries.length > 0) {
      badges.push(`<span class="badge invalid">industries 오류: ${a.invalid_industries.join(", ")}</span>`);
    }
    if (a.auto_approve && !a.auto_approve.passed) {
      badges.push(`<span class="badge fail" title="${escapeAttr(a.auto_approve.reasons.join(" / "))}">자동승인 미통과: ${escapeHtml(a.auto_approve.reasons.join(" / "))}</span>`);
    }

    const checked = selectedIndices.has(a.index) ? "checked" : "";

    li.innerHTML = `
      <label class="item-select" title="일괄 처리 대상으로 선택">
        <input type="checkbox" class="item-checkbox" data-index="${a.index}" ${checked} />
      </label>
      <div class="item-body">
        <div class="title">${escapeHtml(a.title)}</div>
        <div class="meta">
          <span>${escapeHtml((a.tagged.industries || []).join(", ") || "(없음)")}</span>
          <span>impact ${a.tagged.impact_score ?? "-"}</span>
          <span>${escapeHtml(a.source || "")}</span>
          ${badges.join("")}
        </div>
      </div>
    `;
    li.querySelector(".item-body").addEventListener("click", () => selectArticle(a.index));
    li.querySelector(".item-checkbox").addEventListener("change", (e) => {
      toggleSelection(a.index, e.target.checked);
    });
    listEl.appendChild(li);
  }

  syncSelectAllCheckbox(items);
}

function toggleSelection(index, checked) {
  if (checked) selectedIndices.add(index);
  else selectedIndices.delete(index);
  updateSelectedCount();
  syncSelectAllCheckbox(getFilteredSorted());
}

function syncSelectAllCheckbox(filteredItems) {
  if (filteredItems.length === 0) {
    selectAllEl.checked = false;
    selectAllEl.indeterminate = false;
    return;
  }
  const selectedCountInFilter = filteredItems.filter(a => selectedIndices.has(a.index)).length;
  selectAllEl.checked = selectedCountInFilter === filteredItems.length;
  selectAllEl.indeterminate = selectedCountInFilter > 0 && selectedCountInFilter < filteredItems.length;
}

function updateSelectedCount() {
  selectedCountEl.textContent = `선택됨: ${selectedIndices.size}건`;
}

selectAllEl.addEventListener("change", () => {
  const items = getFilteredSorted();
  if (selectAllEl.checked) {
    items.forEach(a => selectedIndices.add(a.index));
  } else {
    items.forEach(a => selectedIndices.delete(a.index));
  }
  renderList();
  updateSelectedCount();
});

async function bulkSetApproved(approved) {
  if (selectedIndices.size === 0) {
    bulkStatusEl.textContent = "선택된 기사가 없습니다.";
    return;
  }
  bulkStatusEl.textContent = "처리 중...";
  const res = await fetch("/api/articles/bulk", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ indices: [...selectedIndices], approved }),
  });
  if (!res.ok) {
    bulkStatusEl.textContent = "일괄 처리 실패";
    return;
  }
  const result = await res.json();
  bulkStatusEl.textContent = `${result.updated}건 ${approved ? "승인" : "미승인"} 처리됨`;
  selectedIndices.clear();
  await loadArticles();
  if (selectedIndex !== null) renderEditor();
}

document.getElementById("bulk-approve-btn").addEventListener("click", () => bulkSetApproved(true));
document.getElementById("bulk-unapprove-btn").addEventListener("click", () => bulkSetApproved(false));

document.getElementById("rerun-auto-approve-btn").addEventListener("click", async () => {
  bulkStatusEl.textContent = "자동승인 규칙 재실행 중...";
  const res = await fetch("/api/auto-approve/rerun", { method: "POST" });
  if (!res.ok) {
    bulkStatusEl.textContent = "재실행 실패";
    return;
  }
  const result = await res.json();
  bulkStatusEl.textContent =
    `재실행 완료: 전체 ${result.total}건 중 규칙 통과 ${result.auto_passed}건, ` +
    `검토 필요 ${result.needs_review}건 (승인상태 변경 ${result.changed}건, 사람이 이미 판단한 건은 그대로 유지)`;
  await loadArticles();
});

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

  const autoBlock = article.auto_approve
    ? `<div class="readonly-block ${article.auto_approve.passed ? "auto-pass" : "auto-fail"}">
        자동승인 규칙: ${article.auto_approve.passed ? "통과" : "미통과"}
        ${article.approval_source ? ` / 현재 승인 근거: ${article.approval_source === "manual" ? "사람이 직접 승인/반려" : "규칙 자동승인"}` : " / 아직 승인되지 않음"}
        ${!article.auto_approve.passed && article.auto_approve.reasons.length > 0
          ? `<ul class="reason-list">${article.auto_approve.reasons.map(r => `<li>${escapeHtml(r)}</li>`).join("")}</ul>`
          : ""}
      </div>`
    : "";

  editorEl.innerHTML = `
    <h2>${escapeHtml(article.title)}</h2>
    <div class="readonly-block">
      출처: ${escapeHtml(article.source || "")} /
      발행: ${escapeHtml(article.published_at || "-")} /
      수집: ${escapeHtml(article.collected_at || "-")}<br/>
      <a href="${escapeAttr(article.link)}" target="_blank" rel="noopener">원문 링크 열기</a>
    </div>

    ${autoBlock}

    <div class="approve-row">
      <input type="checkbox" id="approved-checkbox" ${article.approved ? "checked" : ""} />
      <label for="approved-checkbox"><strong>승인 (approved)</strong> -- 체크해야 news.json/뉴스레터 초안에 포함됩니다. 여기서 저장하면 승인 근거가 "사람이 직접 판단(manual)"으로 기록되어, 이후 자동승인 규칙 재실행에도 바뀌지 않습니다.</label>
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
filterInvalidEl.addEventListener("change", renderList);
filterAutoEl.addEventListener("change", renderList);
filterImpactMinEl.addEventListener("input", renderList);
filterImpactMaxEl.addEventListener("input", renderList);
sortByEl.addEventListener("change", renderList);
document.getElementById("refresh-btn").addEventListener("click", loadArticles);

loadArticles();
