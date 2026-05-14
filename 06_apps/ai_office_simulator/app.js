const office = document.querySelector("#office");
const agentList = document.querySelector("#agentList");
const taskQueue = document.querySelector("#taskQueue");
const riskQueue = document.querySelector("#riskQueue");
const riskQueueSummary = document.querySelector("#riskQueueSummary");
const connectionStageList = document.querySelector("#connectionStageList");
const connectionStageSummary = document.querySelector("#connectionStageSummary");
const eventLog = document.querySelector("#eventLog");
const approvalList = document.querySelector("#approvalList");
const toggleRun = document.querySelector("#toggleRun");
const focusTeam = document.querySelector("#focusTeam");
const speedRange = document.querySelector("#speedRange");
const scenarioSelect = document.querySelector("#scenarioSelect");
const clock = document.querySelector("#clock");
const feedState = document.querySelector("#feedState");
const chatStatus = document.querySelector("#chatStatus");
const chatMessages = document.querySelector("#chatMessages");
const chatForm = document.querySelector("#chatForm");
const chatInput = document.querySelector("#chatInput");
const chatSubmit = document.querySelector("#chatSubmit");

const statusLabel = {
  active: "업무중",
  review: "검수",
  idle: "대기",
  blocked: "막힘",
};

const connectionStatusLabel = {
  ready: "준비됨",
  partial: "일부 준비",
  not_configured: "설정 필요",
  not_ready: "대기",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

const scenarios = {
  mvp: [
    "MVP 명령 회귀 테스트",
    "승인 대기 파일 점검",
    "실행계획 보고서 작성",
    "작업 보드 갱신",
  ],
  ads: [
    "네이버광고 ROAS 분류",
    "낭비 키워드 후보 검토",
    "문구와 랜딩 일치 점검",
    "승인 파일 위험 요소 정리",
  ],
  content: [
    "고스틱 후킹 문구 생성",
    "릴스 초반 2초 구성",
    "이미지 편집 지시서 정리",
    "과장 표현 검수",
  ],
  simulator: [
    "AI 직원 이동 상태 렌더링",
    "업무중/대기 상태판 업데이트",
    "활동 로그 생성",
    "모바일 화면 배치 점검",
  ],
};

const agents = [
  { id: "ceo", name: "CEO AI", role: "ceo", x: 15, y: 27, desk: [13, 29], task: "우선순위 조율" },
  { id: "data", name: "데이터 AI", role: "data", x: 40, y: 27, desk: [38, 29], task: "CSV 분석" },
  { id: "marketing", name: "마케팅 AI", role: "marketing", x: 62, y: 27, desk: [63, 29], task: "광고 문구" },
  { id: "sns", name: "SNS AI", role: "sns", x: 80, y: 27, desk: [82, 29], task: "릴스 대본" },
  { id: "image", name: "이미지 AI", role: "image", x: 18, y: 54, desk: [18, 56], task: "썸네일 구성" },
  { id: "store", name: "스마트스토어 AI", role: "store", x: 43, y: 54, desk: [43, 56], task: "상품 정보 점검" },
  { id: "ads", name: "네이버광고 AI", role: "ads", x: 67, y: 54, desk: [68, 56], task: "키워드 분류" },
  { id: "app", name: "앱개발 AI", role: "app", x: 82, y: 54, desk: [82, 56], task: "시뮬레이터 UI" },
  { id: "qa", name: "검수 AI", role: "qa", x: 50, y: 80, desk: [50, 82], task: "위험 표현 확인" },
];

const paths = [
  [12, 28], [27, 28], [42, 28], [58, 28], [74, 28], [86, 28],
  [14, 55], [30, 55], [47, 55], [64, 55], [80, 55],
  [22, 80], [40, 80], [58, 80], [76, 80],
];

let running = true;
let tickMs = 1800;
let eventCounter = 0;
let latestFeedKey = "";
let latestExternalFeed = window.AI_OFFICE_FEED || null;
let chatBusy = false;

function pick(items) {
  return items[Math.floor(Math.random() * items.length)];
}

function weightedStatus(agent) {
  if (agent.id === "qa") return pick(["review", "review", "active", "idle"]);
  if (agent.id === "ceo") return pick(["active", "active", "review", "idle"]);
  return pick(["active", "active", "active", "review", "idle", "blocked"]);
}

function createAgent(agent) {
  const el = document.createElement("div");
  el.className = "agent";
  el.dataset.agentId = agent.id;
  el.dataset.role = agent.role;
  el.dataset.status = "active";
  el.style.left = `${agent.x}%`;
  el.style.top = `${agent.y}%`;
  el.style.transitionDuration = `${tickMs}ms`;
  el.innerHTML = `
    <span class="status-badge"></span>
    <span class="agent-head"></span>
    <span class="agent-body"></span>
    <span class="agent-name">${agent.name}</span>
  `;
  office.appendChild(el);
  agent.el = el;
}

function createAgentCard(agent) {
  const card = document.createElement("div");
  card.className = "agent-card";
  card.dataset.agentId = agent.id;
  card.dataset.status = "active";
  card.innerHTML = `
    <span class="card-dot"></span>
    <span class="card-name">
      <strong>${agent.name}</strong>
      <span>${agent.task}</span>
    </span>
    <span class="card-state">업무중</span>
  `;
  agentList.appendChild(card);
  agent.card = card;
}

function renderQueue() {
  const tasks = scenarios[scenarioSelect.value];
  taskQueue.innerHTML = tasks.map((task) => `<li>${escapeHtml(task)}</li>`).join("");
}

// ── 채팅 영속화 (localStorage) ─────────
const CHAT_STORAGE_KEY = "ai_company.simulator.chat.v1";
const CHAT_HISTORY_LIMIT = 60;
let chatHistory = [];

function loadChatHistory() {
  try {
    const raw = localStorage.getItem(CHAT_STORAGE_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr.slice(-CHAT_HISTORY_LIMIT) : [];
  } catch (e) { return []; }
}
function saveChatHistory() {
  try {
    localStorage.setItem(
      CHAT_STORAGE_KEY,
      JSON.stringify(chatHistory.slice(-CHAT_HISTORY_LIMIT))
    );
  } catch (e) {}
}
function clearChatHistory() {
  chatHistory = [];
  try { localStorage.removeItem(CHAT_STORAGE_KEY); } catch (e) {}
  if (chatMessages) chatMessages.innerHTML = "";
}

function appendChatMessage(role, text, meta = "", options) {
  const silent = !!(options && options.silent);
  const message = document.createElement("div");
  message.className = `chat-message ${role}`;
  const safeMeta = meta ? `<small>${escapeHtml(meta)}</small>` : "";
  message.innerHTML = `<span>${escapeHtml(text)}</span>${safeMeta}`;
  chatMessages.appendChild(message);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  if (!silent) {
    chatHistory.push({ role, text, meta, t: Date.now() });
    if (chatHistory.length > CHAT_HISTORY_LIMIT) {
      chatHistory.splice(0, chatHistory.length - CHAT_HISTORY_LIMIT);
    }
    saveChatHistory();
  }
}

function restoreChatHistory() {
  chatHistory = loadChatHistory();
  if (chatHistory.length === 0) return false;
  for (const m of chatHistory) {
    appendChatMessage(m.role || "bot", m.text || "", m.meta || "", { silent: true });
  }
  return true;
}

function summarizeOutput(output) {
  if (!output) return "결과 파일을 생성했습니다.";
  const lines = String(output).split(/\r?\n/).filter(Boolean);
  const saved = lines.filter((line) => line.includes("저장:") || line.includes("위치"));
  if (saved.length) return saved.slice(-4).join("\n");
  return lines.slice(0, 7).join("\n");
}

async function sendChat(message) {
  if (!message.trim() || chatBusy) return;
  chatBusy = true;
  chatStatus.textContent = "실행중";
  chatSubmit.disabled = true;
  chatInput.disabled = true;
  appendChatMessage("user", message);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await response.json();
    const command = data.command_line || (Array.isArray(data.command) ? `python -m ai_company.main ${data.command.join(" ")}` : "");
    if (data.routing) {
      const r = data.routing;
      const runners = Array.isArray(r.runners_up) && r.runners_up.length
        ? ` · 후순위 ${r.runners_up.join(", ")}`
        : "";
      appendChatMessage(
        "router",
        `라우터 1순위: ${r.primary_name} (${r.primary_role}) · 점수 ${r.score}${runners}`,
        data.intent ? `의도: ${data.intent}` : ""
      );
    }
    const reply = data.ok
      ? `${data.label || "AI 회사 작업"} 완료\n${summarizeOutput(data.output)}`
      : data.reply || "실행하지 못했습니다.";
    appendChatMessage(data.ok ? "bot" : "warn", reply, command);
    if (data.approval_path) {
      appendChatMessage("warn", `승인 대기 파일 생성: ${data.approval_path}`, "09_approval 폴더 확인");
    }
    reloadActivityFeed();
  } catch (error) {
    appendChatMessage(
      "warn",
      "채팅 서버가 준비되지 않았습니다. scripts/start_local_viewer.ps1로 다시 열어주세요.",
      "powershell -ExecutionPolicy Bypass -File .\\scripts\\start_local_viewer.ps1 -Restart"
    );
  } finally {
    chatBusy = false;
    chatStatus.textContent = "대기";
    chatSubmit.disabled = false;
    chatInput.disabled = false;
    chatInput.focus();
  }
}

function renderRiskQueue(feed) {
  const risk = feed?.risk_queue;
  const counts = risk?.counts || { critical: 0, high: 0, medium: 0, low: 0 };
  const urgent = (counts.critical || 0) + (counts.high || 0);
  riskQueueSummary.textContent = `높은 위험 ${urgent}건 / 보통 ${counts.medium || 0}건`;

  const queue = risk?.queue || [];
  if (!queue.length) {
    riskQueue.innerHTML = `<div class="risk-queue-item risk-low"><strong>검토 큐 없음</strong><span>승인 위험도 데이터 대기중</span></div>`;
    return;
  }

  riskQueue.innerHTML = queue.map((item) => `
    <div class="risk-queue-item risk-${escapeHtml(item.level)}">
      <strong>${escapeHtml(item.rank)}. ${escapeHtml(item.level_label)} · ${escapeHtml(item.score)}점</strong>
      <span title="${escapeHtml(item.file_name)}">${escapeHtml(item.file_name)}</span>
      <em>${escapeHtml(item.gate)}</em>
    </div>
  `).join("");
}

function renderConnectionStages(feed) {
  const stages = feed?.connection_stages;
  const counts = stages?.counts || { ready: 0, partial: 0, not_configured: 0, not_ready: 0 };
  const configured = (counts.ready || 0) + (counts.partial || 0);
  connectionStageSummary.textContent = `준비 ${configured}/5 · 승인 ${stages?.approval_required || 0}건`;

  const items = stages?.items || [];
  if (!items.length) {
    connectionStageList.innerHTML = `
      <div class="connection-stage-item stage-not_ready">
        <strong>연결 상태 대기중</strong>
        <span>CLI 피드가 생성되면 4~8단계 상태가 표시됩니다.</span>
      </div>
    `;
    return;
  }

  connectionStageList.innerHTML = items.map((stage) => `
    <div class="connection-stage-item stage-${escapeHtml(stage.status)}">
      <strong>${escapeHtml(stage.stage)}단계 · ${escapeHtml(stage.name)}</strong>
      <span>${escapeHtml(stage.safe_detail)}</span>
      <em>${escapeHtml(connectionStatusLabel[stage.status] || stage.status)} · ${stage.approval_required_for_real ? "실제 연결 승인 필요" : "로컬 조건부 준비"}</em>
    </div>
  `).join("");
}

function updateCounts() {
  const counts = { active: 0, review: 0, idle: 0, blocked: 0 };
  agents.forEach((agent) => {
    counts[agent.status] += 1;
  });
  document.querySelector("#activeCount").textContent = counts.active;
  document.querySelector("#reviewCount").textContent = counts.review;
  document.querySelector("#idleCount").textContent = counts.idle;
  document.querySelector("#blockedCount").textContent = counts.blocked;
}

function lightDesks() {
  document.querySelectorAll(".desk").forEach((desk) => desk.classList.remove("lit"));
  agents.forEach((agent) => {
    if (agent.status !== "idle") {
      const desk = document.querySelector(`.desk.${agent.role}`);
      if (desk) desk.classList.add("lit");
    }
  });
}

function moveAgent(agent, forceActive = false) {
  const external = latestExternalFeed?.agents?.[agent.id];
  agent.status = external?.status || (forceActive ? "active" : weightedStatus(agent));
  if (external?.task) {
    agent.task = external.task;
    agent.card.querySelector(".card-name span").textContent = external.task;
  }
  const destination = agent.status === "idle" ? agent.desk : pick(paths);
  const driftX = agent.status === "blocked" ? 0 : Math.random() * 2 - 1;
  const driftY = agent.status === "blocked" ? 0 : Math.random() * 2 - 1;
  agent.x = Math.max(6, Math.min(88, destination[0] + driftX));
  agent.y = Math.max(14, Math.min(84, destination[1] + driftY));
  agent.el.dataset.status = agent.status;
  agent.el.style.left = `${agent.x}%`;
  agent.el.style.top = `${agent.y}%`;
  agent.el.style.transitionDuration = `${tickMs}ms`;
  agent.card.dataset.status = agent.status;
  agent.card.querySelector(".card-state").textContent = statusLabel[agent.status];
}

function addEvent(agent) {
  eventCounter += 1;
  const event = document.createElement("div");
  event.className = `event ${agent.status}`;
  event.textContent = `${String(eventCounter).padStart(2, "0")} ${agent.name} - ${statusLabel[agent.status]} - ${agent.task}`;
  eventLog.prepend(event);
  while (eventLog.children.length > 9) {
    eventLog.removeChild(eventLog.lastElementChild);
  }
}

function addExternalEvent(eventData) {
  const key = `${eventData.time}-${eventData.command}-${eventData.status}`;
  if (key === latestFeedKey) return;
  latestFeedKey = key;
  const event = document.createElement("div");
  event.className = `event ${eventData.status}`;
  const duration = typeof eventData.duration_seconds === "number"
    ? ` (${eventData.duration_seconds.toFixed(3)}초)`
    : "";
  event.textContent = `${eventData.time || ""} ${eventData.task || "CLI 작업"} - ${statusLabel[eventData.status] || eventData.status}${duration} - ${eventData.detail || eventData.command}`;
  eventLog.prepend(event);
  while (eventLog.children.length > 9) {
    eventLog.removeChild(eventLog.lastElementChild);
  }
}

function renderApprovals(feed) {
  const approvals = feed?.approvals;
  const counts = approvals?.counts || { pending: 0, approved: 0, rejected: 0 };
  document.querySelector("#approvalPending").textContent = counts.pending || 0;
  document.querySelector("#approvalApproved").textContent = counts.approved || 0;
  document.querySelector("#approvalRejected").textContent = counts.rejected || 0;

  const recent = approvals?.recent || [];
  if (!recent.length) {
    approvalList.innerHTML = `<div class="approval-item"><span>승인 대기 파일 없음</span><strong>대기</strong></div>`;
    return;
  }
  approvalList.innerHTML = recent.map((item) => `
    <div class="approval-item">
      <span title="${escapeHtml(item.file_name)}">${escapeHtml(item.file_name)}</span>
      <strong>${escapeHtml(item.status_label || "대기")}</strong>
    </div>
  `).join("");
}

function applyActivityFeed(feed) {
  if (!feed || !feed.updated_at) {
    feedState.textContent = "CLI 작업 로그 대기중";
    renderApprovals(feed);
    renderRiskQueue(feed);
    renderConnectionStages(feed);
    return;
  }
  latestExternalFeed = feed;
  const updated = new Date(feed.updated_at);
  const ageSeconds = Number.isNaN(updated.getTime()) ? null : Math.round((Date.now() - updated.getTime()) / 1000);
  feedState.textContent = ageSeconds === null
    ? "CLI 작업 로그 연결됨"
    : `CLI 작업 로그 연결됨 - ${ageSeconds}초 전 업데이트`;
  if (Array.isArray(feed.events) && feed.events.length > 0) {
    addExternalEvent(feed.events[feed.events.length - 1]);
  }
  renderApprovals(feed);
  renderRiskQueue(feed);
  renderConnectionStages(feed);
  tick(false);
}

function reloadActivityFeed() {
  const previous = document.querySelector("#activityFeedScript");
  if (previous) previous.remove();
  const script = document.createElement("script");
  script.id = "activityFeedScript";
  script.src = `activity_feed.js?ts=${Date.now()}`;
  script.onload = () => applyActivityFeed(window.AI_OFFICE_FEED);
  script.onerror = () => {
    feedState.textContent = "CLI 작업 로그 파일 없음 - 시뮬레이션 모드";
  };
  document.body.appendChild(script);
}

function updateClock() {
  const now = new Date();
  clock.textContent = now.toLocaleTimeString("ko-KR", { hour12: false });
}

function tick(forceActive = false) {
  if (!running && !forceActive) return;
  agents.forEach((agent) => {
    moveAgent(agent, forceActive);
  });
  const visibleAgent = pick(agents);
  addEvent(visibleAgent);
  updateCounts();
  lightDesks();
  updateClock();
}

function schedule() {
  window.clearInterval(window.officeTimer);
  window.officeTimer = window.setInterval(() => tick(false), tickMs);
}

function setSpeed() {
  const speed = Number(speedRange.value);
  tickMs = Math.round(1800 / speed);
  agents.forEach((agent) => {
    agent.el.style.transitionDuration = `${tickMs}ms`;
  });
  schedule();
}

toggleRun.addEventListener("click", () => {
  running = !running;
  toggleRun.textContent = running ? "일시정지" : "다시 시작";
  if (running) tick(false);
});

focusTeam.addEventListener("click", () => {
  running = true;
  toggleRun.textContent = "일시정지";
  tick(true);
});

speedRange.addEventListener("input", setSpeed);
scenarioSelect.addEventListener("change", () => {
  renderQueue();
  agents.forEach((agent, index) => {
    agent.task = scenarios[scenarioSelect.value][index % scenarios[scenarioSelect.value].length];
    agent.card.querySelector(".card-name span").textContent = agent.task;
  });
  tick(true);
});

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  chatInput.value = "";
  sendChat(message);
});

