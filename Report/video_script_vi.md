# Kịch Bản Quay Video Demo Chi Tiết (5–8 Phút — Trọn 10 Điểm Mục 4.7)

> **Quy định bắt buộc của đề bài (Mục 4.7):**
> * Thời lượng: **5 đến 10 phút** (lý tưởng nhất là ~6–7 phút).
> * Phải có **thuyết minh giọng nói (tiếng Việt hoặc tiếng Anh)** hoặc **phụ đề**.
> * Bắt buộc tải lên **Google Drive**, bật quyền **"Bất kỳ ai có đường liên kết đều có thể xem" (Anyone with the link can view)** và mở thử bằng cửa sổ ẩn danh (`Ctrl + Shift + N`) để kiểm tra. **TUYỆT ĐỐI KHÔNG nộp link YouTube.**

---

## Chuẩn Bị Trước Khi Bấm Quay (30 giây)
1. Đảm bảo server đang chạy: mở terminal tại `d:\Proj_2_AI\Source`, chạy `python main.py` (hoặc mở tab http://127.0.0.1:5050 đang chạy sẵn).
2. Bấm `Restart` trên giao diện để bàn cờ về màn mặc định **`3x3 Stage 1 — Tutorial Watch [Easy]`**.
3. Mở công cụ quay màn hình có thu micro (như **OBS Studio** hoặc `Win + G` Xbox Game Bar / Snipping Tool Video).

---

## Phần 1: Giới Thiệu Kiến Trúc & Giao Diện GUI (0:00 – 1:45) — *5 điểm Graphical Interface*

* **Thao tác trên màn hình:**
  * Chiếu nhanh thư mục `Source/` trong VS Code (chỉ qua `models/`, `logic/`, `solver/`, `agent/`, `engine/`, `gui/`, `main.py`), sau đó chuyển sang cửa sổ trình duyệt tại `http://127.0.0.1:5050`.
* **Lời thoại gợi ý:**
  > *"Xin chào thầy/cô. Hôm nay nhóm xin trình bày đồ án Project 2 môn Nhập môn Trí tuệ Nhân tạo: **No-Guess Griductive Solver** sử dụng logic mệnh đề, mã hóa CNF tự động và bộ giải DPLL SAT tự cài đặt.*
  > *Về kiến trúc, hệ thống tách biệt hoàn toàn hai vai trò: `GameEngine` giữ đáp án ẩn và các clue chưa lật trong thuộc tính riêng tư, còn `DeductiveLogicAgent` chỉ nhận đối tượng `PublicGameState` bất biến gồm các thẻ đã mở.*
  > *Trên giao diện đồ họa, bên trái là bàn cờ N×N hiển thị tọa độ cột A, B, C, tọa độ hàng 1, 2, 3, tên nhân vật theo thứ tự bảng chữ cái, nghề nghiệp, các thẻ đã lật ngửa (màu xanh lá cho Innocent, màu đỏ cho Criminal) và các thẻ đang úp. Bên phải là bảng cấu hình CNF & DPLL, bộ đếm biến sơ cấp, biến phụ, số mệnh đề CNF, số lần gọi SAT và nhật ký suy diễn Deduction Trace."*

---

## Phần 2: Chơi Thủ Công, Highlight Vùng Clue & Chống Đoán Mò (1:45 – 4:00) — *Phần đầu của 5 điểm Feature Presentation*

* **Thao tác 1 (Highlight vùng Clue):** Click vào thẻ đã mở **`A1 (Abel)`**.
  * **Lời thoại:** *"Khi click vào thẻ đã mở A1 với nội dung 'Exactly 2 people in row 1 are criminals', giao diện tự động highlight trực quan cả 3 ô thuộc hàng 1 là A1, B1 và C1."*
* **Thao tác 2 (Chứng minh chặn đoán mò `NOT_PROVABLE`):** Click nút **`Criminal`** trên ô **`B2 (Eliza)`**.
  * **Lời thoại:** *"Quy tắc cốt lõi của Griductive là không được đoán mò. Ở bước đầu tiên, dù trong đáp án ẩn Eliza (B2) thực sự là Criminal, khi người chơi bấm chọn Criminal cho B2, hệ thống kiểm tra trên KB hiện tại thấy cả hai nhánh đều thỏa được nên lập tức từ chối với mã **NOT_PROVABLE** và giữ nguyên thẻ úp."*
* **Thao tác 3 (Chứng minh phát hiện mâu thuẫn `CONTRADICTED`):** Click nút **`Innocent`** trên ô **`B1 (Bea)`**.
  * **Lời thoại:** *"Ngược lại, vì A1 là Innocent mà hàng 1 có đúng 2 tội phạm nên B1 và C1 bắt buộc phải là Criminal. Nếu người chơi cố tình chọn Innocent cho B1, hệ thống báo đỏ **CONTRADICTED** vì mâu thuẫn trực tiếp với hệ quả logic của KB hiện tại."*
* **Thao tác 4 (Nút `Hint` không chạm dữ liệu ẩn):** Bấm nút **`Hint`** trên thanh công cụ.
  * **Lời thoại:** *"Khi bấm nút **Hint**, thuật toán sử dụng phép rút gọn tập không thỏa tối thiểu (MUS) trên các clue công khai để vừa nhấp nháy ô có thể chứng minh tiếp theo là **Bea (B1)**, vừa chỉ ra chính xác clue gốc dẫn tới kết luận là **Abel (A1)** mà hoàn toàn không đọc đáp án ẩn."*
* **Thao tác 5 (Chốt phán quyết hợp lệ `ACCEPTED` & Soi trực tiếp mệnh đề CNF):** Click nút **`Criminal`** trên ô **`B1 (Bea)`**, sau đó bấm nút màu cam **`Inspect KB_t CNF`** trên thanh công cụ (chuyển qua lại 3 tab *Symbolic Clauses*, *Variable Mapping*, *Standard DIMACS .cnf* rồi bấm `Close`).
  * **Lời thoại:** *"Khi chọn đúng kết luận đã được chứng minh là Criminal cho B1, thẻ lật hiệu ứng 3D mở ra clue mới, đồng thời nước đi thủ công cũng được ghi kèm truy vấn phản chứng vào lịch sử bên phải. Bấm nút **Inspect KB_t CNF**, ta quan sát trực tiếp toàn bộ các mệnh đề CNF ký hiệu đang được sinh tự động từ từng thẻ đã mở, bảng tách biệt biến sơ cấp C_i với biến phụ, và định dạng chuẩn DIMACS."*

---

## Phần 3: Chạy Bộ Giải Tự Động (Step / Auto Solve), Extensions & Stress Test 5×5 (4:00 – 6:45) — *Phần sau của 5 điểm Feature Presentation*

* **Thao tác 1 (`Step` & xem `Deduction Trace`):** Bấm nút **`Step`** 2 lần, sau đó mở rộng dòng `Inspect SAT Refutation Queries` ở bảng **Deduction Trace** bên phải. Bấm thêm **`Check Uniqueness`**.
  * **Lời thoại:** *"Khi bấm **Step**, Logic Agent tự động kiểm chứng phản chứng `KB_t ∧ ¬C_i` và `KB_t ∧ C_i` theo thứ tự tất định row-major. Mở bảng truy vấn SAT ở từng bước, ta thấy rõ truy vấn nào trả về UNSAT để ép buộc trạng thái nhân vật, cùng số phép lan truyền đơn vị (propagations) và phân nhánh (decisions). Nút **Check Uniqueness** sử dụng mệnh đề chặn trên các biến sơ cấp xác nhận toàn bộ bộ clue có duy nhất 1 nghiệm hợp lệ."*
* **Thao tác 2 (Màn 4×4 có Extensions & đổi chế độ mã hóa CNF):** Chọn màn **`4x4 Stage 3 — Crossfire [Medium]`** ở ô `Stage`. Thử đổi `Cardinality CNF` từ `Direct Combinatorial (0 Aux)` sang `Sinz Sequential Counter (Aux)` (chỉ vào ô `Auxiliary Vars` tăng lên), bật `Witness-Guided Pruning`, chọn tốc độ `Fast (0.22s)` và bấm **`Auto Solve`**.
  * **Lời thoại:** *"Tiếp theo ở màn 4×4 có tích hợp cả 3 phần mở rộng (giao các vùng, so sánh số tội phạm hai vùng và ràng buộc chẵn/lẻ Parity), khi chuyển sang bộ đếm tuần tự Sinz, hệ thống tách biệt rõ số biến sơ cấp 16 biến và các biến phụ. Bấm **Auto Solve**, tác tử giải mượt toàn bộ 16 ô không cần đoán."*
* **Thao tác 3 (Màn Stress Case 5×5 — 24 bước liên tiếp):** Chọn màn **`5x5 Stress 3 — Lone Informant (24 Steps) [Stress]`**, chọn tốc độ `Fast (0.22s)` (hoặc `Instant`) và bấm **`Auto Solve`**.
  * **Lời thoại:** *"Trên ca kiểm thử tải nặng 5×5 gồm 25 nhân vật xuất phát chỉ từ 1 thẻ mở duy nhất, bộ giải DPLL kết hợp Jeroslow-Wang và Witness Pruning hoàn thành toàn bộ 24 bước suy diễn trong khoảng 0.3 giây."*
* **Thao tác 4 (Hai ca biên `STUCK` & `INCONSISTENT`):** Chọn nhanh **`3x3 Diagnostic — Ambiguous State`** bấm `Auto Solve` (dừng ở bước 2 báo `STUCK`), rồi chọn **`3x3 Diagnostic — Contradictory Clues`** bấm `Step` (báo `INCONSISTENT`).
  * **Lời thoại:** *"Cuối cùng, trên hai ca chẩn đoán biên: khi dữ kiện mơ hồ đa nghiệm, tác tử giải hết các ô chắc chắn rồi dừng ở trạng thái **STUCK** chứ tuyệt đối không đoán; và khi các clue mâu thuẫn nhau, tác tử phát hiện ngay trạng thái **INCONSISTENT (UNSAT)**. Xin cảm ơn thầy/cô đã theo dõi!"*
