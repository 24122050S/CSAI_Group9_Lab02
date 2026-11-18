/* Bilingual (Vietnamese default + English toggle) Frontend Controller for Griductive Solver */

let currentLang = "vi"; // Default to Vietnamese for effortless gameplay!
let catalogItems = [];
let currentPayload = null;
let activeHighlight = null;
let autoSolveTimer = null;
let lastPuzzleId = null;
let previouslyRevealed = new Set();
let latestCNFData = null;

const el = (id) => document.getElementById(id);

const PROFESSION_SVGS = {
  cook: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 13.87A4 4 0 0 1 7.41 6a5.11 5.11 0 0 1 9.18 0A4 4 0 0 1 18 13.87V21H6Z"/><line x1="6" y1="17" x2="18" y2="17"/></svg>',
  guard: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  detective: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
  astronaut: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/></svg>',
  farmer: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20"/><path d="M17 7c-3 0-5 2-5 5 0-3-2-5-5-5"/><path d="M17 13c-3 0-5 2-5 5 0-3-2-5-5-5"/></svg>',
  painter: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="13.5" cy="6.5" r=".5" fill="currentColor"/><circle cx="17.5" cy="10.5" r=".5" fill="currentColor"/><circle cx="8.5" cy="7.5" r=".5" fill="currentColor"/><circle cx="6.5" cy="12.5" r=".5" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.65-.75 1.65-1.69 0-.43-.18-.83-.44-1.12-.29-.29-.44-.65-.44-1.13a1.64 1.64 0 0 1 1.67-1.67h2a5.55 5.55 0 0 0 5.56-5.55C21.97 6.01 17.46 2 12 2z"/></svg>',
  clerk: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
  default: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M6 20v-2a6 6 0 0 1 12 0v2"/></svg>',
};

const JOB_VI = {
  astronaut: "Phi hành gia",
  clerk: "Thư ký",
  cook: "Đầu bếp",
  detective: "Thám tử",
  farmer: "Nông dân",
  guard: "Bảo vệ",
  painter: "Họa sĩ",
  citizen: "Cư dân",
};

const DIFF_VI = {
  Easy: "Dễ",
  Medium: "Trung bình",
  Hard: "Khó",
  "Coupled-Hard": "Khó (Ép quay lui)",
  Stress: "Thử tải 5×5",
  "Coupled-Stress": "Thử tải nặng (Quay lui)",
  Showcase: "Đặc biệt (Hình 1 đề)",
  Diagnostic: "Chẩn đoán biên",
  Standard: "Tiêu chuẩn",
};

const PUZZLE_TITLE_VI = {
  "3x3_01_core_intro": "3×3 Màn 1 — Khởi đầu Ca trực (Cơ bản)",
  "3x3_02_neighbors_chain": "3×3 Màn 2 — Vòng vây Lân cận",
  "3x3_03_extensions_mix": "3×3 Màn 3 — Chẵn lẻ & Giao vùng",
  "3x3_06_compound_connected": "3×3 Màn 4 — Mệnh đề Ghép & Liên thông",
  "3x3_04_ambiguous_case": "3×3 Chẩn đoán — Thiếu dữ kiện (Dừng không đoán)",
  "3x3_05_inconsistent_case": "3×3 Chẩn đoán — Manh mối Mâu thuẫn (UNSAT)",
  "4x4_01_core_patrol": "4×4 Màn 1 — Tuần tra Đêm",
  "4x4_02_core_precinct": "4×4 Màn 2 — Hồ sơ Đồn cảnh sát",
  "4x4_03_ext_intersections": "4×4 Màn 3 — Giao điểm Nghi vấn",
  "4x4_04_ext_professions": "4×4 Màn 4 — Điều tra Nghề nghiệp (15 bước)",
  "4x4_05_ext_deep_chain": "4×4 Màn 5 — Nhân chứng Thầm lặng",
  "4x4_06_coupled_crucible": "4×4 Nâng cao 1 — Ràng buộc Giao thoa (Ép Backtrack)",
  "4x4_07_coupled_parity_matrix": "4×4 Nâng cao 2 — Ma trận Chẵn lẻ & Lực lượng",
  "5x5_01_core_metropolis": "5×5 Thử tải 1 — Đại đô thị (25 nhân vật)",
  "5x5_02_ext_grand_inquest": "5×5 Thử tải 2 — Đại thẩm vấn (Mở rộng)",
  "5x5_03_single_seed_stress": "5×5 Thử tải 3 — Mật báo Đơn độc (24 bước)",
  "5x5_04_coupled_labyrinth": "5×5 Thử tải 4 — Mê cung Ràng buộc (Backtrack cao)",
  "5x5_05_coupled_fortress": "5×5 Thử tải 5 — Pháo đài Giao thoa (645 Backtracks)",
  "5x5_06_figure1_showcase": "5×5 Đặc biệt — Tái hiện Hình 1 Đề bài",
};

