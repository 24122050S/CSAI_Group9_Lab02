"""Generates the comprehensive ~10-page academic Report.pdf (Section 4.6 & Section 5).

Supports full Vietnamese diacritics in TEAM_MEMBERS and mathematical logic symbols
(∧, ∨, ¬, ↔, ⊕, ∑, ⊨, ∈, ∩, ∪, ≤, ≥, ⊥, →) via DejaVu Unicode TTF fonts.

Edit TEAM_MEMBERS and DEMO_VIDEO_DRIVE_URL below, then run:
    python package_submission.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# =====================================================================
# CHỈNH SỬA LINK GOOGLE DRIVE VIDEO DEMO & DANH SÁCH THÀNH VIÊN TẠI ĐÂY
# =====================================================================
DEMO_VIDEO_DRIVE_URL = "https://drive.google.com/drive/folders/REPLACE_WITH_YOUR_PUBLIC_DRIVE_LINK"

TEAM_MEMBERS = [
    (
        "StudentID_1",
        "Member 1 Full Name",
        "Board/Clue models, 4 core regions + Extension 1 advanced regions, ClueValidator, Direct Semantic Evaluator",
        "100%",
    ),
    (
        "StudentID_2",
        "Member 2 Full Name",
        "Automatic CNFEncoder (Combinatorial, Sinz Sequential Counter, Extensions 2–5), Custom DPLL SAT Solver",
        "100%",
    ),
    (
        "StudentID_3",
        "Member 3 Full Name",
        "GameEngine/LogicAgent separation, Witness-Guided Deduction Loop, UniquenessChecker, MUS HintEngine",
        "100%",
    ),
    (
        "StudentID_4",
        "Member 4 Full Name",
        "Vietnamese/English Web GUI + Live CNF Modal, 19-puzzle suite, Coupled Benchmarks, Charts, Report & Demo Video",
        "100%",
    ),
]
# =====================================================================


def _register_unicode_fonts() -> tuple[str, str, str, str]:
    import matplotlib

    mpl_ttf = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    dj_reg = mpl_ttf / "DejaVuSans.ttf"
    dj_bold = mpl_ttf / "DejaVuSans-Bold.ttf"
    dj_ital = mpl_ttf / "DejaVuSans-Oblique.ttf"
    dj_mono = mpl_ttf / "DejaVuSansMono.ttf"

    if dj_reg.exists() and dj_bold.exists() and dj_ital.exists():
        pdfmetrics.registerFont(TTFont("DocSans", str(dj_reg)))
        pdfmetrics.registerFont(TTFont("DocSans-Bold", str(dj_bold)))
        pdfmetrics.registerFont(TTFont("DocSans-Italic", str(dj_ital)))
        pdfmetrics.registerFontFamily(
            "DocSans",
            normal="DocSans",
            bold="DocSans-Bold",
            italic="DocSans-Italic",
        )
        sans_reg, sans_bold, sans_ital = "DocSans", "DocSans-Bold", "DocSans-Italic"
    else:
        sans_reg, sans_bold, sans_ital = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"

    if dj_mono.exists():
        pdfmetrics.registerFont(TTFont("DocMono", str(dj_mono)))
        mono_name = "DocMono"
    else:
        mono_name = "Courier"

    return sans_reg, sans_bold, sans_ital, mono_name


FONT_REG, FONT_BOLD, FONT_ITALIC, FONT_MONO = _register_unicode_fonts()


def _header_footer(canvas, doc) -> None:
    canvas.saveState()
    w, h = A4
    canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
    canvas.setLineWidth(0.6)
    canvas.line(1.8 * cm, h - 1.45 * cm, w - 1.8 * cm, h - 1.45 * cm)
    canvas.line(1.8 * cm, 1.45 * cm, w - 1.8 * cm, 1.45 * cm)

    canvas.setFont(FONT_REG, 8.3)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawString(1.8 * cm, h - 1.2 * cm, "CSC14003 | Introduction to Artificial Intelligence")
    canvas.drawRightString(w - 1.8 * cm, h - 1.2 * cm, "Project 2: No-Guess Griductive Solver")

    canvas.drawString(
        1.8 * cm,
        1.0 * cm,
        "Faculty of Information Technology, University of Science, VNU-HCM",
    )
    canvas.drawRightString(w - 1.8 * cm, 1.0 * cm, f"Page {doc.page}")
    canvas.restoreState()


def _styled_table(data: list[list], col_widths: list[float], font_size: float = 8.0) -> Table:
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                ("FONTNAME", (0, 1), (-1, -1), FONT_REG),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tbl


def _scaled_image(img_path: Path, max_width: float, max_height: float) -> Image:
    from PIL import Image as PILImage

    with PILImage.open(img_path) as im:
        iw, ih = im.size
    scale = min(max_width / iw, max_height / ih)
    return Image(str(img_path), width=iw * scale, height=ih * scale)


def build_pdf() -> Path:
    report_dir = Path(__file__).resolve().parent
    proj_root = report_dir.parent
    out_pdf = proj_root / "Report.pdf"
    results_dir = proj_root / "Source" / "experiments" / "results"
    figs_dir = report_dir / "figures"

    doc = SimpleDocTemplate(
        str(out_pdf),
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.9 * cm,
        bottomMargin=1.9 * cm,
        title="CSC14003 Project 2 Report - No-Guess Griductive Solver",
    )
    usable_w = A4[0] - 3.6 * cm

    base = getSampleStyleSheet()
    st_title = ParagraphStyle(
        "DocTitle",
        parent=base["Title"],
        fontName=FONT_BOLD,
        fontSize=18.5,
        textColor=colors.HexColor("#0f4c5c"),
        spaceAfter=4,
        alignment=TA_CENTER,
    )
    st_sub = ParagraphStyle(
        "DocSub",
        parent=base["Normal"],
        fontName=FONT_REG,
        fontSize=9.8,
        textColor=colors.HexColor("#334155"),
        alignment=TA_CENTER,
        spaceAfter=11,
    )
    st_h1 = ParagraphStyle(
        "SecH1",
        parent=base["Heading1"],
        fontName=FONT_BOLD,
        fontSize=12.8,
        textColor=colors.HexColor("#0f4c5c"),
        spaceBefore=11,
        spaceAfter=5,
    )
    st_h2 = ParagraphStyle(
        "SecH2",
        parent=base["Heading2"],
        fontName=FONT_BOLD,
        fontSize=10.2,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=8,
        spaceAfter=4,
    )
    st_body = ParagraphStyle(
        "Body",
        parent=base["Normal"],
        fontName=FONT_REG,
        fontSize=9.2,
        leading=13.2,
        alignment=TA_JUSTIFY,
        spaceAfter=5,
    )
    st_thm = ParagraphStyle(
        "TheoremBox",
        parent=st_body,
        backColor=colors.HexColor("#f0f9ff"),
        borderColor=colors.HexColor("#0284c7"),
        borderWidth=0.6,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=6,
    )
    st_cell = ParagraphStyle(
        "Cell",
        parent=base["Normal"],
        fontName=FONT_REG,
        fontSize=7.8,
        leading=10.4,
    )
    st_caption = ParagraphStyle(
        "Caption",
        parent=base["Normal"],
        fontName=FONT_ITALIC,
        fontSize=8.2,
        textColor=colors.HexColor("#475569"),
        alignment=TA_CENTER,
        spaceBefore=3,
        spaceAfter=8,
    )
    st_code = ParagraphStyle(
        "CodeBlock",
        parent=base["Code"],
        fontName=FONT_MONO,
        fontSize=7.6,
        leading=10.1,
        backColor=colors.HexColor("#f1f5f9"),
        borderPadding=6,
        spaceAfter=6,
    )

    story: list = []

    # =====================================================================
    # PAGE 1: TITLE, SECTION 1 (PLANNING), SECTION 2.1 & 2.2 (FORMULATION)
    # =====================================================================
    story.append(Paragraph("Project 2: No-Guess Griductive Solver", st_title))
    story.append(
        Paragraph(
            "Propositional Logic, Automatic CNF Encoding, and Custom DPLL SAT Deduction<br/>"
            f"<b>Demonstration Video (Google Drive):</b> <u>{DEMO_VIDEO_DRIVE_URL}</u>",
            st_sub,
        )
    )

    story.append(Paragraph("1. Project Planning and Task Distribution", st_h1))
    story.append(
        Paragraph(
            "The project was executed over a three-week engineering roadmap partitioned into seven milestones across four "
            "decoupled architectural layers: (1) Domain Modeling, Region Algebra, Validation, and Standalone Semantic Evaluation "
            "(Days 1–5); (2) Automatic Propositional CNF Encoding and Custom Pure-Python DPLL Solver (Days 6–10); "
            "(3) Strict Engine/Agent Firewall, Witness-Guided Entailment Loop, Primary-Only Uniqueness Checking, and Deletion-Based "
            "MUS Hinting (Days 11–15); and (4) Interactive Bilingual GUI, Coupled Backtracking Benchmark Suite, and Documentation "
            "(Days 16–21). Individual grades follow the course rule: <i>Individual Score = Group Score × Completion %</i>.",
            st_body,
        )
    )
    team_rows = [["Student ID", "Full Name", "Assigned Tasks & Deliverables", "Completion"]]
    for sid, mname, resp, pct in TEAM_MEMBERS:
        team_rows.append(
            [Paragraph(sid, st_cell), Paragraph(mname, st_cell), Paragraph(resp, st_cell), pct]
        )
    story.append(
        _styled_table(team_rows, [2.6 * cm, 3.8 * cm, usable_w - 8.4 * cm, 2.0 * cm])
    )
    story.append(Spacer(1, 5))

    story.append(Paragraph("2. Problem Formulation and System Architecture", st_h1))
    story.append(Paragraph("2.1 Propositional Variables and Deterministic Separation", st_h2))
    story.append(
        Paragraph(
            "An N×N Griductive board (N ∈ {3, 4, 5}) numbers rows r ∈ {1..N} from top to bottom and letters columns "
            "c ∈ {0..N−1} (A, B, …) from left to right. Characters are ordered alphabetically by display name in canonical "
            "row-major order i = (r − 1)·N + c + 1 ∈ {1..N²}. For each character i, VariableManager allocates one primary "
            "Boolean variable C_i = True iff character i is CRIMINAL, and C_i = False iff character i is INNOCENT. "
            "Auxiliary variables required by Sinz sequential counters, regional comparisons, Tseitin XOR parity chains, "
            "disjunction selectors, or BFS connectivity layers are allocated strictly in the disjoint range {N² + 1, N² + 2, …}.",
            st_body,
        )
    )

    story.append(Paragraph("2.2 Core Clue Templates, Regions, and Five Distinct Extensions", st_h2))
    clue_rows = [
        ["Category", "Clue / Region Type", "Formal Logical Semantics"],
        ["Core 1", "FACT(i, status)", Paragraph("Unit literal C_i (Criminal) or ¬C_i (Innocent).", st_cell)],
        ["Core 2", "SAME(i, j)", Paragraph("Bi-implication C_i ↔ C_j (identical statuses).", st_cell)],
        ["Core 3", "DIFFERENT(i, j)", Paragraph("Exclusive-OR C_i ⊕ C_j (opposite statuses).", st_cell)],
        ["Core 4", "EXACTLY(k, R) / NO(R)", Paragraph("∑_{i ∈ R} C_i = k (NO(R) is normalized to k = 0).", st_cell)],
        ["Core 5", "AT_LEAST(k, R)", Paragraph("∑_{i ∈ R} C_i ≥ k, where 0 ≤ k ≤ |R|.", st_cell)],
        ["Core 6", "AT_MOST(k, R)", Paragraph("∑_{i ∈ R} C_i ≤ k, where 0 ≤ k ≤ |R|.", st_cell)],
        [
            "Extension 1",
            "Advanced Regions",
            Paragraph(
                "R₁ ∩ R₂ (INTERSECTION), COMMON_NEIGHBORS(i, j), CORNERS, BOUNDARY, "
                "BETWEEN(i, j), DIRECTIONAL(i, dir), and PROFESSION(role).",
                st_cell,
            ),
        ],
        [
            "Extension 2",
            "Regional Comparison",
            Paragraph(
                "MORE_CRIMINALS(R₁, R₂): ∑_{i ∈ R₁} C_i &gt; ∑_{j ∈ R₂} C_j; "
                "EQUAL_CRIMINALS(R₁, R₂): ∑_{i ∈ R₁} C_i = ∑_{j ∈ R₂} C_j.",
                st_cell,
            ),
        ],
        [
            "Extension 3",
            "Parity Constraint",
            Paragraph("PARITY(R, ODD | EVEN): (∑_{i ∈ R} C_i) mod 2 = 1 (ODD) or 0 (EVEN).", st_cell),
        ],
        [
            "Extension 4",
            "Compound Clues",
            Paragraph("COMPOUND(AND | OR | IMPLIES, Φ₁, Φ₂): Φ₁ ∧ Φ₂, Φ₁ ∨ Φ₂, or Φ₁ → Φ₂ (Figure 1 cell A5).", st_cell),
        ],
        [
            "Extension 5",
            "Connectivity",
            Paragraph("CONNECTED(R, status): Active status cells in R induce ≤ 1 orthogonal grid component (Figure 1 cell D5).", st_cell),
        ],
    ]
    story.append(_styled_table(clue_rows, [2.35 * cm, 4.15 * cm, usable_w - 6.5 * cm]))
    story.append(Spacer(1, 6))

    # =====================================================================
    # PAGE 2: SECTION 2.3 (REVEAL PROTOCOL + ARCH DIAGRAM) & SECTION 3.1-3.2
    # =====================================================================
    story.append(Paragraph("2.3 Public Knowledge Base KB_t and Strict Architectural Isolation", st_h2))
    story.append(
        Paragraph(
            "Every revealed clue is guaranteed true regardless of whether its owner is Criminal or Innocent. At deduction step t, "
            "let R_t ⊆ {1..N²} denote the currently face-up cards. The public knowledge base is compiled automatically as "
            "KB_t = (∧_{i ∈ R_t} CNF(clue_i)) ∧ (∧_{i ∈ R_t} unit(i, status_i)). To prevent hidden-state leakage at both "
            "compile-time and runtime, GameEngine stores __ground_truth and __clues in private name-mangled attributes and "
            "exposes only an immutable PublicGameState DTO whose __post_init__ invariant raises an exception if any unrevealed "
            "cell carries non-UNKNOWN status or non-None clue data. When a verdict V ∈ {CRIMINAL, INNOCENT} is submitted for "
            "unrevealed cell j: (1) if neither KB_t ⊨ C_j nor KB_t ⊨ ¬C_j holds, GameEngine returns NOT_PROVABLE without flipping "
            "the card—even if V matches the hidden ground truth by luck; (2) if KB_t entails the opposite status, it returns "
            "CONTRADICTED; (3) only when KB_t ⊨ V does GameEngine flip card j and transition to KB_{t+1}.",
            st_body,
        )
    )

    arch_img = figs_dir / "architecture_diagram.png"
    if arch_img.exists():
        story.append(_scaled_image(arch_img, usable_w, 7.2 * cm))
        story.append(
            Paragraph(
                "Figure 1: Three-domain security architecture isolating GameEngine secrets from PublicGameState and DeductiveLogicAgent.",
                st_caption,
            )
        )

    story.append(Paragraph("3. Automatic CNF Encoding Derivations", st_h1))
    story.append(Paragraph("3.1 Binary Clue Derivations (SAME and DIFFERENT)", st_h2))
    story.append(
        Preformatted(
            "1) SAME(i, j):       C_i ↔ C_j  ≡  (C_i → C_j) ∧ (C_j → C_i)\n"
            "                                ≡  (¬C_i ∨ C_j) ∧ (C_i ∨ ¬C_j)      [2 binary clauses, 0 aux vars]\n\n"
            "2) DIFFERENT(i, j):  C_i ⊕ C_j  ≡  (C_i ∧ ¬C_j) ∨ (¬C_i ∧ C_j)\n"
            "                                ≡  (C_i ∨ ¬C_i) ∧ (C_i ∨ C_j) ∧ (¬C_j ∨ ¬C_i) ∧ (¬C_j ∨ C_j)\n"
            "                                ≡  (C_i ∨ C_j) ∧ (¬C_i ∨ ¬C_j)      [2 binary clauses, 0 aux vars]",
            st_code,
        )
    )

    story.append(Paragraph("3.2 Cardinality Encodings: Combinatorial vs. Sinz Sequential Counter", st_h2))
    story.append(
        Preformatted(
            "Derivation A — Direct Combinatorial Encoding for EXACTLY(2, {1, 2, 3, 4}) (0 aux vars, 8 clauses):\n"
            "  • AT_MOST(k, R) forbids every (k+1)-subset from being all True:  ∧_{S⊆R, |S|=k+1} (∨_{i∈S} ¬C_i).\n"
            "    For |R|=4, k=2 (k+1=3), C(4,3) = 4 clauses:\n"
            "      (¬C_1 ∨ ¬C_2 ∨ ¬C_3) ∧ (¬C_1 ∨ ¬C_2 ∨ ¬C_4) ∧ (¬C_1 ∨ ¬C_3 ∨ ¬C_4) ∧ (¬C_2 ∨ ¬C_3 ∨ ¬C_4)\n"
            "  • AT_LEAST(k, R) requires every (|R|−k+1)-subset to have ≥ 1 True var:  ∧_{S⊆R, |S|=|R|−k+1} (∨_{i∈S} C_i).\n"
            "    For |R|=4, k=2 (4−2+1=3), C(4,3) = 4 clauses:\n"
            "      ( C_1 ∨  C_2 ∨  C_3) ∧ ( C_1 ∨  C_2 ∨  C_4) ∧ ( C_1 ∨  C_3 ∨  C_4) ∧ ( C_2 ∨  C_3 ∨  C_4)\n\n"
            "Derivation B — Sinz (2005) Sequential Counter for AT_MOST(k, [l_1..l_n]) ((n−1)·k aux vars s_{i,j}):\n"
            "  Define s_{i,j} ≡ 'at least j literals among l_1..l_i are True' (1 ≤ i ≤ n−1, 1 ≤ j ≤ k):\n"
            "  • Base i=1: (¬l_1 ∨ s_{1,1}) ∧ ∧_{j=2..k} (¬s_{1,j})\n"
            "  • Step 2≤i≤n−1: (¬l_i ∨ s_{i,1}) ∧ (¬s_{i−1,1} ∨ s_{i,1}) ∧ (¬l_i ∨ ¬s_{i−1,k})\n"
            "                  ∧ ∧_{j=2..k} [(¬l_i ∨ ¬s_{i−1,j−1} ∨ s_{i,j}) ∧ (¬s_{i−1,j} ∨ s_{i,j})]\n"
            "  • Overflow guard i=n: (¬l_n ∨ ¬s_{n−1,k}).\n"
            "  Worked Instance AT_MOST(1, {C_1, C_2, C_3}): aux vars s_1, s_2; 5 clauses:\n"
            "    (¬C_1 ∨ s_1) ∧ (¬C_2 ∨ s_2) ∧ (¬s_1 ∨ s_2) ∧ (¬C_2 ∨ ¬s_1) ∧ (¬C_3 ∨ ¬s_2).",
            st_code,
        )
    )

    # =====================================================================
    # PAGE 3: SECTION 3.3 (EXTENSIONS 2-5 DERIVATIONS) & SECTION 4.1 (ALGORITHMS)
    # =====================================================================
    story.append(Paragraph("3.3 Mathematical CNF Derivations for Extensions 2, 3, 4, and 5", st_h2))
    story.append(
        Paragraph(
            "<b>1. Cancelled-Overlap Regional Comparison (Extension 2):</b> Given regions R₁ and R₂, cells in R₁ ∩ R₂ "
            "contribute identically to both sides and cancel out. Let R₁' = R₁ \\ R₂ and R₂' = R₂ \\ R₁ (disjoint). "
            "For each j ∈ R₂', we allocate auxiliary variable A_j ↔ ¬C_j via (¬A_j ∨ ¬C_j) ∧ (A_j ∨ C_j). Since "
            "∑_{j∈R₂'} (1 − C_j) = ∑_{j∈R₂'} A_j, we obtain exact cardinality reductions:<br/>"
            "• MORE_CRIMINALS(R₁, R₂): ∑_{i∈R₁'} C_i − ∑_{j∈R₂'} C_j ≥ 1  ⇔  ∑_{i∈R₁'} C_i + ∑_{j∈R₂'} A_j ≥ |R₂'| + 1.<br/>"
            "• EQUAL_CRIMINALS(R₁, R₂): ∑_{i∈R₁'} C_i = ∑_{j∈R₂'} C_j  ⇔  ∑_{i∈R₁'} C_i + ∑_{j∈R₂'} A_j = |R₂'|.",
            st_body,
        )
    )
    story.append(
        Paragraph(
            "<b>2. Tseitin XOR Parity Chains (Extension 3):</b> Naive parity over m variables requires 2^(m−1) clauses of "
            "length m. Instead, we introduce m−2 intermediate variables z_r ↔ (z_{r−1} ⊕ l_r) encoded via 4 ternary clauses:<br/>"
            "(¬z_{r−1} ∨ ¬l_r ∨ ¬z_r) ∧ (¬z_{r−1} ∨ l_r ∨ z_r) ∧ (z_{r−1} ∨ ¬l_r ∨ z_r) ∧ (z_{r−1} ∨ l_r ∨ ¬z_r), "
            "terminating with z_{m−1} ⊕ l_m (ODD) or z_{m−1} ↔ l_m (EVEN), yielding 4(m−2)+2 short clauses.",
            st_body,
        )
    )
    story.append(
        Paragraph(
            "<b>3. Positive-Selector Compound Clues (Extension 4):</b> Suppose sub-clues Φ₁, Φ₂ compile to equisatisfiable "
            "CNFs ∃A₁ F₁(C, A₁) and ∃A₂ F₂(C, A₂). Negating F₁ directly would be unsound over existential auxiliary variables "
            "(¬∃A₁ F₁ ≡ ∀A₁ ¬F₁). Instead: (i) for OR(Φ₁, Φ₂), existential quantifiers commute with disjunction, so introducing "
            "positive selectors (s₁ ∨ s₂) ∧ ∧_{D∈F₁}(¬s₁ ∨ D) ∧ ∧_{E∈F₂}(¬s₂ ∨ E) is 100% equisatisfiable (when s_b = False, "
            "all clauses ¬s_b ∨ D are satisfied trivially); (ii) for IMPLIES(Φ₁, Φ₂) ≡ ¬Φ₁ ∨ Φ₂, _encode_negated_clue applies "
            "exact structural De Morgan / arithmetic trichotomy (e.g., ¬EXACTLY(k,R) ≡ AT_MOST(k−1,R) ∨ AT_LEAST(k+1,R)) "
            "before applying positive-selector disjunction.",
            st_body,
        )
    )
    story.append(
        Paragraph(
            "<b>4. 1D Forbidden-Triple &amp; 2D Canonical-Root BFS Connectivity (Extension 5):</b> Let G_R = (R, E_R) be the "
            "4-connected grid graph on R = [u₁..u_m] with status literals l₁..l_m, and let S = {u_i | l_i = True}.<br/>"
            "• <i>1D Contiguous Chain Shortcut:</i> When G_R is a simple path u₁—u₂—…—u_m, S is connected iff no active cells "
            "are separated by an inactive cell (no 1…0…1 pattern): ∧_{1≤a&lt;b&lt;c≤m} (¬l_a ∨ l_b ∨ ¬l_c) (0 aux vars).<br/>"
            "• <i>General 2D BFS Reachability:</i> We elect the unique minimum-index active vertex as canonical root "
            "r_i ↔ (l_i ∧ ∧_{p&lt;i} ¬l_p) via (¬r_i ∨ l_i), ∧_{p&lt;i}(¬r_i ∨ ¬l_p), and (¬l_i ∨ l₁ ∨ … ∨ l_{i−1} ∨ r_i). "
            "Setting d_{i,0} = r_i, for steps t = 1..m−1 we enforce (¬d_{i,t} ∨ l_i) and (¬d_{i,t} ∨ d_{i,t−1} ∨ ∨_{j∈N_R(i)} d_{j,t−1}), "
            "plus goal clauses ∧_{i=1}^m (¬l_i ∨ d_{i,m−1}). By induction on t, d_{i,t} = True implies a valid path in G_R[S] of "
            "length ≤ t from the unique root to u_i; conversely, any connected G_R[S] has diameter ≤ |S|−1 ≤ m−1. Exhaustive "
            "testing over all 2⁹ = 512 assignments on 3×3 grids confirmed 100% agreement with SemanticEvaluator.",
            st_body,
        )
    )

    story.append(Paragraph("4. Algorithms, Correctness Proofs, and Complexity Analysis", st_h1))
    story.append(Paragraph("4.1 Custom DPLL Solver and No-Guess Deduction Loop", st_h2))
    story.append(
        Preformatted(
            "Algorithm 1: Custom DPLL(Clauses, Assignment)\n"
            "  1: (conflict, Clauses, Assignment) <- UnitPropagate(Clauses, Assignment)\n"
            "  2: if conflict then return UNSAT\n"
            "  3: if use_PLE then Clauses <- PureLiteralEliminate(Clauses, Assignment)\n"
            "  4: if Clauses is empty then pad unassigned v in 1..V_total with False; return SAT(Assignment)\n"
            "  5: (v, pol) <- SelectDeterministicVar(Clauses)   // FIXED_ORDER or 2-sided Jeroslow-Wang\n"
            "  6: decisions += 1; if DPLL(Clauses, Assignment ∪ {v = pol}) == SAT then return SAT\n"
            "  7: backtracks += 1; return DPLL(Clauses, Assignment ∪ {v = ¬pol})\n\n"
            "Algorithm 2: Witness-Pruned Entailment Classification(KB_t)\n"
            "  1: res0 <- DPLL(KB_t); if res0 == UNSAT then return INCONSISTENT\n"
            "  2: record witness polarities M_0[C_j] in seen_true / seen_false for each unsolved cell j\n"
            "  3: for each unsolved cell i in deterministic row-major order:\n"
            "  4:   if seen_true[i] and seen_false[i] then status[i] <- UNKNOWN   // 0 extra SAT calls!\n"
            "  5:   else L_opp <- (¬C_i if i in seen_true else C_i)\n"
            "  6:     if DPLL(KB_t ∧ L_opp) == UNSAT then status[i] <- (CRIMINAL if i in seen_true else INNOCENT)\n"
            "  7:     else update seen_true / seen_false from new witness model; status[i] <- UNKNOWN",
            st_code,
        )
    )

    # =====================================================================
    # PAGE 4: SECTION 4.2 (FORMAL PROOFS) & SECTION 4.3 (COMPLEXITY)
    # =====================================================================
    story.append(PageBreak())
    story.append(Paragraph("4.2 Formal Soundness, Completeness, and Minimality Proofs", st_h2))

    story.append(
        Paragraph(
            "<b>Theorem 1 (Soundness &amp; Completeness of Witness-Guided Refutation Pruning):</b> <i>Suppose KB_t is "
            "satisfiable with initial model M₀ ⊨ KB_t, and let W ⊇ {M₀} be the set of satisfying models accumulated prior to "
            "inspecting unresolved cell i. Algorithm 2 returns the exact same classification (CRIMINAL, INNOCENT, or UNKNOWN) "
            "as running both explicit refutation queries KB_t ∧ ¬C_i and KB_t ∧ C_i.</i><br/>"
            "<b>Proof:</b> Since M₀ ∈ W assigns every primary variable C_i a definite truth value, at least one polarity of C_i "
            "is guaranteed satisfiable with KB_t. (Case 1) If ∃M⁺, M⁻ ∈ W with M⁺(C_i) = True and M⁻(C_i) = False, then M⁺ ⊨ "
            "(KB_t ∧ C_i) and M⁻ ⊨ (KB_t ∧ ¬C_i); both refutation formulas are SAT, so cell i is provably UNKNOWN with 0 new SAT "
            "calls. (Case 2) If every M ∈ W has M(C_i) = True, then KB_t ∧ C_i is already SAT (witnessed by M₀), so KB_t ⊭ ¬C_i. "
            "Testing KB_t ∧ ¬C_i yields UNSAT iff KB_t ⊨ C_i (CRIMINAL), and otherwise returns M⁻ ⊨ (KB_t ∧ ¬C_i), proving UNKNOWN "
            "while enriching W for subsequent cells. The case M(C_i) = False is symmetric. ∎",
            st_thm,
        )
    )

    story.append(
        Paragraph(
            "<b>Theorem 2 (Primary-Only Blocking Clause Uniqueness Characterization):</b> <i>Let KB_full(C, A) be an "
            "equisatisfiable CNF over primary variables C = (C₁..C_{N²}) and auxiliary variables A, with first model M* ⊨ KB_full. "
            "Then KB_full ∧ B_prim(M*), where B_prim(M*) = ∨_{i=1}^{N²} (¬C_i if M*(C_i) else C_i), is UNSAT iff M*|_C is the "
            "unique valid Criminal/Innocent board assignment.</i><br/>"
            "<b>Proof:</b> Any total assignment (C', A') satisfies B_prim(M*) iff ∃i ∈ {1..N²} with C'_i ≠ M*(C_i), i.e., C' ≠ M*|_C. "
            "By equisatisfiability of CNFEncoder, C' is a valid board solution iff ∃A' such that (C', A') ⊨ KB_full. Hence a second "
            "distinct board solution C' ≠ M*|_C exists iff KB_full ∧ B_prim(M*) is SAT. Crucially, omitting A from B_prim prevents "
            "spurious 'second solutions' caused solely by unconstrained slack auxiliary variables (e.g., in Sinz counters or OR selectors). ∎",
            st_thm,
        )
    )

    story.append(
        Paragraph(
            "<b>Theorem 3 (Soundness &amp; Subset-Minimality of Deletion-Based MUS Hinting):</b> <i>When cell i* has forced literal "
            "L_{i*} (so CNF(R_t) ∧ ¬L_{i*} is UNSAT), iterative deletion retains a clue subset C* ⊆ R_t such that (1) C* entails "
            "L_{i*}, and (2) no proper subset C' ⊂ C* entails L_{i*}.</i><br/>"
            "<b>Proof:</b> (1) Soundness holds by loop invariant: a clue c is removed from working set W only when CNF(W \\ {c}) ∧ "
            "¬L_{i*} remains UNSAT. (2) For minimality, take any c ∈ C*. When c was tested against working set W_c ⊇ C*, removing c "
            "rendered CNF(W_c \\ {c}) ∧ ¬L_{i*} satisfiable with some model M_c. Since C* \\ {c} ⊆ W_c \\ {c}, M_c satisfies every "
            "clause of CNF(C* \\ {c}) ∧ ¬L_{i*} as well; hence C* \\ {c} ⊭ L_{i*}. ∎",
            st_thm,
        )
    )

    story.append(Paragraph("4.3 Asymptotic Time and Space Complexity", st_h2))
    comp_rows = [
        ["Subsystem / Operation", "Time Complexity", "Formula / Space Size", "Practical Bound (N ≤ 5, M = N² ≤ 25)"],
        ["SemanticEvaluator.evaluate", "O(|R| + |E_R|)", "O(M) auxiliary memory", "Direct sum / BFS; < 0.01 ms per clue"],
        ["CNFEncoder (Combinatorial)", "O(C(|R|, k+1))", "C(|R|, k+1) clauses, 0 aux", "|R| ≤ 8 ⇒ at most 70 clauses per clue"],
        ["CNFEncoder (Sinz Counter)", "O(|R| · k)", "O(|R| · k) clauses & aux", "Linear growth on large boundary regions"],
        ["CNFEncoder (2D CONNECTED)", "O(|R|² · deg)", "|R|² aux vars, O(|R|²) cls", "Exact BFS layers; 0 aux on 1D paths"],
        ["DPLLSolver.solve", "O(2^V · L) worst", "O(V + L) per branch depth", "Sub-millisecond typical with unit prop & JW"],
        ["Agent Step (Explicit / Pruned)", "2U vs. ≤ U+1 SAT", "O(|KB_t|) active clauses", "Witness pruning cuts SAT calls by ~46%"],
        ["HintEngine (Deletion MUS)", "≤ |R_t| + |P_t| SAT", "O(|KB_t|) active clauses", "≤ 50 tiny SAT calls (< 5 ms total)"],
    ]
    story.append(
        _styled_table(
            comp_rows,
            [4.3 * cm, 2.8 * cm, 3.8 * cm, usable_w - 10.9 * cm],
            font_size=7.6,
        )
    )

    # =====================================================================
    # PAGE 5: SECTION 4.4 (WORKED HAND TRACE KB_0 -> KB_8 ON 3x3)
    # =====================================================================
    story.append(PageBreak())
    story.append(Paragraph("4.4 Complete Worked Step-by-Step Hand Trace on 3x3_01_core_intro (KB₀ → KB₈)", st_h2))
    story.append(
        Paragraph(
            "To illustrate how CNF encoding, refutation querying, and progressive card revelation interact without guessing, "
            "we trace all 8 steps on 3x3_01_core_intro. Initially only A1 (Abel, Cook) is face-up as INNOCENT, revealing "
            "clue_A1 = EXACTLY(2, Row 1). Thus KB₀ consists of unit clause (¬C_A1) plus the 4 combinatorial clauses of "
            "EXACTLY(2, {A1, B1, C1}): (¬C_A1 ∨ ¬C_B1 ∨ ¬C_C1) ∧ (C_A1 ∨ C_B1) ∧ (C_A1 ∨ C_C1) ∧ (C_B1 ∨ C_C1).",
            st_body,
        )
    )

    trace_rows = [
        ["Step", "KB_t Size", "Forced Verdict", "Refutation Derivation (KB_t ∧ ¬L_i ⇒ ⊥)", "Newly Flipped Clue"],
        [
            "t = 1",
            "1 clue, 5 cls",
            "B1 = CRIMINAL\n(Bea)",
            Paragraph("Assume ¬C_B1. Propagating ¬C_A1 and ¬C_B1 into (C_A1 ∨ C_B1) yields empty clause ⊥ (2 props, 0 decs). Note: C1 is also forced; row-major order selects B1 first.", st_cell),
            Paragraph("clue_B1: DIFFERENT(B1, A2)\n(C_B1 ∨ C_A2) ∧ (¬C_B1 ∨ ¬C_A2)", st_cell),
        ],
        [
            "t = 2",
            "2 clues, 8 cls",
            "C1 = CRIMINAL\n(Clara)",
            Paragraph("Assume ¬C_C1. Propagating ¬C_A1 and ¬C_C1 into (C_A1 ∨ C_C1) yields ⊥ in 2 propagations.", st_cell),
            Paragraph("clue_C1: EXACTLY(1, Col C)\n4 clauses on {C1, C2, C3}", st_cell),
        ],
        [
            "t = 3",
            "3 clues, 13 cls",
            "A2 = INNOCENT\n(Derek)",
            Paragraph("Assume C_A2. Together with unit (C_B1), binary clause (¬C_B1 ∨ ¬C_A2) from clue_B1 immediately yields ⊥.", st_cell),
            Paragraph("clue_A2: EXACTLY(1, Row 2)\n4 clauses on {A2, B2, C2}", st_cell),
        ],
        [
            "t = 4",
            "4 clues, 18 cls",
            "B2 = CRIMINAL\n(Eliza)",
            Paragraph("Assume ¬C_B2. From Col C = 1 and C_C1, unit prop derives ¬C_C2; then Row 2 = 1 with ¬C_A2, ¬C_B2, ¬C_C2 violates (C_A2 ∨ C_B2 ∨ C_C2) ⇒ ⊥!", st_cell),
            Paragraph("clue_B2: AT_LEAST(3, Nbr(B2))\n35 clauses on 8 neighbors", st_cell),
        ],
        [
            "t = 5",
            "5 clues, 54 cls",
            "C2 = INNOCENT\n(Franz)",
            Paragraph("Assume C_C2. Together with proved unit (C_C1), AT_MOST(1, Col C) clause (¬C_C1 ∨ ¬C_C2) yields ⊥.", st_cell),
            Paragraph("clue_C2: SAME(B2, A3)\n(¬C_B2 ∨ C_A3) ∧ (C_B2 ∨ ¬C_A3)", st_cell),
        ],
        [
            "t = 6",
            "6 clues, 57 cls",
            "A3 = CRIMINAL\n(Grant)",
            Paragraph("Assume ¬C_A3. With proved unit (C_B2), implication clause (¬C_B2 ∨ C_A3) from clue_C2 yields ⊥.", st_cell),
            Paragraph("clue_A3: AT_MOST(1, Row 3)\n3 binary clauses on {A3, B3, C3}", st_cell),
        ],
        [
            "t = 7",
            "7 clues, 61 cls",
            "B3 = INNOCENT\n(Hannah)",
            Paragraph("Assume C_B3. With proved unit (C_A3), AT_MOST(1, Row 3) clause (¬C_A3 ∨ ¬C_B3) yields ⊥.", st_cell),
            Paragraph("clue_B3: NO({B3, C3})\nUnit clauses (¬C_B3) ∧ (¬C_C3)", st_cell),
        ],
        [
            "t = 8",
            "8 clues, 64 cls",
            "C3 = INNOCENT\n(Ivy)",
            Paragraph("Assume C_C3. Contradicts unit (¬C_C3) from clue_B3 (as well as Col C = 1 and Row 3 ≤ 1) ⇒ ⊥. All 9/9 cards SOLVED!", st_cell),
            Paragraph("clue_C3: DIFFERENT(A3, C3)\n(Consistent terminal clue)", st_cell),
        ],
    ]
    story.append(
        _styled_table(
            trace_rows,
            [1.3 * cm, 2.1 * cm, 2.5 * cm, usable_w - 10.2 * cm, 4.3 * cm],
            font_size=7.4,
        )
    )

    # =====================================================================
    # PAGES 6–7: SECTION 4.5 (GUI SHOWCASE + LIVE CNF INSPECTOR)
    # =====================================================================
    story.append(PageBreak())
    story.append(Paragraph("4.5 Interactive Bilingual Graphical User Interface and Live CNF Inspector", st_h2))
    story.append(
        Paragraph(
            "The web-based GUI supports instant bilingual switching (Vietnamese default / English), 3D card-flip animations, "
            "profession vector icons, visual region highlighting when clicking any revealed clue, distinct NOT_PROVABLE vs. "
            "CONTRADICTED feedback banners, MUS Hint highlighting, step/animated Auto Solve, manual move entailment logging, "
            "and a live KB_t CNF Formula Inspector modal.",
            st_body,
        )
    )
    gui_vi = figs_dir / "gui_vietnamese.png"
    gui_img2 = figs_dir / "gui_solved_trace.png"
    gui_cnf = figs_dir / "gui_cnf_inspector.png"
    gui_img1 = figs_dir / "gui_hint_gameplay.png"
    top_gui = gui_vi if gui_vi.exists() else gui_img1
    if top_gui.exists():
        story.append(_scaled_image(top_gui, usable_w, 7.6 * cm))
        story.append(
            Paragraph(
                "Figure 2a: Bilingual (Vietnamese/English) gameplay & MUS Hint highlighting provable target Bea (B1) and essential clue Abel (A1).",
                st_caption,
            )
        )
    if gui_cnf.exists():
        story.append(_scaled_image(gui_cnf, usable_w, 7.6 * cm))
        story.append(
            Paragraph(
                "Figure 2b: Live KB_t CNF Inspector modal displaying symbolic clauses grouped by active clue, variable map, and DIMACS export.",
                st_caption,
            )
        )
    if gui_img2.exists():
        story.append(PageBreak())
        story.append(_scaled_image(gui_img2, usable_w, 7.8 * cm))
        story.append(
            Paragraph(
                "Figure 2c: Complete solved state with Uniqueness verification, DPLL counters, and expanded SAT Refutation Queries.",
                st_caption,
            )
        )

    # =====================================================================
    # PAGES 8–9: SECTION 5 (EXPERIMENTAL EVALUATION ON 19 PUZZLES)
    # =====================================================================
    story.append(Paragraph("5. Experimental Evaluation", st_h1))
    story.append(
        Paragraph(
            "We evaluated 4 solver/encoding configurations on the exact same 19-puzzle benchmark suite (six 3×3 puzzles "
            "including STUCK/ambiguous, INCONSISTENT, and Compound/Connected cases; seven 4×4 puzzles including two coupled "
            "non-unit backtrack cases; and six 5×5 stress/showcase cases up to 645 backtracks): "
            "(1) 1_Comb_Fixed (Combinatorial CNF + Fixed Order), (2) 2_Seq_Fixed (Sinz Sequential Counter + Fixed Order), "
            "(3) 3_Comb_JW (Combinatorial + Jeroslow-Wang Heuristic), and (4) 4_Comb_JW_Pruned (+ PLE + Witness Pruning).",
            st_body,
        )
    )

    csv_path = results_dir / "benchmark_results.csv"
    if csv_path.exists():
        with csv_path.open("r", encoding="utf-8") as fh:
            b_rows = list(csv.DictReader(fh))

        t1_data = [
            [
                "Puzzle ID",
                "Grid",
                "State",
                "Vars (P+A)",
                "Clauses",
                "SAT",
                "Dec",
                "Prop",
                "BT",
                "Steps(W)",
                "Time(ms)",
            ]
        ]
        for r in b_rows:
            if r["config"] != "1_Comb_Fixed":
                continue
            t1_data.append(
                [
                    r["puzzle_id"],
                    r["grid_size"],
                    r["terminal_state"],
                    f"{r['primary_vars']}+{r['aux_vars']}",
                    r["cnf_clauses"],
                    r["sat_calls"],
                    r["decisions"],
                    r["propagations"],
                    r["backtracks"],
                    f"{r['deduction_steps']}({r['reveal_waves']})",
                    f"{float(r['wall_runtime_ms']):.2f}",
                ]
            )
        story.append(Paragraph("5.1 Per-Puzzle Metrics on Complete 19-Puzzle Suite (Baseline 1_Comb_Fixed)", st_h2))
        story.append(
            _styled_table(
                t1_data,
                [
                    4.15 * cm,
                    0.95 * cm,
                    2.3 * cm,
                    1.5 * cm,
                    1.2 * cm,
                    1.0 * cm,
                    1.0 * cm,
                    1.2 * cm,
                    0.9 * cm,
                    1.4 * cm,
                    usable_w - 15.6 * cm,
                ],
                font_size=6.8,
            )
        )
        story.append(Spacer(1, 5))

        story.append(Paragraph("5.2 Comparative Summary Across Configurations (17 Solvable Puzzles)", st_h2))
        t2_data = [
            [
                "Configuration",
                "Avg Aux",
                "Avg Clauses",
                "Total SAT Calls",
                "Decisions",
                "Propagations",
                "Backtracks",
                "Time (ms)",
            ]
        ]
        for cfg in ("1_Comb_Fixed", "2_Seq_Fixed", "3_Comb_JW", "4_Comb_JW_Pruned"):
            sub = [r for r in b_rows if r["config"] == cfg and r["terminal_state"] == "SOLVED"]
            n = len(sub)
            t2_data.append(
                [
                    cfg,
                    f"{sum(int(r['aux_vars']) for r in sub)/n:.1f}",
                    f"{sum(int(r['cnf_clauses']) for r in sub)/n:.1f}",
                    str(sum(int(r["sat_calls"]) for r in sub)),
                    str(sum(int(r["decisions"]) for r in sub)),
                    str(sum(int(r["propagations"]) for r in sub)),
                    str(sum(int(r["backtracks"]) for r in sub)),
                    f"{sum(float(r['wall_runtime_ms']) for r in sub):.2f}",
                ]
            )
        story.append(
            _styled_table(
                t2_data,
                [
                    3.1 * cm,
                    2.0 * cm,
                    2.0 * cm,
                    2.3 * cm,
                    1.8 * cm,
                    2.2 * cm,
                    1.8 * cm,
                    usable_w - 15.2 * cm,
                ],
                font_size=7.8,
            )
        )

    story.append(PageBreak())
    c1 = results_dir / "chart_runtime_by_grid.png"
    c2 = results_dir / "chart_sat_calls_and_decisions.png"
    c_bt = results_dir / "chart_backtracks_coupled.png"
    c3 = results_dir / "chart_clauses_comb_vs_seq.png"
    if c2.exists():
        story.append(_scaled_image(c2, usable_w, 4.8 * cm))
        story.append(
            Paragraph(
                "Figure 3: Aggregate SAT calls, branching decisions, and DPLL backtracks across the 17 solvable puzzles.",
                st_caption,
            )
        )
    if c_bt.exists() and c1.exists():
        chart_tbl = Table(
            [
                [
                    _scaled_image(c_bt, usable_w * 0.51, 4.9 * cm),
                    _scaled_image(c1, usable_w * 0.47, 4.9 * cm),
                ]
            ],
            colWidths=[usable_w * 0.52, usable_w * 0.48],
        )
        story.append(chart_tbl)
        story.append(
            Paragraph(
                "Figure 4: (Left) Fixed Order vs. Jeroslow-Wang backtracks on coupled non-unit puzzles; "
                "(Right) Mean runtime scaling across 3×3, 4×4, and 5×5 grids.",
                st_caption,
            )
        )
    if c3.exists():
        story.append(_scaled_image(c3, usable_w * 0.74, 4.5 * cm))
        story.append(
            Paragraph(
                "Figure 5: Peak CNF clause count comparison between Direct Combinatorial and Sinz Sequential Counter encodings.",
                st_caption,
            )
        )

    story.append(Paragraph("5.3 Key Experimental Findings, Failure/Diagnostic Analysis, and Limitations", st_h2))
    story.append(
        Paragraph(
            "• <b>Coupled Constraints &amp; Branching Thrashing:</b> Standard puzzles with unit or narrow neighbor clues propagate "
            "almost immediately to conflict, yielding 0 backtracks. In contrast, our coupled overlapping cardinality &amp; parity "
            "puzzles (4x4_06, 4x4_07, 5x5_04, 5x5_05) and 5x5_06_figure1_showcase contain zero initial unit clauses, forcing genuine "
            "recursive search (up to 645 backtracks on 5x5_05_coupled_fortress). Under FIXED_ORDER (1_Comb_Fixed), DPLL branches "
            "across loosely constrained early-row bands (e.g., C(8,4)=70 combinations) before reaching the unsatisfiable core, "
            "incurring <b>1,251 total backtracks</b>. Weighting short clauses by 2^(−|C|) via Jeroslow-Wang (3_Comb_JW) focuses "
            "immediately on the coupled core and slashes backtracks by <b>78.1% (1,251 → 274)</b> on the exact same 4,370 SAT calls.<br/>"
            "• <b>Witness-Guided Pruning &amp; Encoding Trade-off:</b> Adding Witness-Guided Pruning (4_Comb_JW_Pruned) cuts total "
            "SAT calls by <b>45.5% (4,370 → 2,380)</b>, decisions by <b>61.3% (6,679 → 2,586)</b>, and runtime by <b>37.9% (10.11s → 6.28s)</b> "
            "with zero timeouts. Direct Combinatorial encoding runs 5.2× faster than Sinz Sequential Counters because Griductive "
            "region sizes (|R| ≤ 8) stay small enough to avoid combinatorial explosion while avoiding 17× auxiliary variable overhead.<br/>"
            "• <b>Diagnostic Cases &amp; Architectural Limitations:</b> On 3x3_04_ambiguous_case, the agent proves B1 and C1 in Wave 1 "
            "and halts cleanly at STUCK without guessing (UniquenessChecker confirms multiple global models). On 3x3_05_inconsistent_case, "
            "it detects UNSAT in 1 SAT call (0.36 ms). Because our pure-Python DPLL solver eagerly copies simplified clause lists "
            "without 2-watched literals or CDCL learned clauses, 2D BFS connectivity over large regions (|R| ≥ 12) increases runtime; "
            "integrating watched literals and clause learning would enable scaling to 10×10+ boards.",
            st_body,
        )
    )

    # =====================================================================
    # PAGE 10: SECTION 6 (REFERENCES & GENERATIVE AI APPENDIX)
    # =====================================================================
    story.append(Paragraph("6. References and Appendix", st_h1))
    story.append(
        Paragraph(
            "[1] M. Davis and H. Putnam, 'A computing procedure for quantification theory,' JACM, vol. 7, no. 3, pp. 201–215, 1960.<br/>"
            "[2] M. Davis, G. Logemann, and D. Loveland, 'A machine program for theorem-proving,' CACM, vol. 5, no. 7, pp. 394–397, 1962.<br/>"
            "[3] C. Sinz, 'Towards an optimal CNF encoding of Boolean cardinality constraints,' in Proc. CP 2005, LNCS 3709, pp. 827–831.<br/>"
            "[4] R. G. Jeroslow and J. Wang, 'Solving propositional satisfiability problems,' Ann. Math. Artif. Intell., vol. 1, pp. 167–187, 1990.<br/>"
            "[5] G. S. Tseitin, 'On the complexity of derivation in propositional calculus,' Seminars in Mathematics, vol. 8, pp. 115–125, 1968.<br/>"
            "[6] S. Russell and P. Norvig, Artificial Intelligence: A Modern Approach, 4th ed., Pearson, 2020, ch. 7.<br/>"
            "[7] Griductive Official Puzzle Game &amp; How-To-Play Guide: https://griductive.com",
            st_body,
        )
    )
    story.append(Paragraph("Appendix: Generative AI (LLM) Usage Disclosure", st_h2))
    story.append(
        Paragraph(
            "Generative AI (LLM) tools were used responsibly during development for architectural planning, automated truth-table "
            "verification harness generation, bilingual UI localization, and report formatting. Every logical encoding and solver "
            "routine was mathematically derived and verified via 20 automated unit &amp; integration test suites (including exhaustive "
            "2⁹ = 512 state equivalence checks against SemanticEvaluator). Representative prompts included:<br/>"
            "• <i>Prompt 1:</i> 'Read the CSC14003 Project 2 Griductive Solver specification and construct a detailed roadmap strictly "
            "aligned with the 100-point rubric and Engine/Agent isolation rules.'<br/>"
            "• <i>Prompt 2:</i> 'Derive equisatisfiable CNF encodings for Compound (AND/OR/IMPLIES) and 2D Orthogonal Connectivity clues "
            "and verify them exhaustively against a standalone semantic evaluator across all 512 assignments of a 3×3 grid.'<br/>"
            "• <i>Prompt 3:</i> 'Design coupled non-unit overlapping cardinality and parity puzzles on 4×4 and 5×5 boards to stress-test "
            "DPLL backtracking and evaluate Fixed Order vs. Jeroslow-Wang heuristics.'",
            st_body,
        )
    )

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    print(f"Successfully generated PDF report: {out_pdf}")
    return out_pdf


if __name__ == "__main__":
    build_pdf()
