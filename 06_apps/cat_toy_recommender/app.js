const form = document.querySelector("#quizForm");
const resultName = document.querySelector("#resultName");
const resultReason = document.querySelector("#resultReason");
const resultTips = document.querySelector("#resultTips");
const refreshShare = document.querySelector("#refreshShare");
const downloadShare = document.querySelector("#downloadShare");
const shareCanvas = document.querySelector("#shareCanvas");
const shareCtx = shareCanvas.getContext("2d");
let currentProductCode = "GOSTICK01";

const results = {
  GOSTICK01: {
    name: "고스틱",
    reason: "활동량이 많고 추격이나 점프 놀이에 잘 반응하는 고양이에게 어울립니다.",
    tips: ["짧게 흔들기보다 숨었다 나오는 흐름을 섞어주세요.", "첫 반응이 약하면 속도를 천천히 올려보세요.", "놀이 후에는 충분히 잡는 경험을 주세요."],
  },
  PLAGO01: {
    name: "플라고스틱",
    reason: "처음 장난감을 고르거나 부담 없이 반응을 테스트하고 싶은 집사에게 어울립니다.",
    tips: ["짧은 놀이를 여러 번 나눠 진행하세요.", "고양이가 멀리서 관찰할 시간을 주세요.", "반응이 좋은 움직임을 기록해두세요."],
  },
  REFILL01: {
    name: "고스틱 리필",
    reason: "이미 고스틱에 익숙하거나 기존 장난감 반응이 줄어든 고양이에게 어울립니다.",
    tips: ["리필 교체 후 새로운 냄새와 움직임에 적응 시간을 주세요.", "기존 놀이 루틴에 변화를 주세요.", "마모된 리필은 안전을 위해 점검하세요."],
  },
};

const shareThemes = {
  GOSTICK01: { accent: "#2f7d5c", warm: "#e9b44c", label: "추격 놀이형" },
  PLAGO01: { accent: "#154c5b", warm: "#d96b57", label: "입문 관찰형" },
  REFILL01: { accent: "#704b33", warm: "#5f8f75", label: "루틴 전환형" },
};

function pickProduct(values) {
  const score = { GOSTICK01: 0, PLAGO01: 0, REFILL01: 0 };

  if (values.style === "chase" || values.style === "jump") score.GOSTICK01 += 2;
  if (values.style === "slow") score.PLAGO01 += 2;
  if (values.energy === "high") score.GOSTICK01 += 2;
  if (values.energy === "medium") score.PLAGO01 += 1;
  if (values.energy === "low") score.PLAGO01 += 2;
  if (values.experience === "new") score.PLAGO01 += 2;
  if (values.experience === "many") score.GOSTICK01 += 1;
  if (values.experience === "refill") score.REFILL01 += 4;
  if (values.personality === "bold") score.GOSTICK01 += 2;
  if (values.personality === "careful") score.PLAGO01 += 2;
  if (values.personality === "lazy") score.PLAGO01 += 1;
  if (values.playTime === "long") score.GOSTICK01 += 1;
  if (values.playTime === "short") score.PLAGO01 += 1;
  if (values.playTime === "night") score.GOSTICK01 += 1;
  if (values.space === "wide" || values.space === "vertical") score.GOSTICK01 += 1;
  if (values.space === "small") score.PLAGO01 += 1;
  if (values.sensitivity === "high") score.PLAGO01 += 2;
  if (values.sensitivity === "low") score.GOSTICK01 += 1;
  if (values.problem === "replace") score.REFILL01 += 3;
  if (values.problem === "starter") score.PLAGO01 += 2;
  if (values.problem === "bored") score.GOSTICK01 += 1;

  return Object.entries(score).sort((a, b) => b[1] - a[1])[0][0];
}

function renderResult(productCode) {
  const result = results[productCode];
  currentProductCode = productCode;
  resultName.textContent = result.name;
  resultReason.textContent = result.reason;
  resultTips.innerHTML = result.tips.map((tip) => `<li>${tip}</li>`).join("");
  drawSharePreview(productCode);
}

function roundedRect(ctx, x, y, width, height, radius) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + width, y, x + width, y + height, radius);
  ctx.arcTo(x + width, y + height, x, y + height, radius);
  ctx.arcTo(x, y + height, x, y, radius);
  ctx.arcTo(x, y, x + width, y, radius);
  ctx.closePath();
}