const PUZZLE_DESC_VI = {
  "3x3_01_core_intro": "Màn hướng dẫn 3×3 dễ chơi sử dụng 6 mẫu manh mối cốt lõi.",
  "3x3_02_neighbors_chain": "Kết hợp đếm số tội phạm ở các ô xung quanh và theo cột.",
  "3x3_03_extensions_mix": "Giới thiệu vùng nâng cao, so sánh hai vùng và tính chẵn/lẻ.",
  "3x3_06_compound_connected": "Minh họa mệnh đề ghép (VÀ, HOẶC, NẾU-THÌ) và tính liên thông cạnh.",
  "3x3_04_ambiguous_case": "Giải được B1 & C1 rồi dừng an toàn ở trạng thái STUCK vì nhiều nghiệm (không đoán mò!).",
  "3x3_05_inconsistent_case": "Hai thẻ mở đầu mâu thuẫn nhau — phát hiện ngay trạng thái UNSAT.",
  "4x4_01_core_patrol": "Màn 4×4 tiêu chuẩn sử dụng 6 mẫu manh mối cơ bản.",
  "4x4_02_core_precinct": "Chuỗi suy luận 14 bước liên tiếp trên bàn cờ 4×4.",
  "4x4_03_ext_intersections": "Kết hợp phép giao hai vùng, chẵn lẻ và so sánh số lượng.",
  "4x4_04_ext_professions": "Xuất phát chỉ từ 1 thẻ mở đầu duy nhất, suy luận trọn vẹn 15 bước.",
  "4x4_05_ext_deep_chain": "Chuỗi suy luận nhiều đợt mở thẻ nối tiếp nhau.",
  "4x4_06_coupled_crucible": "Hệ ràng buộc giao nhau không có mệnh đề đơn sẵn, thử thách nhánh quay lui DPLL.",
  "4x4_07_coupled_parity_matrix": "Kết hợp chuỗi XOR chẵn/lẻ 6 biến với ràng buộc đếm.",
  "5x5_01_core_metropolis": "Bàn cờ lớn 5×5 (25 nhân vật) với các manh mối đếm cơ bản.",
  "5x5_02_ext_grand_inquest": "Bàn cờ 5×5 kết hợp đầy đủ các biểu thức vùng nâng cao.",
  "5x5_03_single_seed_stress": "Xuất phát từ đúng 1 người chỉ điểm, giải liên hoàn 24 bước.",
  "5x5_04_coupled_labyrinth": "Dải 7 biến tự do phía trên cụm ràng buộc giao thoa trên lưới 5×5.",
  "5x5_05_coupled_fortress": "Bài kiểm thử cực hạn ép thứ tự biến cố định phải quay lui 645 lần.",
  "5x5_06_figure1_showcase": "Mô phỏng đúng các dạng câu manh mối trong Hình 1 trang 1 của đề bài.",
};

function isVi() {
  return currentLang === "vi";
}

function getProfessionIcon(job) {
  const key = (job || "").trim().toLowerCase();
  return PROFESSION_SVGS[key] || PROFESSION_SVGS.default;
}

function formatProfession(job) {
  const raw = (job || "Citizen").trim();
  if (!isVi()) return raw;
  return JOB_VI[raw.toLowerCase()] || raw;
}

function formatDifficulty(diff) {
  if (!isVi()) return diff;
  return DIFF_VI[diff] || diff;
}

function formatPuzzleTitle(pid, fallbackTitle) {
  if (!isVi()) return fallbackTitle;
  return PUZZLE_TITLE_VI[pid] || fallbackTitle;
}

function formatPuzzleDesc(pid, fallbackDesc) {
  if (!isVi()) return fallbackDesc || "";
  return PUZZLE_DESC_VI[pid] || fallbackDesc || "";
}

function formatStatusWord(st) {
  if (!isVi()) return st;
  if (st === "CRIMINAL") return "TỘI PHẠM";
  if (st === "INNOCENT") return "VÔ TỘI";
  return "CHƯA MỞ";
}

function applyStaticTranslations() {
  const vi = isVi();
  el("btnLangToggle").textContent = vi ? "🇻🇳 Tiếng Việt" : "🇬🇧 English";
  el("lblSubtitle").textContent = vi
    ? "Trò chơi Suy luận Logic Mệnh đề — Không Đoán Mò (CNF & DPLL SAT)"
    : "No-Guess Propositional Logic, CNF & Custom DPLL SAT Lab";
  el("lblStage").textContent = vi ? "Màn chơi" : "Stage";
  el("txtUploadJson").textContent = vi ? "Tải JSON" : "Load JSON";
  el("btnRestart").textContent = vi ? "Chơi lại" : "Restart";
  el("btnHint").textContent = vi ? "Gợi ý" : "Hint";
  el("btnStep").textContent = vi ? "Giải 1 bước" : "Step";
  if (autoSolveTimer === null) {
    el("btnAutoSolve").textContent = vi ? "Tự động giải" : "Auto Solve";
  } else {
    el("btnAutoSolve").textContent = vi ? "Dừng" : "Stop";
  }
  el("btnInspectCNF").innerHTML = vi
    ? "Soi CNF (KB<sub>t</sub>)"
    : "Inspect KB<sub>t</sub> CNF";
  el("btnUniqueness").textContent = vi ? "Kiểm tra Duy nhất" : "Check Uniqueness";
  el("btnClearHighlight").textContent = vi ? "Bỏ đánh dấu" : "Clear Highlight";

  // Speed select options
  const sp = el("speedSelect").options;
  sp[0].textContent = vi ? "Vừa (0.65s)" : "Normal (0.65s)";
  sp[1].textContent = vi ? "Chậm / Demo (1.1s)" : "Demo (1.1s)";
  sp[2].textContent = vi ? "Nhanh (0.22s)" : "Fast (0.22s)";
  sp[3].textContent = vi ? "Tức thì" : "Instant";

  // Legend
  el("legInno").innerHTML = vi ? "Vô tội (¬C<sub>i</sub>)" : "Innocent (¬C<sub>i</sub>)";
  el("legCrim").innerHTML = vi ? "Tội phạm (C<sub>i</sub>)" : "Criminal (C<sub>i</sub>)";
  el("legHl1").textContent = vi ? "Vùng manh mối / Ô gợi ý" : "Clue Region / Hint Target";
  el("legHl2").textContent = vi ? "Vùng đối chiếu / Thẻ hỗ trợ" : "Compared Region / Supporting Clue";

  // Right inspector labels
  el("hdrConfig").textContent = vi
    ? "Cấu hình Mã hóa CNF & Bộ giải DPLL"
    : "CNF Encoder & DPLL Configuration";
  el("lblEncMode").textContent = vi ? "Mã hóa lực lượng CNF" : "Cardinality CNF";
  el("selEncoding").options[0].textContent = vi
    ? "Tổ hợp trực tiếp (0 biến phụ)"
    : "Direct Combinatorial (0 Aux)";
  el("selEncoding").options[1].textContent = vi
    ? "Bộ đếm tuần tự Sinz (Có biến phụ)"
    : "Sinz Sequential Counter (Aux)";

  el("lblHeurMode").textContent = vi ? "Chiến lược chọn biến DPLL" : "DPLL Branching";
  el("selHeuristic").options[0].textContent = vi
    ? "Thứ tự biến cố định"
    : "Fixed Variable Order";
  el("selHeuristic").options[1].textContent = vi
    ? "Jeroslow-Wang tất định"
    : "Jeroslow-Wang Deterministic";

  el("lblPLE").textContent = vi ? "Khử literal thuần (PLE)" : "Pure-Literal Elimination";
  el("lblPrune").textContent = vi
    ? "Cắt tỉa theo mô hình mẫu (Witness)"
    : "Witness-Guided Pruning";

  el("hdrStats").innerHTML = vi
    ? "Kho Tri Thức Công Khai (KB<sub>t</sub>) &amp; DPLL"
    : "Public Knowledge Base (KB<sub>t</sub>) &amp; DPLL Stats";
  el("btnQuickCNF").textContent = vi ? "Xem mệnh đề" : "View Clauses";

  el("mlPrimary").textContent = vi ? "Biến sơ cấp" : "Primary Vars";
  el("mlAux").textContent = vi ? "Biến phụ" : "Auxiliary Vars";
  el("mlClauses").textContent = vi ? "Mệnh đề CNF" : "CNF Clauses";
  el("mlSat").textContent = vi ? "Lần gọi SAT" : "SAT Calls";
  el("mlProp").textContent = vi ? "Lan truyền" : "Propagations";
  el("mlDec").textContent = vi ? "Phân nhánh" : "Decisions";
  el("mlBt").textContent = vi ? "Quay lui" : "Backtracks";
  el("mlTime").textContent = vi ? "Thời gian DPLL" : "DPLL Runtime";

  el("hdrUniq").textContent = vi
    ? "Kiểm tra Tính Duy nhất Nghiệm"
    : "Complete Clue Set Uniqueness";
  el("btnCloseUniq").textContent = vi ? "Ẩn" : "Hide";
  el("hdrTrace").textContent = vi
    ? "Lịch sử Suy diễn & Nước đi"
    : "Deduction & Move History";

  el("cnfModalTitle").innerHTML = vi
    ? "Soi Trực Tiếp Công Thức CNF Của Kho Tri Thức (KB<sub>t</sub>)"
    : "Live Knowledge Base (KB<sub>t</sub>) CNF Inspector";
  el("btnDownloadCNF").textContent = vi ? "Tải file .cnf" : "Download .cnf";
  el("btnCloseCNFModal").textContent = vi ? "Đóng" : "Close";
  el("tabBtnSym").textContent = vi
    ? "Mệnh đề Ký hiệu (Theo từng thẻ)"
    : "Symbolic Clauses (Grouped by Clue)";
  el("tabBtnVar").innerHTML = vi
    ? "Bảng Ánh xạ Biến (C<sub>i</sub> &amp; Biến phụ)"
    : "Variable Mapping (C<sub>i</sub> &amp; Aux)";
  el("tabBtnDimacs").textContent = vi ? "Chuẩn DIMACS .cnf" : "Standard DIMACS .cnf";

  populateCatalogSelect();
  if (currentPayload) updateUI(currentPayload, true);
}

