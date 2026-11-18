# CSAI_Group9_Lab02 — No-Guess Griductive Solver (CSC14003)

**CSC14003: Introduction to Artificial Intelligence — Project 2 (FIT, VNU-HCM)**

Một triển khai hoàn chỉnh cho bài toán **No-Guess Griductive** bằng **Logic Mệnh đề (Propositional Logic)**, biên dịch tự động sang **CNF** và giải bằng bộ **DPLL SAT Solver** viết thuần bằng Python từ đầu (không dùng thư viện SAT bên ngoài).

---

## Cấu trúc thư mục

* [`Source/`](Source/) — Mã nguồn hoàn chỉnh (Domain Models, Regions, Automatic CNF Encoder cho 6 Core + 5 Extensions, Direct Semantic Evaluator, Custom Pure-Python DPLL Solver, `GameEngine` cách ly dữ liệu ẩn, `DeductiveLogicAgent`, `UniquenessChecker`, `HintEngine` theo MUS, Giao diện Web song ngữ Việt/Anh + Inspect $KB_t$ CNF, 19 màn chơi & suite benchmark + 20 unit/integration tests). Xem chi tiết tại [`Source/README.md`](Source/README.md).
* [`Report.pdf`](Report.pdf) — Báo cáo học thuật chính thức (11 trang: mô hình hóa, sơ đồ kiến trúc 3 miền, dẫn xuất CNF, giải tay $KB_0 \to KB_8$, chứng minh Soundness/Completeness/Minimality, độ phức tạp và kết quả thực nghiệm trên 19 màn chơi).
* [`Report/`](Report/) — Mã nguồn LaTeX ([`Report/main.tex`](Report/main.tex)), script sinh PDF ([`Report/build_report_pdf.py`](Report/build_report_pdf.py)), sơ đồ kiến trúc, kịch bản demo & tài liệu bảo vệ.
* [`package_submission.py`](package_submission.py) — Script đóng gói tự động `Report.pdf` và `Source/` thành file `.zip` đúng quy cách nộp bài.

---

## Chạy nhanh (Quick Start)

Yêu cầu **Python 3.10+**:

```bash
cd Source
pip install -r requirements.txt

# 1. Mở giao diện Web chơi game (mặc định Tiếng Việt, có nút đổi Tiếng Anh)
python main.py

# 2. Chạy toàn bộ 20 bài kiểm thử (gồm kiểm chứng vét cạn 2^9 = 512 trạng thái)
python -m pytest tests -v

# 3. Chạy thực nghiệm 19 màn x 4 cấu hình và sinh biểu đồ
python main.py --benchmark
```