function wrapText(ctx, text, maxWidth) {
  const lines = [];
  let current = "";
  text.split(" ").forEach((word) => {
    const next = current ? `${current} ${word}` : word;
    if (ctx.measureText(next).width <= maxWidth) {
      current = next;
      return;
    }
    if (current) lines.push(current);
    if (ctx.measureText(word).width <= maxWidth) {
      current = word;
      return;
    }
    let chunk = "";
    [...word].forEach((char) => {
      if (ctx.measureText(chunk + char).width > maxWidth) {
        lines.push(chunk);
        chunk = char;
      } else {
        chunk += char;
      }
    });
    current = chunk;
  });
  if (current) lines.push(current);
  return lines;
}

function drawLines(ctx, lines, x, y, lineHeight) {
  lines.forEach((line, index) => {
    ctx.fillText(line, x, y + index * lineHeight);
  });
}

function drawToyMark(ctx, theme) {
  ctx.save();
  ctx.translate(360, 430);
  ctx.strokeStyle = theme.accent;
  ctx.lineWidth = 18;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(-210, 120);
  ctx.bezierCurveTo(-120, -50, 100, -110, 210, -230);
  ctx.stroke();
  ctx.fillStyle = theme.warm;
  for (let index = 0; index < 5; index += 1) {
    const angle = index * 1.25;
    const x = Math.cos(angle) * 66;
    const y = Math.sin(angle) * 46 - 180;
    roundedRect(ctx, x - 34, y - 18, 68, 36, 18);
    ctx.fill();
  }
  ctx.fillStyle = theme.accent;
  roundedRect(ctx, -60, 75, 120, 56, 24);
  ctx.fill();
  ctx.restore();
}

function drawSharePreview(productCode) {
  const result = results[productCode];
  const theme = shareThemes[productCode];
  const ctx = shareCtx;
  ctx.clearRect(0, 0, shareCanvas.width, shareCanvas.height);

  const gradient = ctx.createLinearGradient(0, 0, 720, 1280);
  gradient.addColorStop(0, "#fbfaf6");
  gradient.addColorStop(0.58, "#f3f2ed");
  gradient.addColorStop(1, "#e8f0ef");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 720, 1280);

  ctx.fillStyle = theme.accent;
  ctx.fillRect(0, 0, 720, 24);
  ctx.fillStyle = theme.warm;
  ctx.fillRect(0, 24, 720, 10);

  ctx.fillStyle = "#20242a";
  ctx.font = "800 30px Segoe UI, Malgun Gothic, sans-serif";
  ctx.fillText("ABIBI CAT PLAY", 58, 98);

  ctx.fillStyle = "#65727b";
  ctx.font = "700 24px Segoe UI, Malgun Gothic, sans-serif";
  ctx.fillText(theme.label, 58, 148);

  drawToyMark(ctx, theme);

  roundedRect(ctx, 48, 620, 624, 468, 32);
  ctx.fillStyle = "rgba(255, 255, 255, 0.88)";
  ctx.fill();
  ctx.strokeStyle = "#d9e0dc";
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.fillStyle = theme.accent;
  ctx.font = "900 70px Segoe UI, Malgun Gothic, sans-serif";
  ctx.fillText(result.name, 86, 720);

  ctx.fillStyle = "#303840";
  ctx.font = "700 32px Segoe UI, Malgun Gothic, sans-serif";
  drawLines(ctx, wrapText(ctx, result.reason, 540).slice(0, 3), 86, 786, 48);

  ctx.fillStyle = "#20242a";
  ctx.font = "800 27px Segoe UI, Malgun Gothic, sans-serif";
  result.tips.slice(0, 3).forEach((tip, index) => {
    const y = 940 + index * 58;
    ctx.fillStyle = theme.warm;
    ctx.beginPath();
    ctx.arc(94, y - 8, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#20242a";
    drawLines(ctx, wrapText(ctx, tip, 500).slice(0, 1), 118, y, 38);
  });

  ctx.fillStyle = "#65727b";
  ctx.font = "700 24px Segoe UI, Malgun Gothic, sans-serif";
  ctx.fillText("고양이 놀이 성향 추천 결과", 58, 1195);

  downloadShare.href = shareCanvas.toDataURL("image/png");
  downloadShare.download = `abibi-cat-play-${productCode.toLowerCase()}.png`;
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const values = {
    style: data.get("style"),
    energy: data.get("energy"),
    experience: data.get("experience"),
    personality: data.get("personality"),
    playTime: data.get("playTime"),
    space: data.get("space"),
    sensitivity: data.get("sensitivity"),
    problem: data.get("problem"),
  };
  renderResult(pickProduct(values));
});

refreshShare.addEventListener("click", () => {
  drawSharePreview(currentProductCode);
});

renderResult("GOSTICK01");