function populateCatalogSelect() {
  const select = el("puzzleSelect");
  const curVal = currentPayload ? currentPayload.state.puzzle_id : select.value;
  select.innerHTML = "";
  for (const p of catalogItems) {
    const opt = document.createElement("option");
    opt.value = p.puzzle_id;
    const t = formatPuzzleTitle(p.puzzle_id, p.title);
    const d = formatDifficulty(p.difficulty);
    opt.textContent = `${t} [${d}]`;
    if (p.puzzle_id === curVal) opt.selected = true;
    select.appendChild(opt);
  }
}

function setBanner(kind, badge, message, showClear = false) {
  const banner = el("statusBanner");
  banner.className = `status-banner status-${kind}`;
  el("statusBadge").textContent = badge;
  el("statusText").textContent = message;
  el("btnClearHighlight").hidden = !showClear;
}

function clearHighlightState() {
  activeHighlight = null;
  el("btnClearHighlight").hidden = true;
  if (currentPayload) renderBoard(currentPayload.state, new Set());
}

async function apiFetch(url, method = "GET", body = null) {
  const opts = { method, headers: {} };
  if (body !== null) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const resp = await fetch(url, opts);
  const data = await resp.json();
  if (!resp.ok || data.ok === false) {
    throw new Error(data.error || `Request failed (${resp.status})`);
  }
  return data;
}

function renderBoard(state, newlyFlippedSet = new Set()) {
  const wrapper = el("boardWrapper");
  const n = state.grid_size;
  wrapper.className = `board-wrapper board-size-${n}`;
  wrapper.style.gridTemplateColumns = `28px repeat(${n}, minmax(130px, 1fr))`;
  wrapper.innerHTML = "";

  const corner = document.createElement("div");
  wrapper.appendChild(corner);
  for (let c = 0; c < n; c++) {
    const colHdr = document.createElement("div");
    colHdr.className = "coord-col-header";
    colHdr.textContent = String.fromCharCode(65 + c);
    wrapper.appendChild(colHdr);
  }

  for (let r = 1; r <= n; r++) {
    const rowHdr = document.createElement("div");
    rowHdr.className = "coord-row-header";
    rowHdr.textContent = String(r);
    wrapper.appendChild(rowHdr);

    const rowCells = state.cells.filter((cell) => cell.row === r);
    for (const cell of rowCells) {
      wrapper.appendChild(buildCardElement(cell, newlyFlippedSet.has(cell.cell_id)));
    }
  }
}

function getClueDisplayText(clueObj) {
  if (!clueObj) return isVi() ? "(Không có manh mối thêm)" : "(No additional clue)";
  if (isVi() && clueObj.text_vi) return clueObj.text_vi;
  return clueObj.text || "";
}

