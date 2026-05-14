(() => {
  const STORAGE_KEY = "ai_company.agent_matrix.model_map.v1";
  const FILTER_KEY = "ai_company.agent_matrix.filter.v1";
  const agents = window.AI_COMPANY_AGENTS || [];
  const models = window.AI_COMPANY_MODELS || [];
  const autoMap = window.AI_COMPANY_AUTO_MAP || {};

  const grid = document.getElementById("agentGrid");
  const onlineSummary = document.getElementById("onlineSummary");
  const filterRow = document.getElementById("filterRow");
  const todayLabel = document.getElementById("todayLabel");
  const chatCount = document.getElementById("chatCount");

  let currentFilter = loadFilter();
  let modelMap = loadMap();

  function loadMap() {
    // 신 키 → 구 키 순으로 시도 (마이그레이션)
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
                || localStorage.getItem("ai_company_model_map");
      if (raw) return JSON.parse(raw);
    } catch {}
    const m = {};
    for (const a of agents) m[a.key] = "ollama";
    return m;
  }
  function saveMap() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(modelMap)); } catch {}
  }
  function loadFilter() {
    try {
      const v = localStorage.getItem(FILTER_KEY);
      if (v && ["all", "active", "offline", "open"].includes(v)) return v;
    } catch {}
    return "all";
  }
  function saveFilter() {
    try { localStorage.setItem(FILTER_KEY, currentFilter); } catch {}
  }
  function clearAllMatrixStorage() {
    try {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(FILTER_KEY);
      localStorage.removeItem("ai_company_model_map");
    } catch {}
  }

  function escapeHtml(s) {
    return (s || "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  function renderCounts() {
    const counts = { all: agents.length, active: 0, offline: 0, open: 0 };
    for (const a of agents) {
      if (a.status === "active") counts.active++;
      else if (a.status === "offline") counts.offline++;
      else if (a.status === "open") counts.open++;
    }
    document.getElementById("countAll").textContent = counts.all;
    document.getElementById("countActive").textContent = counts.active;
    document.getElementById("countOffline").textContent = counts.offline;
    document.getElementById("countOpen").textContent = counts.open;
    onlineSummary.textContent = `${counts.active} / ${counts.all} ONLINE`;
  }

  function renderAgents() {
    const filtered = agents.filter((a) => {
      if (currentFilter === "all") return true;
      return a.status === currentFilter;
    });

    grid.innerHTML = filtered.map((a) => {
      const statusBadge =
        a.status === "active" ? `<div class="agent-status active">●</div>`
        : a.status === "offline" ? `<div class="agent-status offline">||</div>`
        : `<div class="agent-status offline">+</div>`;
      const meta = a.status === "offline" ? "OFFLINE"
        : a.status === "open" ? "채용 대기"
        : `모델: ${modelLabel(modelMap[a.key])}`;
      const cls = `agent-card ${a.status}`;
      return `
        <div class="${cls}" style="--card-from:${a.cardFrom};--card-to:${a.cardTo}">
          ${statusBadge}
          <div class="agent-portrait">${a.icon}</div>
          <div>
            <div class="agent-name">${escapeHtml(a.name)}</div>
            <div class="agent-role">${escapeHtml(a.title)}</div>
            <div class="agent-meta">${escapeHtml(meta)}</div>
          </div>
        </div>
      `;
    }).join("");
  }

  function modelLabel(key) {
    const m = models.find((x) => x.key === key);
    return m ? m.label : "기본";
  }

  // 필터 chip 클릭
  filterRow.addEventListener("click", (e) => {
    const btn = e.target.closest(".chip");
    if (!btn) return;
    document.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
    btn.classList.add("active");
    currentFilter = btn.dataset.filter;
    saveFilter();
    renderAgents();
  });

  // 로드된 필터로 시작 chip 동기화
  function syncFilterChips() {
    document.querySelectorAll(".chip").forEach((c) => {
      c.classList.toggle("active", c.dataset.filter === currentFilter);
    });
  }

  // 모달 토글
  function openModal(name) {
    const m = document.getElementById(`modal-${name}`);
    if (!m) return;
    m.hidden = false;
    if (name === "systemDiag") fillSystemInfo();
    if (name === "orchestrator") renderModelMap();
  }
  function closeModals() {
    document.querySelectorAll(".modal").forEach((m) => (m.hidden = true));
  }
  document.querySelectorAll("[data-modal]").forEach((btn) => {
    btn.addEventListener("click", () => openModal(btn.dataset.modal));
  });
  document.addEventListener("click", (e) => {
    if (e.target.dataset && e.target.dataset.close !== undefined) closeModals();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModals();
  });

  // 시스템 진단 채우기
  function fillSystemInfo() {
    const info = document.getElementById("systemInfo");
    const cores = navigator.hardwareConcurrency || "알 수 없음";
    const platform = navigator.platform || "알 수 없음";
    const ua = navigator.userAgent.length > 80
      ? navigator.userAgent.slice(0, 80) + "…"
      : navigator.userAgent;
    const lang = navigator.language || "ko";
    const memEst = navigator.deviceMemory ? `${navigator.deviceMemory}GB+` : "감지 불가";
    const screenInfo = `${screen.width}×${screen.height}`;
    const ts = new Date().toLocaleString("ko-KR");

    info.innerHTML = `
      <div class="info-cell"><b>OS Platform</b><span>${escapeHtml(platform)}</span></div>
      <div class="info-cell"><b>CPU 코어</b><span>${cores}</span></div>
      <div class="info-cell"><b>RAM 추정</b><span>${escapeHtml(memEst)}</span></div>
      <div class="info-cell"><b>화면</b><span>${screenInfo}</span></div>
      <div class="info-cell"><b>언어</b><span>${escapeHtml(lang)}</span></div>
      <div class="info-cell"><b>UA</b><span>${escapeHtml(ua)}</span></div>
      <div class="info-cell"><b>현재 시각</b><span>${escapeHtml(ts)}</span></div>
    `;

    // 머신 사양 박스(오케스트레이션 모달용)
    const machineSpec = document.getElementById("machineSpec");
    if (machineSpec) {
      machineSpec.textContent =
        `${platform} · CPU ${cores}코어 · RAM ${memEst} · ${screenInfo}`;
    }
  }

  // 공급자(Ollama/Claude/OpenAI) 상태 폴링
  let providersCache = { ollama: {alive:false}, claude: {api_key_present:false}, openai: {api_key_present:false} };
  async function refreshOllamaStatus() {
    const dot = document.getElementById("liveDot");
    const text = document.getElementById("liveText");
    if (!dot || !text) return;
    try {
      const r = await fetch("/api/providers/status", { cache: "no-store" });
      if (!r.ok) throw new Error("not ok");
      const data = await r.json();
      providersCache = data.providers || providersCache;

      const ol = providersCache.ollama || {};
      const cl = providersCache.claude || {};
      const op = providersCache.openai || {};

      const olOk = !!ol.alive;
      const clOk = !!cl.api_key_present;
      const opOk = !!op.api_key_present;

      const any = olOk || clOk || opOk;
      dot.className = "live-dot " + (any ? "on" : "off");
      const gm = providersCache.gemini || {};
      const gmOk = !!gm.api_key_present;
      const segs = [];
      segs.push(`Ollama ${olOk ? "🟢 LIVE" : "⚪ off"}`);
      segs.push(`Claude(코딩) ${clOk ? "🟢 KEY" : "⚪ no key"}`);
      segs.push(`OpenAI(디자인) ${opOk ? "🟢 KEY" : "⚪ no key"}`);
      segs.push(`Gemini(리서치) ${gmOk ? "🟢 KEY" : "⚪ no key"}`);
      if (data.usage) {
        const u = data.usage;
        segs.push(
          `오늘 ${u.daily_calls}회 · ₩${Math.round(u.daily_used_krw).toLocaleString()} / 캡 ₩${Math.round(u.daily_cap_krw).toLocaleString()}`
        );
      }
      text.textContent = segs.join(" · ");
    } catch (e) {
      dot.className = "live-dot off";
      text.textContent = "공급자 상태 확인 불가 (로컬 뷰어 서버를 켜고 접속하세요)";
    }
    // 매핑 리스트의 LIVE 태그 갱신
    document.querySelectorAll(".map-row .live-tag").forEach((el) => el.remove());
    document.querySelectorAll('.map-row select[data-agent]').forEach((sel) => {
      const opt = sel.options[sel.selectedIndex];
      if (!opt) return;
      const val = opt.value;
      const ol = providersCache.ollama || {};
      const cl = providersCache.claude || {};
      const op = providersCache.openai || {};
      let on = false, label = "";
      const gm = providersCache.gemini || {};
      if (val === "ollama"        && ol.alive)            { on = true; label = "🟢 LIVE"; }
      if (val === "claude"        && cl.api_key_present)  { on = true; label = "🟢 KEY"; }
      if (val === "codex_chatgpt" && op.api_key_present)  { on = true; label = "🟢 KEY"; }
      if (val === "image_ai"      && op.api_key_present)  { on = true; label = "🟢 DALL-E"; }
      if (val === "gemini"        && gm.api_key_present)  { on = true; label = "🟢 KEY"; }
      if (on) {
        const tag = document.createElement("span");
        tag.className = "live-tag";
        tag.textContent = label;
        sel.parentElement.querySelector(".map-name").appendChild(tag);
      }
    });
  }

  // 모델 매핑 리스트
  function renderModelMap() {
    fillSystemInfo();
    const list = document.getElementById("modelMapList");
    list.innerHTML = agents
      .filter((a) => a.status !== "open")
      .map((a) => `
        <div class="map-row">
          <div class="map-name">
            <span>${a.icon}</span>
            <div>
              <b>${escapeHtml(a.name)}</b>
              <small>${escapeHtml(a.title)}</small>
            </div>
          </div>
          <select data-agent="${a.key}">
            ${models.map((m) => `
              <option value="${m.key}" ${modelMap[a.key] === m.key ? "selected" : ""}>
                ${escapeHtml(m.label)} · ${escapeHtml(m.short)}
              </option>
            `).join("")}
          </select>
        </div>
      `).join("");

    list.querySelectorAll("select").forEach((sel) => {
      sel.addEventListener("change", (e) => {
        modelMap[sel.dataset.agent] = sel.value;
        refreshOllamaStatus(); // 선택 변경 후 LIVE 태그 갱신
      });
    });
    refreshOllamaStatus();
  }

  // 자동 오케스트레이션
  document.getElementById("btnAutoMap").addEventListener("click", () => {
    for (const k in autoMap) modelMap[k] = autoMap[k];
    renderModelMap();
  });

  // 카탈로그 토글
  document.getElementById("btnCatalog").addEventListener("click", () => {
    const c = document.getElementById("catalog");
    c.hidden = !c.hidden;
  });

  // 저장
  document.getElementById("btnSaveMap").addEventListener("click", () => {
    saveMap();
    renderAgents();
    closeModals();
  });

  // 새로고침 버튼
  document.getElementById("reloadAgents").addEventListener("click", () => {
    renderCounts();
    renderAgents();
  });

  // 오늘 라벨, 채팅 카운트(시뮬레이터에 접속해야 채워짐 - 여기는 0)
  const d = new Date();
  todayLabel.textContent = `${d.getMonth() + 1}월 ${d.getDate()}일 ${["일","월","화","수","목","금","토"][d.getDay()]}요일`;
  chatCount.textContent = "0";

  syncFilterChips();
  renderCounts();
  renderAgents();

  // 매트릭스 헤더(에이전트 매트릭스 글자) 더블클릭 → 매트릭스 영속 상태 초기화
  const matrixTitle = document.querySelector(".matrix-title");
  if (matrixTitle) {
    matrixTitle.style.cursor = "pointer";
    matrixTitle.title = "더블클릭하면 매트릭스 설정(모델 매핑/필터) 초기화";
    matrixTitle.addEventListener("dblclick", () => {
      if (!confirm("저장된 모델 매핑과 필터를 초기화할까요?")) return;
      clearAllMatrixStorage();
      currentFilter = "all";
      const m = {};
      for (const a of agents) m[a.key] = "ollama";
      modelMap = m;
      syncFilterChips();
      renderCounts();
      renderAgents();
    });
  }
})();
