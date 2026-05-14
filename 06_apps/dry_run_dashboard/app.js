const data = window.DRY_RUN_DASHBOARD_DATA || {
  approvals: { pending: 0, approved: 0, rejected: 0 },
  approval_risk: { counts: { critical: 0, high: 0, medium: 0, low: 0 }, top: [] },
  approval_items: [],
  approval_priority_queue: [],
  execution_artifacts: [],
  reports: { total_reports: 0, approval_files: 0, meetings: 0 },
  dry_runs: { smartstore: 0, naver_ads: 0, instagram: 0, schemas: 0 },
  apps: [],
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

document.querySelector("#reportCount").textContent = data.reports.total_reports;
document.querySelector("#approvalCount").textContent = data.reports.approval_files;
document.querySelector("#meetingCount").textContent = data.reports.meetings;
document.querySelector("#schemaCount").textContent = data.dry_runs.schemas;
document.querySelector("#highRiskCount").textContent =
  (data.approval_risk?.counts?.critical || 0) + (data.approval_risk?.counts?.high || 0);

const approvalLabels = [
  ["대기", data.approvals.pending],
  ["승인", data.approvals.approved],
  ["반려", data.approvals.rejected],
];

document.querySelector("#approvalBars").innerHTML = approvalLabels.map(([label, value]) => `
  <div class="bar"><span>${label}</span><strong>${value}</strong></div>
`).join("");

const riskLabels = [
  ["매우 높음", data.approval_risk?.counts?.critical || 0, "critical"],
  ["높음", data.approval_risk?.counts?.high || 0, "high"],
  ["보통", data.approval_risk?.counts?.medium || 0, "medium"],
  ["낮음", data.approval_risk?.counts?.low || 0, "low"],
];

document.querySelector("#riskBars").innerHTML = riskLabels.map(([label, value, level]) => `
  <div class="bar risk-${level}"><span>${label}</span><strong>${value}</strong></div>
`).join("");

const dryRunLabels = [
  ["스마트스토어", data.dry_runs.smartstore],
  ["네이버광고", data.dry_runs.naver_ads],
  ["인스타그램", data.dry_runs.instagram],
  ["스키마", data.dry_runs.schemas],
];

document.querySelector("#dryRunList").innerHTML = dryRunLabels.map(([label, value]) => `
  <div class="row"><span>${label}</span><strong>${value}</strong></div>
`).join("");

function renderApprovalDetail(index = 0) {
  const items = data.approval_items || [];
  const item = items[index];
  if (!item) {
    document.querySelector("#approvalDetail").innerHTML = `<p class="empty-state">승인 파일 없음</p>`;
    return;
  }
  document.querySelectorAll(".approval-detail-row").forEach((row, rowIndex) => {
    row.classList.toggle("selected", rowIndex === index);
  });
  document.querySelector("#approvalDetail").innerHTML = `
    <strong>${escapeHtml(item.title)}</strong>
    <dl>
      <div><dt>상태</dt><dd>${escapeHtml(item.status_label)}</dd></div>
      <div><dt>위험도</dt><dd><span class="risk-pill risk-${escapeHtml(item.risk_level)}">${escapeHtml(item.risk_label)} · ${escapeHtml(item.risk_score)}점</span></dd></div>
      <div><dt>파일</dt><dd>${escapeHtml(item.file_name)}</dd></div>
      <div><dt>수정 시각</dt><dd>${escapeHtml(item.modified_at)}</dd></div>
      <div><dt>결정 시각</dt><dd>${escapeHtml(item.decided_at)}</dd></div>
      <div><dt>사유</dt><dd>${escapeHtml(item.reason)}</dd></div>
      <div><dt>경로</dt><dd>${escapeHtml(item.path)}</dd></div>
    </dl>
  `;
}

const approvalItems = data.approval_items || [];
document.querySelector("#approvalDetailList").innerHTML = approvalItems.length
  ? approvalItems.map((item, index) => `
      <button class="approval-detail-row" type="button" data-index="${index}">
        <span>${escapeHtml(item.title)}</span>
        <strong class="risk-pill risk-${escapeHtml(item.risk_level)}">${escapeHtml(item.risk_label)}</strong>
      </button>
    `).join("")
  : `<p class="empty-state">승인 파일 없음</p>`;

document.querySelectorAll(".approval-detail-row").forEach((button) => {
  button.addEventListener("click", () => renderApprovalDetail(Number(button.dataset.index)));
});
renderApprovalDetail(0);

const priorityQueue = data.approval_priority_queue || [];
document.querySelector("#priorityQueueList").innerHTML = priorityQueue.length
  ? priorityQueue.map((item) => `
      <div class="priority-row risk-${escapeHtml(item.level)}">
        <strong>${escapeHtml(item.rank)}. ${escapeHtml(item.level_label)} · ${escapeHtml(item.score)}점</strong>
        <span>${escapeHtml(item.file_name)}</span>
        <em>${escapeHtml(item.next_step)}</em>
      </div>
    `).join("")
  : `<p class="empty-state">실행 검토 큐 없음</p>`;

const executionArtifacts = data.execution_artifacts || [];
document.querySelector("#executionArtifactList").innerHTML = executionArtifacts.length
  ? executionArtifacts.map((item) => `
      <a class="row app-row" href="${escapeHtml(item.href)}">
        <span>${escapeHtml(item.kind)}<br>${escapeHtml(item.title)}</span>
        <strong>${escapeHtml(item.modified_at)}</strong>
      </a>
    `).join("")
  : `<p class="empty-state">실행 전 자료 없음</p>`;

document.querySelector("#appList").innerHTML = data.apps.map((app) => `
  <a class="row app-row" href="${escapeHtml(app.href || app.path)}">
    <span>${escapeHtml(app.name)}<br>${escapeHtml(app.path)}</span>
    <strong>${escapeHtml(app.status)}</strong>
  </a>
`).join("");