function buildCardElement(cell, animateFlip = false) {
  const card = document.createElement("div");
  card.id = `card-${cell.cell_id}`;
  const classes = ["suspect-card"];

  if (cell.is_revealed) {
    classes.push(
      cell.status === "CRIMINAL" ? "revealed-criminal" : "revealed-innocent"
    );
    if (animateFlip) classes.push("flip-reveal");
  } else {
    classes.push("facedown");
  }

  if (activeHighlight) {
    if (activeHighlight.owner === cell.cell_id) classes.push("hl-owner");
    if (activeHighlight.hintTarget === cell.cell_id) classes.push("hl-hint-target");
    else if (activeHighlight.primary.has(cell.cell_id)) classes.push("hl-primary");
    else if (activeHighlight.secondary.has(cell.cell_id)) classes.push("hl-secondary");
  }
  card.className = classes.join(" ");

  const top = document.createElement("div");
  top.className = "card-top";

  const coordChip = document.createElement("span");
  coordChip.className = "coord-chip";
  coordChip.textContent = cell.cell_id;

  const pill = document.createElement("span");
  if (cell.is_revealed) {
    pill.className =
      cell.status === "CRIMINAL"
        ? "status-pill pill-criminal"
        : "status-pill pill-innocent";
    pill.textContent = formatStatusWord(cell.status);
  } else {
    pill.className = "status-pill pill-unknown";
    pill.textContent = formatStatusWord("UNKNOWN");
  }
  top.append(coordChip, pill);

  const ident = document.createElement("div");
  ident.className = "card-identity";

  const avatar = document.createElement("div");
  avatar.className = "avatar-circle";
  avatar.textContent = cell.name.charAt(0).toUpperCase();

  const nameDiv = document.createElement("div");
  nameDiv.className = "char-name";
  nameDiv.textContent = cell.name;

  const jobDiv = document.createElement("div");
  jobDiv.className = "job-badge";
  const rawJob = cell.profession || "Citizen";
  jobDiv.innerHTML = `${getProfessionIcon(rawJob)}<span>${formatProfession(rawJob)}</span>`;

  ident.append(avatar, nameDiv, jobDiv);
  card.append(top, ident);

  if (cell.is_revealed) {
    const clueBox = document.createElement("div");
    clueBox.className = "clue-box";
    clueBox.textContent = getClueDisplayText(cell.clue);
    card.appendChild(clueBox);
    card.addEventListener("click", () => toggleClueHighlight(cell.cell_id));
  } else {
    const actions = document.createElement("div");
    actions.className = "verdict-actions";

    const btnInno = document.createElement("button");
    btnInno.className = "btn-verdict btn-call-innocent";
    btnInno.textContent = isVi() ? "Vô tội" : "Innocent";
    btnInno.addEventListener("click", (ev) => {
      ev.stopPropagation();
      submitVerdict(cell.cell_id, "INNOCENT");
    });

    const btnCrim = document.createElement("button");
    btnCrim.className = "btn-verdict btn-call-criminal";
    btnCrim.textContent = isVi() ? "Tội phạm" : "Criminal";
    btnCrim.addEventListener("click", (ev) => {
      ev.stopPropagation();
      submitVerdict(cell.cell_id, "CRIMINAL");
    });

    actions.append(btnInno, btnCrim);
    card.appendChild(actions);
  }

  return card;
}

function updateUI(payload, resetFlipHistory = false) {
  currentPayload = payload;
  const st = payload.state;

  const currentRev = new Set(
    st.cells.filter((c) => c.is_revealed).map((c) => c.cell_id)
  );
  const newlyFlipped = new Set();

  if (resetFlipHistory || lastPuzzleId !== st.puzzle_id) {
    lastPuzzleId = st.puzzle_id;
  } else {
    for (const cid of currentRev) {
      if (!previouslyRevealed.has(cid)) newlyFlipped.add(cid);
    }
  }
  previouslyRevealed = currentRev;

  el("puzzleTitle").textContent = formatPuzzleTitle(st.puzzle_id, st.title);
  el("puzzleDesc").textContent = formatPuzzleDesc(st.puzzle_id, payload.description);
  el("progressLabel").textContent = isVi()
    ? `${st.revealed_count} / ${st.total_cells} Đã mở`
    : `${st.revealed_count} / ${st.total_cells} Proved`;
  el("difficultyBadge").textContent = `${st.grid_size}×${st.grid_size} • ${formatDifficulty(payload.difficulty)}`;

  el("selEncoding").value = payload.solver_settings.encoding_mode;
  el("selHeuristic").value = payload.solver_settings.heuristic;
  el("chkPureLiteral").checked = payload.solver_settings.use_pure_literal;
  el("chkWitnessPruning").checked = payload.solver_settings.use_witness_pruning;

  const kb = payload.kb_metrics;
  const stats = payload.telemetry.stats;
  el("mPrimaryVars").textContent = kb.num_primary_vars;
  el("mAuxVars").textContent = kb.num_aux_vars;
  el("mClauses").textContent = kb.num_clauses;
  el("mSatCalls").textContent = payload.telemetry.total_sat_calls;
  el("mPropagations").textContent = stats.propagations;
  el("mDecisions").textContent = stats.decisions;
  el("mBacktracks").textContent = stats.backtracks;
  el("mRuntime").textContent = `${stats.runtime_ms.toFixed(2)} ms`;

  renderBoard(st, newlyFlipped);
  renderTraces(payload.telemetry.traces);
}

