(() => {
  const agents = (window.AI_COMPANY_AGENTS || []).filter(a => a.status !== "open");

  // 책상 좌표 (SVG viewBox 600 x 360 기준)
  const desks = [
    { x: 70,  y: 70,  room: "리서치룸" },
    { x: 70,  y: 140, room: "리서치룸" },
    { x: 140, y: 70,  room: "리서치룸" },
    { x: 140, y: 140, room: "리서치룸" },
    { x: 460, y: 70,  room: "스튜디오" },
    { x: 530, y: 70,  room: "스튜디오" },
    { x: 460, y: 140, room: "스튜디오" },
    { x: 530, y: 140, room: "스튜디오" },   // 비디오 에디터 자리(편집실)
    { x: 70,  y: 280, room: "운영실" },
    { x: 530, y: 280, room: "운영실" },
  ];
  // 특별 위치
  const SPOTS = {
    meetingTable: { x: 300, y: 180, room: "대회의실" },
    coffeeRoom:   { x: 300, y: 300, room: "휴게실" },
    copyRoom:     { x: 300, y: 70,  label: "복사실" },
    secretaryDesk: { x: 300, y: 240, room: "운영실" }, // 수영이 전용 자리
  };

  // ── 시뮬레이션 상태 ──────────────
  const state = {
    day: 1,
    minutes: 9 * 60, // 09:00 시작
    autoOn: true,
    speed: 1, // 1초 = 1분
    agentsPos: {}, // key -> {x, y, room, occupation}
    activities: [],
    dialog: [],
    artifacts: [],
    currentPair: null,
    tickHandle: null,
    realData: null,            // 텔레그램 비서가 채워주는 실데이터
    realDataConnected: false,  // 정식 데이터 파일 발견 시 true
    realDataIsSample: false,   // 샘플 데이터 폴백일 때 true
    realDataSeenAlerts: new Set(),
  };

  // ── 영속 저장 (localStorage) ─────────
  const STORAGE_KEY = "ai_company.virtual_office.state.v1";
  const STORAGE_LIMITS = { activities: 40, dialog: 60, artifacts: 20 };
  function saveStateLocal() {
    try {
      const snap = {
        day: state.day,
        minutes: state.minutes,
        autoOn: state.autoOn,
        activities: state.activities.slice(0, STORAGE_LIMITS.activities),
        dialog: state.dialog.slice(0, STORAGE_LIMITS.dialog),
        artifacts: state.artifacts.slice(0, STORAGE_LIMITS.artifacts),
        saved_at: new Date().toISOString(),
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(snap));
    } catch (e) { /* quota 초과 등은 조용히 무시 */ }
  }
  function loadStateLocal() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return false;
      const snap = JSON.parse(raw);
      if (typeof snap.day === "number" && snap.day >= 1) state.day = snap.day;
      if (typeof snap.minutes === "number") state.minutes = snap.minutes;
      if (typeof snap.autoOn === "boolean") state.autoOn = snap.autoOn;
      if (Array.isArray(snap.activities)) state.activities = snap.activities;
      if (Array.isArray(snap.dialog)) state.dialog = snap.dialog;
      if (Array.isArray(snap.artifacts)) state.artifacts = snap.artifacts;
      return true;
    } catch (e) { return false; }
  }
  function clearStateLocal() {
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) {}
  }

  // 실데이터 경로 — 정식 → 샘플 순서로 시도
  const REAL_DATA_URLS = [
    "../../08_reports/real_data.json",
    "../../08_reports/real_data.sample.json",
  ];
  const REAL_DATA_REFRESH_MS = 30 * 1000; // 30초마다 폴링

  // 초기 배치
  agents.forEach((a, i) => {
    if (a.key === 'suyeong') {
      state.agentsPos[a.key] = { x: SPOTS.secretaryDesk.x, y: SPOTS.secretaryDesk.y, room: SPOTS.secretaryDesk.room, status: "사장님 대기 중" };
    } else {
      const d = desks[i % desks.length];
      state.agentsPos[a.key] = { x: d.x, y: d.y, room: d.room, status: "자기 자리" };
    }
  });

  // ── SVG 사무실 맵 그리기 ──────────────
  const svg = document.getElementById("officeMap");

  function svgEl(name, attrs = {}) {
    const el = document.createElementNS("http://www.w3.org/2000/svg", name);
    for (const k in attrs) el.setAttribute(k, attrs[k]);
    return el;
  }

  function drawOffice() {
    svg.innerHTML = "";

    // 바닥 (이미지처럼 밝고 따뜻한 톤)
    svg.appendChild(svgEl("rect", { x: 0, y: 0, width: 600, height: 360, fill: "#fdf8f5" }));

    // 방 구획 및 카페트 (공간별 색상 구분)
    const rooms = [
      { x: 20,  y: 20,  w: 180, h: 140, label: "CEO OFFICE", fill: "#fff" },
      { x: 210, y: 20,  w: 180, h: 100, label: "LOUNGE", fill: "#f8fafc" },
      { x: 400, y: 20,  w: 180, h: 140, label: "STUDIO", fill: "#fff" },
      { x: 210, y: 130, w: 180, h: 120, label: "CONFERENCE", fill: "#f1f5f9" },
      { x: 20,  y: 240, w: 180, h: 100, label: "OPERATIONS", fill: "#fff" },
      { x: 210, y: 260, w: 180, h: 80,  label: "CAFE", fill: "#fef3c7" },
      { x: 400, y: 240, w: 180, h: 100, label: "TECH LAB", fill: "#fff" },
    ];
    rooms.forEach((r) => {
      svg.appendChild(svgEl("rect", { x: r.x, y: r.y, width: r.w, height: r.h, class: "room", rx: 4, fill: r.fill }));
      svg.appendChild(svgEl("text", {
        x: r.x + 6, y: r.y + 12, class: "label", "font-size": "8px"
      })).textContent = r.label;
    });

    // 책상 및 모니터 배치 (이미지처럼 듀얼 모니터 표현)
    desks.forEach((d) => {
      // 책상
      svg.appendChild(svgEl("rect", { x: d.x - 20, y: d.y - 12, width: 40, height: 24, class: "desk", rx: 2 }));
      // 모니터 1
      svg.appendChild(svgEl("rect", { x: d.x - 15, y: d.y - 10, width: 12, height: 2, fill: "#334155" }));
      // 모니터 2
      svg.appendChild(svgEl("rect", { x: d.x + 3, y: d.y - 10, width: 12, height: 2, fill: "#334155" }));
    });

    // 회의실 테이블 및 의자
    const mt = SPOTS.meetingTable;
    svg.appendChild(svgEl("ellipse", { cx: mt.x, cy: mt.y, rx: 50, ry: 25, class: "table" }));
    // 의자들 (이미지처럼 테이블 주변 배치)
    for(let i=0; i<8; i++) {
      const angle = (i / 8) * Math.PI * 2;
      svg.appendChild(svgEl("circle", { 
        cx: mt.x + Math.cos(angle) * 60, 
        cy: mt.y + Math.sin(angle) * 35, 
        r: 6, fill: "#94a3b8" 
      }));
    }

    // 인테리어 소품 (이미지의 아기자기함 추가)
    // 식물들
    const plants = [ {x:35, y:35}, {x:185, y:35}, {x:415, y:35}, {x:565, y:35}, {x:225, y:325}, {x:375, y:325} ];
    plants.forEach(p => {
      svg.appendChild(svgEl("circle", { cx: p.x, cy: p.y, r: 5, fill: "#22c55e" }));
      svg.appendChild(svgEl("rect", { x: p.x-2, y: p.y, width: 4, height: 6, fill: "#92400e" }));
    });
    
    // 정수기 (TECH LAB)
    svg.appendChild(svgEl("rect", { x: 420, y: 250, width: 12, height: 20, fill: "#e2e8f0" }));
    svg.appendChild(svgEl("rect", { x: 422, y: 252, width: 8, height: 8, fill: "#38bdf8" }));

    // 대형 스크린 (CONFERENCE)
    svg.appendChild(svgEl("rect", { x: 250, y: 135, width: 100, height: 5, fill: "#1e293b", rx: 2 }));

    // pair-line (대화 표시용)
    const pairLine = svgEl("line", { id: "pairLine", class: "pair-line", x1: 0, y1: 0, x2: 0, y2: 0 });
    svg.appendChild(pairLine);

    // 에이전트 캐릭터
    agents.forEach((a, i) => {
      const pos = state.agentsPos[a.key];
      const g = svgEl("g", { 
        "data-agent": a.key,
        "class": "agent-group",
        "transform": `translate(${pos.x}, ${pos.y})`
      });
      
      // 얼굴 (살구색 톤)
      const face = svgEl("circle", { cx: 0, cy: -22, r: 7, fill: "#ffdbac", class: "agent-sprite" });
      
      // 머리카락 (에이전트 고유 색상 반영)
      const hair = svgEl("path", {
        d: "M -8 -22 Q -8 -32 0 -32 Q 8 -32 8 -22 L 8 -20 L -8 -20 Z",
        fill: a.cardTo || a.cardFrom,
        class: "agent-sprite"
      });

      // 눈 (깜빡이는 느낌의 점)
      const eyeL = svgEl("circle", { cx: -2.5, cy: -22, r: 1, fill: "#000" });
      const eyeR = svgEl("circle", { cx: 2.5, cy: -22, r: 1, fill: "#000" });

      // 몸통 (에이전트 고유 색상의 옷)
      const clothes = svgEl("rect", {
        x: -7, y: -15, width: 14, height: 15, rx: 4,
        fill: a.cardFrom,
        class: "agent-sprite"
      });
      
      // 발 (작은 도트)
      const footL = svgEl("circle", { cx: -3.5, cy: 0, r: 2.5, fill: "#334155" });
      const footR = svgEl("circle", { cx: 3.5, cy: 0, r: 2.5, fill: "#334155" });

      // 이름표 배경
      const nameBg = svgEl("rect", {
        x: -20, y: 5, width: 40, height: 12, rx: 6,
        class: "name-tag-bg"
      });

      // 이름표 텍스트
      const tag = svgEl("text", {
        x: 0, y: 13.5,
        "text-anchor": "middle",
        class: "agent-tag",
        "font-size": "8px"
      });
      tag.textContent = a.name;

      // 상태 바
      const barBg = svgEl("rect", { x: -12, y: 19, width: 24, height: 3, rx: 1.5, class: "status-bar-bg" });
      const barFill = svgEl("rect", { x: -12, y: 19, width: 18, height: 3, rx: 1.5, class: "status-bar-fill" });
      
      g.appendChild(footL);
      g.appendChild(footR);
      g.appendChild(clothes);
      g.appendChild(face);
      g.appendChild(hair);
      g.appendChild(eyeL);
      g.appendChild(eyeR);
      g.appendChild(nameBg);
      g.appendChild(tag);
      g.appendChild(barBg);
      g.appendChild(barFill);
      svg.appendChild(g);
    });
  }

  function moveAgent(key, x, y, room, status) {
    const g = svg.querySelector(`g[data-agent="${key}"]`);
    if (!g) return;
    g.setAttribute("transform", `translate(${x}, ${y})`);
    state.agentsPos[key] = { x, y, room, status };
  }

  function setPairLine(a, b) {
    const pa = state.agentsPos[a];
    const pb = state.agentsPos[b];
    const line = document.getElementById("pairLine");
    if (!pa || !pb) {
      line.classList.remove("active");
      return;
    }
    line.setAttribute("x1", pa.x);
    line.setAttribute("y1", pa.y);
    line.setAttribute("x2", pb.x);
    line.setAttribute("y2", pb.y);
    line.classList.add("active");
  }

  // ── 시간/상태 표시 ──────────────
  function fmtTime() {
    const h = Math.floor(state.minutes / 60) % 24;
    const m = state.minutes % 60;
    return `${String(h).padStart(2,"0")}:${String(m).padStart(2,"0")}`;
  }
  function render() {
    document.getElementById("dayValue").textContent = state.day;
    document.getElementById("timeValue").textContent = fmtTime();
    document.getElementById("autoLabel").textContent = state.autoOn ? "ON" : "OFF";
    document.getElementById("autoTile")
      .querySelector(".tile-pill")
      .classList.toggle("green-on", state.autoOn);
    document.getElementById("currentPair").textContent = state.currentPair || "사장님 명령 대기";

    renderActivity();
    renderArtifacts();
    renderDialog();
  }

  function logActivity(text, fresh = true) {
    state.activities.unshift({ t: fmtTime(), text, fresh });
    if (state.activities.length > 60) state.activities.pop();
  }
  function renderActivity() {
    const ul = document.getElementById("activityList");
    ul.innerHTML = state.activities.map((a, idx) => `
      <li class="${idx === 0 && a.fresh ? "fresh" : ""}">
        <span class="a-time">${a.t}</span>
        <span class="a-body">${a.text}</span>
      </li>
    `).join("");
  }
  function renderArtifacts() {
    const empty = document.getElementById("artifactsEmpty");
    const list = document.getElementById("artifactList");
    if (state.artifacts.length === 0) {
      empty.hidden = false;
      list.hidden = true;
      return;
    }
    empty.hidden = true;
    list.hidden = false;
    list.innerHTML = state.artifacts.map(a => `
      <li>
        <b>${a.name}</b>
        <small>${a.by} · ${a.time}</small>
      </li>
    `).join("");
  }
  function renderDialog() {
    const box = document.getElementById("dialogBox");
    if (state.dialog.length === 0) {
      box.innerHTML = `<span class="ts">대화록 비어 있음. 자율 모드를 켜면 에이전트들의 잡담/회의 기록이 누적됩니다.</span>`;
      return;
    }
    box.innerHTML = state.dialog.map(d => {
      if (d.type === "h2") return `<div class="h2">## [${d.t}] ${d.title}</div>`;
      if (d.type === "err") return `<div class="err">⚠ ${d.text}</div>`;
      return `<div><span class="ts">[${d.t}]</span> ${d.text}</div>`;
    }).join("");
    box.scrollTop = box.scrollHeight;
  }

  // ── 이벤트 생성기 ──────────────
  const ACTIONS = [
    {
      kind: "chat",
      verbs: ["복사실로 이동", "휴게실에서 한숨 돌림", "회의 테이블로 이동"],
      target: ["copyRoom", "coffeeRoom", "meetingTable"]
    },
  ];

  function pickPair() {
    const a = agents[Math.floor(Math.random() * agents.length)];
    let b = agents[Math.floor(Math.random() * agents.length)];
    while (b.key === a.key) b = agents[Math.floor(Math.random() * agents.length)];
    return [a, b];
  }

  function pickEvent() {
    const r = Math.random();
    // 실데이터가 있으면 데이터 기반 이벤트가 더 자주 등장
    if (state.realData) {
      if (r < 0.18) return "real_alert";       // 수영이 알림 릴레이
      if (r < 0.32) return "real_data_chat";   // 데이터/스마트스토어 에이전트 발언
      if (r < 0.55) return "pair_chat";
      if (r < 0.75) return "meeting";
      if (r < 0.88) return "move";
      return "artifact";
    }
    if (r < 0.45) return "pair_chat";
    if (r < 0.7) return "meeting";
    if (r < 0.85) return "move";
    return "artifact";
  }

  const CHAT_TOPICS = [
    "고스틱 광고 후킹 2초",
    "리필 세트 가격 구성",
    "고양이 MBTI 앱 질문지",
    "릴스 썸네일 톤",
    "리뷰 200건 분류 룰",
    "스마트스토어 상세페이지 헤드라인",
    "ROAS 낮은 키워드 처리",
    "광고 이미지 저작권 체크",
    "스튜디오 조명 톤 매핑",
    "고양이 행동 데이터 정리",
  ];
  const ARTIFACT_TEMPLATES = [
    { name: "릴스 대본 3안", from: "마케팅" },
    { name: "썸네일 시안 2종", from: "이미지" },
    { name: "키워드 분석 표", from: "데이터" },
    { name: "리뷰 분류 결과", from: "검수" },
    { name: "상세페이지 검수 메모", from: "검수" },
    { name: "고스틱 광고 패키지", from: "마케팅" },
    { name: "고양이 MBTI 문항", from: "Developer" },
    { name: "트렌드 리서치 요약", from: "리서처" },
    { name: "릴스 9:16 타임라인 + ffmpeg 스크립트", from: "비디오" },
    { name: "쇼츠 자막 SRT 초안", from: "비디오" },
  ];

  function findAgent(name) {
    return agents.find(a => a.name === name) || agents[0];
  }

  // ── 실데이터 로딩 ──────────────
  async function loadRealData() {
    for (const url of REAL_DATA_URLS) {
      try {
        const r = await fetch(url, { cache: "no-store" });
        if (!r.ok) continue;
        const data = await r.json();
        data._source_url = url;
        data._is_sample = url.endsWith(".sample.json") || data.is_sample === true;
        return data;
      } catch (e) {
        // file:// 또는 CORS 실패 → 다음 URL로
      }
    }
    return null;
  }

  function renderRealDataBadge() {
    const badge = document.getElementById("realDataBadge");
    if (!badge) return;
    if (!state.realData) {
      badge.hidden = true;
      return;
    }
    const rd = state.realData;
    const roas = rd.naver_ads?.roas;
    const tag = rd._is_sample ? "샘플" : "실데이터";
    const cls = rd._is_sample ? "real-badge sample" : "real-badge live";
    badge.hidden = false;
    badge.className = cls;
    badge.innerHTML = `🌊 ${tag} · ROAS ${roas ? roas.toFixed(2) : "—"}` +
      (rd.alerts ? ` · 알림 ${rd.alerts.length}` : "");
  }

  async function refreshRealData() {
    const data = await loadRealData();
    const wasConnected = state.realDataConnected;
    const wasSample = state.realDataIsSample;
    state.realData = data;
    state.realDataConnected = !!data;
    state.realDataIsSample = !!(data && data._is_sample);

    // 신규 연결 시 한 번 알림
    if (data && (!wasConnected || (wasSample && !state.realDataIsSample))) {
      const tag = state.realDataIsSample ? "샘플 데이터" : "실데이터";
      logActivity(`🌊 <b>수영</b> · ${tag} 연결됨 (${data.source || "외부 비서"})`);
      // 새 알림 큐잉
      (data.alerts || []).forEach((al) => {
        const id = `${al.level}|${al.title}`;
        if (!state.realDataSeenAlerts.has(id)) {
          state.realDataSeenAlerts.add(id);
          logActivity(`⚠ <span class="alert-${al.level}">${al.title}</span> — ${al.detail || ""}`);
        }
      });
    }
    renderRealDataBadge();
  }

  // ── 실데이터 기반 발언 생성 ──────────────
  function dataAgentLineFromReal() {
    const rd = state.realData;
    if (!rd || !rd.naver_ads) return null;
    const roas = rd.naver_ads.roas;
    const target = rd.naver_ads.target_roas || 2.0;
    const worst = (rd.naver_ads.worst_keywords || [])[0];
    if (typeof roas === "number" && roas < target) {
      let line = `현재 ROAS ${roas.toFixed(2)} — 목표 ${target.toFixed(1)} 미달.`;
      if (worst) line += ` 낭비 키워드 1순위: "${worst.keyword}" (ROAS ${worst.roas?.toFixed(2)})`;
      return line;
    }
    if (typeof roas === "number") {
      return `ROAS ${roas.toFixed(2)} 안정 구간. 입찰 변경보다 새 광고 문구 A/B 권장.`;
    }
    return null;
  }

  function smartstoreLineFromReal() {
    const rd = state.realData;
    if (!rd || !rd.smartstore) return null;
    const low = (rd.smartstore.low_stock || [])[0];
    if (low) {
      return `재고 경고: ${low.product} ${low.stock}개 · 일평균 ${low.daily_velocity}개 → 발주 검토(승인 후 실행).`;
    }
    if (typeof rd.smartstore.avg_review_score === "number") {
      return `최근 리뷰 평균 ${rd.smartstore.avg_review_score.toFixed(1)}점 · 부정 키워드: ${(rd.smartstore.negative_review_keywords || []).join(", ") || "없음"}`;
    }
    return null;
  }

  function pickRealAlert() {
    const rd = state.realData;
    if (!rd || !rd.alerts || rd.alerts.length === 0) return null;
    return rd.alerts[Math.floor(Math.random() * rd.alerts.length)];
  }

  function step() {
    if (!state.autoOn) return;

    // 시간 진행 (한 틱당 5분)
    state.minutes += 5;
    if (state.minutes >= 24 * 60) {
      state.minutes = 9 * 60;
      state.day += 1;
      logActivity(`오늘 하루 종료 → DAY ${state.day} 시작`);
    }

    const ev = pickEvent();
    const time = fmtTime();
    if (ev === "pair_chat") {
      const [a, b] = pickPair();
      const topic = CHAT_TOPICS[Math.floor(Math.random() * CHAT_TOPICS.length)];
      const spot = Math.random() < 0.5 ? "coffeeRoom" : "copyRoom";
      const s = SPOTS[spot];
      moveAgent(a.key, s.x - 14, s.y, s.room, "잡담");
      moveAgent(b.key, s.x + 14, s.y, s.room, "잡담");
      state.currentPair = `${a.name} — ${a.title.split(" ")[0]} → ${b.name} (잡담)`;
      logActivity(`<b>${a.name}</b> → <b>${b.name}</b> · ${s.room}에서 "${topic}" 잡담`);
      setPairLine(a.key, b.key);
      // 대화록에 페어 대화
      state.dialog.unshift({ type: "h2", t: time, title: `${a.name} ↔ ${b.name} (잡담)` });
      state.dialog.unshift({ type: "msg", t: time, text: `<b>${a.name}</b>: ${topic} 어떻게 가져갈까?` });
      state.dialog.unshift({ type: "msg", t: time, text: `<b>${b.name}</b>: 일단 dry-run으로 가설 3개 만들어보자.` });
    } else if (ev === "meeting") {
      const [a, b] = pickPair();
      const c = SPOTS.meetingTable;
      moveAgent(a.key, c.x - 22, c.y, c.room, "회의");
      moveAgent(b.key, c.x + 22, c.y, c.room, "회의");
      state.currentPair = `${a.name} ↔ ${b.name} (회의)`;
      logActivity(`<b>${a.name}</b>, <b>${b.name}</b> · 대회의실 회의`);
      setPairLine(a.key, b.key);
      state.dialog.unshift({ type: "h2", t: time, title: `[CEO 회의 진행] ${a.name}, ${b.name}` });
      state.dialog.unshift({ type: "msg", t: time, text: `<b>CEO</b>: ${a.name}, ${b.name} 다음 주 광고 캠페인 검토 부탁.` });
    } else if (ev === "move") {
      const a = agents[Math.floor(Math.random() * agents.length)];
      const i = agents.indexOf(a);
      const d = desks[i % desks.length];
      moveAgent(a.key, d.x, d.y, d.room, "자기 자리");
      logActivity(`<b>${a.name}</b> · ${d.room} 책상으로 돌아옴`);
      const line = document.getElementById("pairLine");
      if (line) line.classList.remove("active");
    } else if (ev === "artifact") {
      const t = ARTIFACT_TEMPLATES[Math.floor(Math.random() * ARTIFACT_TEMPLATES.length)];
      state.artifacts.unshift({ name: t.name, by: t.from, time: fmtTime() });
      if (state.artifacts.length > 20) state.artifacts.pop();
      const who = findAgent(t.from);
      logActivity(`📦 <b>${who.name}</b> · "${t.name}" 산출물 생성 (dry-run)`);
    } else if (ev === "real_alert") {
      // 수영이 알림 발견 → 담당 에이전트에게 릴레이
      const alert = pickRealAlert();
      if (!alert) return;
      const suyeong = agents.find(a => a.key === "suyeong");
      const owner = findAgent(alert.owner || "데이터");
      if (suyeong) {
        moveAgent(suyeong.key, owner.key === suyeong.key ? SPOTS.secretaryDesk.x : state.agentsPos[owner.key].x - 18,
                  state.agentsPos[owner.key].y, state.agentsPos[owner.key].room, "릴레이");
        setPairLine(suyeong.key, owner.key);
      }
      state.currentPair = `수영 → ${owner.name} (실데이터 알림)`;
      logActivity(`🌊 <b>수영</b> → <b>${owner.name}</b> · <span class="alert-${alert.level}">${alert.title}</span>`);
      state.dialog.unshift({
        type: "h2", t: time,
        title: `수영 → ${owner.name} · 실데이터 알림 (${alert.level})`
      });
      state.dialog.unshift({
        type: "msg", t: time,
        text: `<b>수영</b>: 사장님, ${alert.title} — ${owner.name}에게 전달했습니다.`
      });
      state.dialog.unshift({
        type: "msg", t: time,
        text: `<b>${owner.name}</b>: 확인했습니다. ${alert.detail || "후속 dry-run 작성"}`
      });
      if (state.artifacts.length === 0 || Math.random() < 0.4) {
        state.artifacts.unshift({
          name: `[실데이터] ${alert.title} 후속 메모`,
          by: owner.name,
          time: fmtTime()
        });
      }
    } else if (ev === "real_data_chat") {
      // 데이터 / 스마트스토어 에이전트 발언
      const useStore = Math.random() < 0.5;
      const line = useStore ? smartstoreLineFromReal() : dataAgentLineFromReal();
      if (!line) return;
      const speakerName = useStore ? "스마트스토어" : "데이터";
      const speaker = findAgent(speakerName);
      const ceo = findAgent("CEO");
      const c = SPOTS.meetingTable;
      moveAgent(speaker.key, c.x - 22, c.y, c.room, "데이터 보고");
      moveAgent(ceo.key, c.x + 22, c.y, c.room, "회의");
      setPairLine(speaker.key, ceo.key);
      state.currentPair = `${speaker.name} → CEO (실데이터 보고)`;
      logActivity(`📊 <b>${speaker.name}</b> · ${line}`);
      state.dialog.unshift({ type: "h2", t: time, title: `${speaker.name} → CEO · 실데이터 보고` });
      state.dialog.unshift({ type: "msg", t: time, text: `<b>${speaker.name}</b>: ${line}` });
      state.dialog.unshift({
        type: "msg", t: time,
        text: `<b>CEO</b>: 09_approval 파일 만들고 사장님 승인 후 실행.`
      });
    }

    // 가끔 LLM 에러 mock — 시각적 다양성
    if (Math.random() < 0.04) {
      state.dialog.unshift({
        type: "err",
        t: time,
        text: "모든 에이전트의 LLM 호출이 실패했습니다. (LM Studio 미실행 추정) — 시뮬레이션은 계속됩니다."
      });
    }

    // 직전 fresh 표시 정리
    state.activities.slice(1).forEach(a => (a.fresh = false));
    if (state.dialog.length > 80) state.dialog.length = 80;

    render();
    saveStateLocal();
  }

  // ── 탭 전환 ──────────────
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const tab = btn.dataset.tab;
      document.querySelectorAll("[data-tab-body]").forEach((body) => {
        body.hidden = body.dataset.tabBody !== tab;
      });
    });
  });

  // ── 자율 모드 토글 ──────────────
  document.getElementById("autoTile").addEventListener("click", () => {
    state.autoOn = !state.autoOn;
    if (state.autoOn) {
      logActivity("자율 모드 ON — 에이전트들이 일과를 시작합니다.");
    } else {
      logActivity("자율 모드 OFF — 모든 에이전트 대기 상태");
      const line = document.getElementById("pairLine");
      if (line) line.classList.remove("active");
    }
    render();
    saveStateLocal();
  });

  // ── 새로고침 / 미니 버튼 ──────────────
  document.getElementById("dialogRefresh").addEventListener("click", render);
  document.getElementById("settingsTile").addEventListener("click", () => {
    alert(
      "설정은 직원 에이전트 보기 > 모델 오케스트레이션에서 변경하세요.\n\n" +
      "⚙ 아이콘을 더블클릭하면 가상 사무실 상태(로그/대화록/DAY/TIME)를 초기화합니다."
    );
  });
  document.getElementById("logsTile").addEventListener("click", () => {
    alert("AI 회사 활동 로그는 D:\\AI_COMPANY\\12_logs\\ 에 저장됩니다.");
  });
  document.getElementById("filesTile").addEventListener("click", () => {
    alert("산출물은 D:\\AI_COMPANY\\08_reports\\ 와 09_approval\\ 에 저장됩니다.");
  });

  // ── 초기화 ──────────────
  const restored = loadStateLocal();
  drawOffice();
  if (restored) {
    logActivity(`이전 상태 복원됨 (DAY ${state.day} ${fmtTime()})`);
  } else {
    logActivity("캠퍼스 v2.28: 1동 + 0 장식 · 커스텀 맵 사용");
    logActivity("자율 모드 ON — 에이전트들이 일과를 시작합니다.");
    logActivity(`사무실 가동. 에이전트 ${agents.length}명 자리 잡음.`);
    logActivity("오늘 하루 시작.");
  }
  render();

  // 실데이터 즉시 로딩 + 30초 폴링
  refreshRealData();
  window.setInterval(refreshRealData, REAL_DATA_REFRESH_MS);

  // ── Hermes inbox 폴링 (30초) ─────────
  const HERMES_SEEN_KEY = "ai_company.virtual_office.hermes_seen.v1";
  function loadSeenIds() {
    try { return new Set(JSON.parse(localStorage.getItem(HERMES_SEEN_KEY) || "[]")); }
    catch { return new Set(); }
  }
  function saveSeenIds(setRef) {
    try {
      const arr = Array.from(setRef).slice(-200);
      localStorage.setItem(HERMES_SEEN_KEY, JSON.stringify(arr));
    } catch {}
  }
  let hermesSeen = loadSeenIds();
  async function pollHermes() {
    try {
      const r = await fetch("/api/hermes/recent", { cache: "no-store" });
      if (!r.ok) return;
      const data = await r.json();
      const inbox = data.inbound || [];
      let added = 0;
      for (const m of inbox) {
        const id = `${m.time}|${m.message_id || 0}|${(m.text || "").slice(0,40)}`;
        if (hermesSeen.has(id)) continue;
        hermesSeen.add(id);
        added++;
        const txt = (m.text || "").slice(0, 80);
        if (m.status === "ignored_non_owner") {
          logActivity(`🚫 비-오너 메시지 무시: ${txt}`);
        } else {
          logActivity(`🔔 <b>사장님 텔레그램</b>: ${txt}`);
          // 수영이 받았다는 시각 표현
          const suyeong = agents.find(a => a.key === "suyeong");
          if (suyeong) {
            state.currentPair = `수영 ← 사장님 (텔레그램)`;
          }
        }
      }
      if (added > 0) saveSeenIds(hermesSeen);
      // 배지 갱신 — 자격 상태도 같이
      const sr = await fetch("/api/hermes/status", { cache: "no-store" });
      if (sr.ok) {
        const sd = await sr.json();
        const badge = document.getElementById("realDataBadge");
        if (badge && sd) {
          const tag = sd.credentials_ready ? "🟢 Hermes 연결됨" : "⚪ Hermes 미연결";
          // 기존 real_data 배지 다음에 hermes 상태 추가 표시
          const hermesBadge = document.getElementById("hermesBadge");
          if (hermesBadge) hermesBadge.textContent = tag;
        }
      }
    } catch {}
  }
  pollHermes();
  window.setInterval(pollHermes, 30 * 1000);

  // Ollama 라이브 상태 폴링 (15초 간격) — 가능하면 strip에 표시
  async function pollOllama() {
    try {
      const r = await fetch("/api/ollama/status", { cache: "no-store" });
      if (!r.ok) return;
      const data = await r.json();
      const badge = document.getElementById("realDataBadge");
      const prev = state.ollamaAlive;
      state.ollamaAlive = !!data.alive;
      if (state.ollamaAlive && !prev) {
        logActivity(`🟢 <b>Ollama LIVE</b> · ${data.default_model || "기본 모델"} 응답 (${data.latency_ms ?? "?"}ms)`);
      } else if (!state.ollamaAlive && prev) {
        logActivity("⚪ Ollama 응답 없음 — dry-run 폴백");
      }
    } catch {}
  }
  pollOllama();
  window.setInterval(pollOllama, 15 * 1000);

  // 1.5초마다 한 틱
  state.tickHandle = window.setInterval(step, 1500);

  // 페이지 종료 시 마지막 저장 보장
  window.addEventListener("beforeunload", saveStateLocal);

  // 리셋 버튼 — settings 타일 길게 누르거나 logsTile 더블클릭으로 초기화
  document.getElementById("settingsTile").addEventListener("dblclick", () => {
    if (!confirm("가상 사무실 진행 상태를 초기화할까요? (로그/대화록/산출물/DAY/TIME 모두 삭제)")) return;
    clearStateLocal();
    state.day = 1;
    state.minutes = 9 * 60;
    state.autoOn = true;
    state.activities = [];
    state.dialog = [];
    state.artifacts = [];
    state.realDataSeenAlerts = new Set();
    logActivity("초기화 완료 — 새 일과 시작");
    render();
  });
})();