document.querySelectorAll("[data-chat-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    const prompt = button.dataset.chatPrompt || "";
    chatInput.value = prompt;
    sendChat(prompt);
  });
});

agents.forEach((agent) => {
  createAgent(agent);
  createAgentCard(agent);
});
renderQueue();
applyActivityFeed(window.AI_OFFICE_FEED);
const _chatRestored = restoreChatHistory();
if (!_chatRestored) {
  appendChatMessage("bot", "원하는 일을 말하면 안전한 dry-run 명령으로 실행합니다.", "예: 고스틱 광고 만들어줘");
} else {
  appendChatMessage("bot", `이전 대화 ${chatHistory.length}개 복원됨.`, "채팅 메시지 위 빈 공간 더블클릭 → 초기화");
}
tick(true);
schedule();
window.setInterval(updateClock, 1000);

// 채팅창 상단 빈 공간 더블클릭 → 채팅 내역 초기화
if (chatMessages) {
  chatMessages.addEventListener("dblclick", (e) => {
    // 메시지 자체가 아닌 빈 영역 더블클릭 시에만
    if (e.target !== chatMessages) return;
    if (!confirm("이 채팅 내역을 모두 지울까요? (브라우저에 저장된 기록만 삭제됩니다)")) return;
    clearChatHistory();
    appendChatMessage("bot", "채팅 내역을 초기화했습니다.", "");
  });
}
window.setInterval(reloadActivityFeed, 5000);