function renderTraces(traces) {
  const list = el("traceList");
  const vi = isVi();
  el("traceCountBadge").textContent = vi
    ? `${traces.length} bước`
    : `${traces.length} step${traces.length === 1 ? "" : "s"}`;

  if (!traces.length) {
    list.innerHTML = vi
      ? '<p class="empty-trace">Chưa có bước suy diễn nào. Hãy tự kết luận một nghi phạm hoặc bấm <strong>Giải 1 bước</strong> / <strong>Tự động giải</strong> để xem truy vấn SAT.</p>'
      : '<p class="empty-trace">No proved moves recorded yet. Submit a valid verdict manually, or click <strong>Step</strong> / <strong>Auto Solve</strong> to trace SAT refutation queries.</p>';
    return;
  }

  // Build map cell_id -> localized clue text from current state if available
  const clueViByCell = {};
  if (currentPayload && currentPayload.state) {
    for (const c of currentPayload.state.cells) {
      if (c.is_revealed && c.clue) {
        clueViByCell[c.cell_id] = getClueDisplayText(c.clue);
      }
    }
  }

  list.innerHTML = "";
  for (let i = traces.length - 1; i >= 0; i--) {
    const tr = traces[i];
    const div = document.createElement("div");
    div.className = "trace-item";

    let verdictBadge = "";
    if (tr.chosen_cell && tr.verdict) {
      const cls = tr.verdict === "CRIMINAL" ? "pill-criminal" : "pill-innocent";
      const dispChar = vi
        ? tr.chosen_character.replace("[Manual]", "[Tự chọn]")
        : tr.chosen_character;
      verdictBadge = `<span class="status-pill ${cls}">${dispChar} (${tr.chosen_cell}) → ${formatStatusWord(tr.verdict)}</span>`;
    } else {
      verdictBadge = `<span class="status-pill pill-unknown">${tr.terminal_state}</span>`;
    }

    const rowsHtml = tr.sat_queries
      .map(
        (q) => `
      <tr>
        <td><code>${q.query_label}</code></td>
        <td class="${q.result === "UNSAT" ? "q-unsat" : "q-sat"}">${q.result}</td>
        <td>${q.stats.propagations}p / ${q.stats.decisions}d / ${q.stats.backtracks}b</td>
      </tr>`
      )
      .join("");

    const dispClue =
      tr.chosen_cell && clueViByCell[tr.chosen_cell]
        ? clueViByCell[tr.chosen_cell]
        : tr.newly_revealed_clue_text;

    div.innerHTML = `
      <div class="trace-top">
        <span>${vi ? "Bước" : "Step"} #${tr.step_number}</span>
        ${verdictBadge}
      </div>
      <div class="trace-meta">
        KB<sub>${tr.step_number}</sub>: ${tr.num_primary_vars} ${vi ? "sơ cấp" : "primary"} + ${tr.num_aux_vars} ${vi ? "biến phụ" : "aux"},
        ${tr.num_clauses} ${vi ? "mệnh đề" : "clauses"} • ${tr.sat_queries_count} ${vi ? "lần gọi SAT" : "SAT calls"}
      </div>
      ${
        dispClue
          ? `<div class="trace-new-clue"><strong>${vi ? "Manh mối mở ra" : "Revealed"} (${tr.newly_revealed_clue_id}):</strong> ${dispClue}</div>`
          : ""
      }
      <details>
        <summary>${vi ? `Xem ${tr.sat_queries_count} truy vấn phản chứng SAT` : `Inspect ${tr.sat_queries_count} SAT Refutation Queries`}</summary>
        <table class="sat-query-table">
          <thead><tr><th>${vi ? "Truy vấn" : "Query"}</th><th>${vi ? "Kết quả" : "Outcome"}</th><th>DPLL</th></tr></thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </details>
    `;
    list.appendChild(div);
  }
}

async function openCNFModal() {
  stopAutoSolve();
  const vi = isVi();
  try {
    const data = await apiFetch("/api/cnf");
    const cnf = data.cnf;
    latestCNFData = cnf;

    el("cnfModalSubtitle").textContent = vi
      ? `Màn: ${cnf.puzzle_id} • Bước t = ${cnf.step_number} • Chế độ: ${cnf.encoding_mode} • ${cnf.num_primary_vars} Biến sơ cấp + ${cnf.num_aux_vars} Biến phụ • ${cnf.num_clauses} Mệnh đề`
      : `Puzzle: ${cnf.puzzle_id} • Step t = ${cnf.step_number} • Mode: ${cnf.encoding_mode} • ${cnf.num_primary_vars} Primary + ${cnf.num_aux_vars} Aux Vars • ${cnf.num_clauses} Total Clauses`;

    const symPane = el("cnfTabSymbolic");
    let symHtml = "";

    if (cnf.verdict_unit_clauses.length) {
      const unitChips = cnf.verdict_unit_clauses
        .map(
          (u) =>
            `<span class="clause-chip" title="${u.name} (${u.cell_id}) = ${u.status}">${u.symbolic}</span>`
        )
        .join("");
      symHtml += `
        <div class="cnf-group-box">
          <div class="cnf-group-header">
            <strong>${vi ? `Mệnh đề đơn cho các ô đã chứng minh (${cnf.verdict_unit_clauses.length})` : `Proved Verdict Unit Clauses (${cnf.verdict_unit_clauses.length})`}</strong>
            <span class="count-pill">Unit Clauses</span>
          </div>
          <div class="clause-list">${unitChips}</div>
        </div>`;
    }

    for (const grp of cnf.clue_groups) {
      const chips = grp.symbolic_clauses.length
        ? grp.symbolic_clauses.map((c) => `<span class="clause-chip">${c}</span>`).join("")
        : `<span class="clause-chip">⊤ (${vi ? "0 mệnh đề — luôn đúng" : "0 clauses — tautological"})</span>`;
      const dispText = vi && grp.text_vi ? grp.text_vi : grp.text;
      symHtml += `
        <div class="cnf-group-box">
          <div class="cnf-group-header">
            <span><strong>${grp.owner_name} (${grp.owner_cell})</strong> — "${dispText}"</span>
            <span class="count-pill">${grp.clue_type} • ${grp.clause_count} ${vi ? "mệnh đề" : "clause(s)"}</span>
          </div>
          <div class="clause-list">${chips}</div>
        </div>`;
    }
    symPane.innerHTML = symHtml || `<p>${vi ? "Chưa có mệnh đề nào." : "Knowledge base has 0 active clauses."}</p>`;

    const varPane = el("cnfTabVariables");
    const primRows = cnf.primary_variables
      .map(
        (v) =>
          `<tr><td><code>${v.var_id}</code></td><td><code>${v.symbol}</code></td><td>${v.name} (${v.cell_id})</td><td>${formatProfession(v.profession)}</td></tr>`
      )
      .join("");
    const auxRows = cnf.auxiliary_variables.length
      ? cnf.auxiliary_variables
          .map(
            (a) =>
              `<tr><td><code>${a.var_id}</code></td><td><code>${a.symbol}</code></td><td colspan="2">${vi ? "Biến phụ mã hóa (tách riêng hoàn toàn khỏi C_i)" : "Encoding Auxiliary Variable (kept strictly separate from C_i)"}</td></tr>`
          )
          .join("")
      : `<tr><td colspan="4" style="color:#64748b">${vi ? "Không có biến phụ nào trong KB_t hiện tại." : "0 auxiliary variables allocated in current KB_t."}</td></tr>`;

    varPane.innerHTML = `
      <h4 style="margin-bottom:6px">${vi ? `Biến Mệnh đề Sơ cấp C<sub>1</sub>..C<sub>${cnf.num_primary_vars}</sub>` : `Primary Propositional Variables C<sub>1</sub>..C<sub>${cnf.num_primary_vars}</sub>`}</h4>
      <table class="var-table">
        <thead><tr><th>DIMACS ID</th><th>${vi ? "Ký hiệu" : "Symbol"}</th><th>${vi ? "Nhân vật" : "Character"}</th><th>${vi ? "Nghề nghiệp" : "Profession"}</th></tr></thead>
        <tbody>${primRows}</tbody>
      </table>
      <h4 style="margin:10px 0 6px">${vi ? `Biến Phụ Mã hóa (${cnf.num_aux_vars})` : `Auxiliary Encoding Variables (${cnf.num_aux_vars})`}</h4>
      <table class="var-table">
        <thead><tr><th>DIMACS ID</th><th>${vi ? "Ký hiệu" : "Symbol"}</th><th colspan="2">${vi ? "Vai trò" : "Role"}</th></tr></thead>
        <tbody>${auxRows}</tbody>
      </table>`;

    el("cnfDimacsPre").textContent = cnf.dimacs_text;
    el("cnfModalBackdrop").hidden = false;
  } catch (err) {
    setBanner("contradicted", "ERROR", err.message);
  }
}

function downloadCurrentCNF() {
  if (!latestCNFData) return;
  const blob = new Blob([latestCNFData.dimacs_text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${latestCNFData.puzzle_id}_step${latestCNFData.step_number}.cnf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function submitVerdict(cellId, verdict) {
  stopAutoSolve();
  const vi = isVi();
  try {
    const data = await apiFetch("/api/verdict", "POST", { cell_id: cellId, verdict });
    const sub = data.submission;
    activeHighlight = null;
    updateUI(data);

    if (sub.status_code === "ACCEPTED") {
      if (data.state.is_solved) {
        setBanner(
          "accepted",
          "SOLVED",
          vi
            ? `HOÀN THÀNH XUẤT SẮC! Đã chứng minh toàn bộ ${data.state.total_cells} nhân vật mà không cần đoán mò!`
            : `Puzzle Solved! All ${data.state.total_cells} characters proved without guessing.`
        );
      } else {
        const newClueTxt = sub.revealed_clue ? getClueDisplayText(sub.revealed_clue) : "";
        setBanner(
          "accepted",
          "ACCEPTED",
          vi
            ? `CHÍNH XÁC: ${sub.character_name} (${sub.cell_id}) được chứng minh là ${formatStatusWord(sub.accepted_status)}!` +
                (newClueTxt ? ` Manh mối mới: "${newClueTxt}"` : "")
            : sub.message
        );
      }
    } else if (sub.status_code === "NOT_PROVABLE") {
      setBanner(
        "not-provable",
        "NOT_PROVABLE",
        vi
          ? `CHƯA ĐỦ CƠ SỞ (NOT_PROVABLE): Từ các manh mối đang mở, chưa thể chứng minh chắc chắn ${sub.character_name} (${sub.cell_id}) là Vô tội hay Tội phạm. Không được đoán mò!`
          : sub.message
      );
      shakeCard(cellId);
    } else if (sub.status_code === "CONTRADICTED") {
      setBanner(
        "contradicted",
        "CONTRADICTED",
        vi
          ? `MÂU THUẪN LOGIC (CONTRADICTED): Các manh mối hiện tại chứng minh kết quả NGƯỢC LẠI cho ${sub.character_name} (${sub.cell_id})!`
          : sub.message
      );
      shakeCard(cellId);
    } else {
      setBanner("not-provable", sub.status_code, sub.message);
      shakeCard(cellId);
    }
  } catch (err) {
    setBanner("contradicted", "ERROR", err.message);
  }
}

function shakeCard(cellId) {
  const cardEl = el(`card-${cellId}`);
  if (!cardEl) return;
  cardEl.classList.remove("shake");
  void cardEl.offsetWidth;
  cardEl.classList.add("shake");
}

async function toggleClueHighlight(cellId) {
  const vi = isVi();
  if (activeHighlight && activeHighlight.owner === cellId && !activeHighlight.hintTarget) {
    clearHighlightState();
    setBanner("info", vi ? "SẴN SÀNG" : "READY", vi ? "Đã tắt đánh dấu vùng manh mối." : "Clue highlight cleared.");
    return;
  }
  try {
    const data = await apiFetch(`/api/highlight/${cellId}`);
    const hl = data.highlight;
    activeHighlight = {
      owner: cellId,
      primary: new Set(hl.primary || []),
      secondary: new Set(hl.secondary || []),
      hintTarget: null,
    };
    renderBoard(currentPayload.state, new Set());
    const totalHl = activeHighlight.primary.size + activeHighlight.secondary.size;
    const clueTxt = vi && hl.text_vi ? hl.text_vi : hl.text;
    setBanner(
      "info",
      vi ? `MANH MỐI ${cellId}` : `CLUE ${cellId}`,
      vi
        ? `"${clueTxt}" — Đang tô sáng ${totalHl} ô liên quan.`
        : `"${clueTxt}" — Highlighting ${totalHl} referenced cell(s).`,
      true
    );
  } catch (err) {
    setBanner("contradicted", "ERROR", err.message);
  }
}

async function requestHint() {
  stopAutoSolve();
  const vi = isVi();
  try {
    const data = await apiFetch("/api/hint", "POST");
    const h = data.hint;
    if (!h.available) {
      let msg = h.message;
      if (vi) {
        if (h.terminal_state === "SOLVED") msg = "Bàn cờ đã được giải hoàn tất!";
        else if (h.terminal_state === "INCONSISTENT") msg = "Kho tri thức hiện tại đang mâu thuẫn (UNSAT)!";
        else msg = "Hiện không có nghi phạm nào đủ dữ kiện để chứng minh chắc chắn từ các thẻ đang mở.";
      }
      setBanner("not-provable", h.terminal_state, msg);
      return;
    }
    activeHighlight = {
      owner: null,
      primary: new Set(h.relevant_clue_cells || []),
      secondary: new Set(h.supporting_verdict_cells || []),
      hintTarget: h.target_cell,
    };
    renderBoard(currentPayload.state, new Set());

    let msg = h.message;
    if (vi) {
      const srcCells = (h.relevant_clue_cells || []).join(", ");
      msg = srcCells
        ? `Gợi ý: Bạn có thể suy luận chắc chắn thân phận của ${h.target_name} (${h.target_cell}) tiếp theo dựa vào manh mối ở ô ${srcCells}!`
        : `Gợi ý: Ô ${h.target_name} (${h.target_cell}) đã đủ dữ kiện để chứng minh tiếp theo!`;
    }
    setBanner("hint", vi ? "GỢI Ý" : "HINT", msg, true);
  } catch (err) {
    setBanner("contradicted", "ERROR", err.message);
  }
}

async function runSingleStep() {
  const vi = isVi();
  try {
    const data = await apiFetch("/api/step", "POST");
    const tr = data.step_trace;

    if (tr.chosen_cell) {
      activeHighlight = {
        owner: tr.chosen_cell,
        primary: new Set([tr.chosen_cell]),
        secondary: new Set(),
        hintTarget: null,
      };
      updateUI(data);
      if (tr.terminal_state === "SOLVED") {
        setBanner(
          "accepted",
          "SOLVED",
          vi
            ? `Bước #${tr.step_number}: Chứng minh ${tr.chosen_character} (${tr.chosen_cell}) = ${formatStatusWord(tr.verdict)}. Đã giải xong toàn bộ bàn cờ!`
            : `Step #${tr.step_number}: Proved ${tr.chosen_character} (${tr.chosen_cell}) = ${tr.verdict}. Puzzle completely solved!`
        );
        stopAutoSolve();
      } else {
        setBanner(
          "accepted",
          vi ? `BƯỚC #${tr.step_number}` : `STEP #${tr.step_number}`,
          vi
            ? `Đã chứng minh ${tr.chosen_character} (${tr.chosen_cell}) = ${formatStatusWord(tr.verdict)} (${tr.sat_queries_count} lần gọi SAT).`
            : `Proved ${tr.chosen_character} (${tr.chosen_cell}) = ${tr.verdict} (${tr.sat_queries_count} SAT calls).`,
          true
        );
      }
      return true;
    } else {
      updateUI(data);
      setBanner(
        tr.terminal_state === "INCONSISTENT" ? "contradicted" : "not-provable",
        tr.terminal_state,
        tr.terminal_state === "INCONSISTENT"
          ? vi
            ? "Kho tri thức KB_t mâu thuẫn (UNSAT — các manh mối xung đột nhau)!"
            : "Knowledge base KB_t is UNSAT (inconsistent clues)!"
          : vi
            ? "Không còn ô nào có thể chứng minh chắc chắn (STUCK). Tác tử dừng lại, tuyệt đối không đoán mò!"
            : "No unresolved character is logically forced (UNKNOWN). Agent refuses to guess."
      );
      stopAutoSolve();
      return false;
    }
  } catch (err) {
    stopAutoSolve();
    setBanner("contradicted", "ERROR", err.message);
    return false;
  }
}

function stopAutoSolve() {
  if (autoSolveTimer !== null) {
    clearTimeout(autoSolveTimer);
    autoSolveTimer = null;
  }
  const btn = el("btnAutoSolve");
  btn.textContent = isVi() ? "Tự động giải" : "Auto Solve";
  btn.className = "btn btn-accent";
}

async function toggleAutoSolve() {
  const vi = isVi();
  if (autoSolveTimer !== null) {
    stopAutoSolve();
    setBanner("info", vi ? "TẠM DỪNG" : "PAUSED", vi ? "Đã tạm dừng giải tự động." : "Auto Solve paused.");
    return;
  }

  const delayMs = parseInt(el("speedSelect").value, 10);
  if (delayMs === 0) {
    try {
      const data = await apiFetch("/api/auto_solve", "POST");
      activeHighlight = null;
      updateUI(data);
      const rep = data.report;
      if (rep.terminal_state === "SOLVED") {
        setBanner(
          "accepted",
          "SOLVED",
          vi
            ? `Đã giải xong sau ${rep.deduction_steps} bước (${rep.reveal_waves} đợt mở thẻ, ${rep.total_sat_calls} lần gọi SAT, ${rep.wall_runtime_ms.toFixed(2)} ms).`
            : `Solved in ${rep.deduction_steps} steps (${rep.reveal_waves} waves, ${rep.total_sat_calls} SAT calls, ${rep.wall_runtime_ms.toFixed(2)} ms).`
        );
      } else {
        setBanner(
          rep.terminal_state === "INCONSISTENT" ? "contradicted" : "not-provable",
          rep.terminal_state,
          vi
            ? `Tác tử dừng ở trạng thái ${rep.terminal_state} sau ${rep.deduction_steps} bước (không đoán mò).`
            : `Agent halted at ${rep.terminal_state} after ${rep.deduction_steps} step(s) without guessing.`
        );
      }
    } catch (err) {
      setBanner("contradicted", "ERROR", err.message);
    }
    return;
  }

  const btn = el("btnAutoSolve");
  btn.textContent = vi ? "Dừng" : "Stop";
  btn.className = "btn btn-danger";

  async function tick() {
    if (currentPayload && currentPayload.state.is_solved) {
      stopAutoSolve();
      return;
    }
    const progressed = await runSingleStep();
    if (progressed && autoSolveTimer !== null && !currentPayload.state.is_solved) {
      autoSolveTimer = setTimeout(tick, delayMs);
    } else {
      stopAutoSolve();
    }
  }

  autoSolveTimer = setTimeout(tick, 40);
}

async function checkUniqueness() {
  stopAutoSolve();
  const vi = isVi();
  try {
    const data = await apiFetch("/api/uniqueness", "POST");
    const u = data.uniqueness;
    const box = el("uniquenessBox");
    const content = el("uniquenessContent");
    box.hidden = false;

    if (!u.is_consistent) {
      content.innerHTML = vi
        ? `<div class="uniq-warn"><strong>MÂU THUẪN (UNSAT):</strong> Tập toàn bộ manh mối không có nghiệm hợp lệ nào (${u.num_clauses} mệnh đề, ${u.sat_calls} lần gọi SAT).</div>`
        : `<div class="uniq-warn"><strong>INCONSISTENT (UNSAT):</strong> The complete clue set has 0 valid assignments (${u.num_clauses} clauses, ${u.sat_calls} SAT call).</div>`;
    } else if (u.is_unique) {
      content.innerHTML = vi
        ? `<div class="uniq-ok"><strong>NGHIỆM DUY NHẤT HỢP LỆ:</strong> Có duy nhất 1 cách phân bổ Tội phạm/Vô tội thỏa mãn toàn bộ ${u.num_primary_vars} nhân vật (${u.num_aux_vars} biến phụ, ${u.num_clauses} mệnh đề, ${u.sat_calls} lần gọi SAT, ${u.stats.runtime_ms.toFixed(2)} ms).</div>`
        : `<div class="uniq-ok"><strong>UNIQUE SOLUTION VERIFIED:</strong> Exactly 1 valid Criminal/Innocent assignment exists across all ${u.num_primary_vars} characters (${u.num_aux_vars} aux vars, ${u.num_clauses} clauses, ${u.sat_calls} SAT calls, ${u.stats.runtime_ms.toFixed(2)} ms).</div>`;
    } else {
      content.innerHTML = vi
        ? `<div class="uniq-warn"><strong>ĐA NGHIỆM (MƠ HỒ):</strong> Tồn tại nhiều hơn 1 nghiệm thỏa mãn toàn bộ manh mối. Các ô có thể đổi trạng thái: <code>${u.differing_cells.join(", ")}</code>.</div>`
        : `<div class="uniq-warn"><strong>AMBIGUOUS (MULTIPLE SOLUTIONS):</strong> Multiple assignments satisfy all clues. Differing cells: <code>${u.differing_cells.join(", ")}</code>.</div>`;
    }
  } catch (err) {
    setBanner("contradicted", "ERROR", err.message);
  }
}

async function updateSettings() {
  stopAutoSolve();
  const vi = isVi();
  try {
    const data = await apiFetch("/api/settings", "POST", {
      encoding_mode: el("selEncoding").value,
      heuristic: el("selHeuristic").value,
      use_pure_literal: el("chkPureLiteral").checked,
      use_witness_pruning: el("chkWitnessPruning").checked,
    });
    updateUI(data, true);
    setBanner(
      "info",
      vi ? "ĐÃ CẬP NHẬT" : "UPDATED",
      vi ? "Đã cập nhật cấu hình bộ mã hóa CNF và bộ giải DPLL." : "CNF Encoder and DPLL Solver configuration updated."
    );
  } catch (err) {
    setBanner("contradicted", "ERROR", err.message);
  }
}

function setupModalTabs() {
  const btns = document.querySelectorAll(".tab-btn");
  btns.forEach((btn) => {
    btn.addEventListener("click", () => {
      btns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const target = btn.getAttribute("data-tab");
      el("cnfTabSymbolic").hidden = target !== "symbolic";
      el("cnfTabVariables").hidden = target !== "variables";
      el("cnfTabDimacs").hidden = target !== "dimacs";
    });
  });

  el("btnCloseCNFModal").addEventListener("click", () => {
    el("cnfModalBackdrop").hidden = true;
  });
  el("cnfModalBackdrop").addEventListener("click", (ev) => {
    if (ev.target === el("cnfModalBackdrop")) {
      el("cnfModalBackdrop").hidden = true;
    }
  });
  el("btnDownloadCNF").addEventListener("click", downloadCurrentCNF);
}

async function initApp() {
  setupModalTabs();

  const cat = await apiFetch("/api/puzzles");
  catalogItems = cat.puzzles || [];
  applyStaticTranslations();

  const select = el("puzzleSelect");
  for (const opt of select.options) {
    if (opt.value === cat.current_puzzle_id) opt.selected = true;
  }

  const stateData = await apiFetch("/api/state");
  updateUI(stateData, true);

  el("btnLangToggle").addEventListener("click", () => {
    currentLang = currentLang === "vi" ? "en" : "vi";
    applyStaticTranslations();
    setBanner(
      "info",
      isVi() ? "TIẾNG VIỆT" : "ENGLISH",
      isVi()
        ? "Đã chuyển giao diện và toàn bộ manh mối sang Tiếng Việt!"
        : "Switched interface and all card clues to English!"
    );
  });

  select.addEventListener("change", async () => {
    stopAutoSolve();
    activeHighlight = null;
    el("uniquenessBox").hidden = true;
    const data = await apiFetch("/api/load", "POST", { puzzle_id: select.value });
    updateUI(data, true);
    setBanner(
      "info",
      isVi() ? "ĐÃ TẢI MÀN" : "LOADED",
      isVi()
        ? `Đã mở màn: ${formatPuzzleTitle(data.state.puzzle_id, data.state.title)}`
        : `Loaded stage: ${data.state.title}`
    );
  });

  el("jsonFileInput").addEventListener("change", async (ev) => {
    stopAutoSolve();
    const file = ev.target.files[0];
    if (!file) return;
    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
      activeHighlight = null;
      el("uniquenessBox").hidden = true;
      const data = await apiFetch("/api/load", "POST", { puzzle_json: parsed });
      updateUI(data, true);
      setBanner(
        "accepted",
        "JSON",
        isVi() ? `Đã tải màn tùy chỉnh: ${data.state.title}` : `Loaded custom puzzle: ${data.state.title}`
      );
    } catch (err) {
      setBanner("contradicted", "INVALID JSON", err.message);
    } finally {
      ev.target.value = "";
    }
  });

  el("btnRestart").addEventListener("click", async () => {
    stopAutoSolve();
    activeHighlight = null;
    el("uniquenessBox").hidden = true;
    const data = await apiFetch("/api/restart", "POST");
    updateUI(data, true);
    setBanner(
      "info",
      isVi() ? "CHƠI LẠI" : "RESTARTED",
      isVi() ? "Đã đặt lại bàn cờ về các thẻ mở ban đầu." : "Board reset to initial opening cards."
    );
  });

  el("btnHint").addEventListener("click", requestHint);
  el("btnInspectCNF").addEventListener("click", openCNFModal);
  el("btnQuickCNF").addEventListener("click", openCNFModal);
  el("btnStep").addEventListener("click", () => {
    stopAutoSolve();
    runSingleStep();
  });
  el("btnAutoSolve").addEventListener("click", toggleAutoSolve);
  el("btnUniqueness").addEventListener("click", checkUniqueness);
  el("btnClearHighlight").addEventListener("click", clearHighlightState);
  el("btnCloseUniq").addEventListener("click", () => {
    el("uniquenessBox").hidden = true;
  });

  el("selEncoding").addEventListener("change", updateSettings);
  el("selHeuristic").addEventListener("change", updateSettings);
  el("chkPureLiteral").addEventListener("change", updateSettings);
  el("chkWitnessPruning").addEventListener("change", updateSettings);
}

window.addEventListener("DOMContentLoaded", initApp);
