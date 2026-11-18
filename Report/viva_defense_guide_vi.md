# Cẩm Nang Ôn Tập Vấn Đáp (Oral Interview Guide — Mục 6 Đề Bài)

Đề bài lưu ý giảng viên hướng dẫn thực hành có thể gọi vấn đáp ngẫu nhiên để kiểm tra mức độ hiểu bài của các thành viên. Tài liệu này tóm tắt luồng code cốt lõi và giải đáp **10 câu hỏi vấn đáp kinh điển nhất** của đồ án này.

---

## Phần 1: Sơ Đồ Nắm Nhanh Toàn Bộ Code Trong 5 Phút

| Thư mục / File | Vai trò cốt lõi (Ai hỏi file nào trả lời ngay ý đó) |
| :--- | :--- |
| `Source/models/state.py` | Định nghĩa `PublicGameState` & `PublicCellState` (bất biến `frozen=True`). Chặn ở ngay hàm khởi tạo `__post_init__`: nếu thẻ chưa lật (`is_revealed=False`) thì bắt buộc `status=UNKNOWN` và `clue=None`. |
| `Source/logic/variables.py` | `VariableManager`: Gán biến sơ cấp $C_1 \dots C_{N^2}$ cố định theo thứ tự row-major (`A1 -> 1, B1 -> 2...`). Biến phụ luôn cấp phát từ `N^2 + 1` trở đi (`new_aux_var`), không bao giờ lẫn với biến sơ cấp. |
| `Source/logic/evaluator.py` | `SemanticEvaluator`: Định giá trực tiếp một phép gán đầy đủ bằng phép đếm Python thuần (không gọi `CNFEncoder`), dùng để kiểm tra độ đúng đắn của bộ mã hóa CNF và kiểm tra đề hợp lệ. |
| `Source/logic/cnf_encoder.py` | Chuyển tự động 6 mẫu clue cốt lõi + 3 extensions sang CNF. Hỗ trợ cả **Direct Combinatorial** (tổ hợp trực tiếp, 0 biến phụ cho lực lượng) và **Sinz Sequential Counter** (mạch đếm tuần tự dùng biến phụ $s_{i,j}$). |
| `Source/solver/dpll.py` | Thuật toán DPLL tự viết 100%: `_unit_propagate` (lan truyền mệnh đề đơn), phát hiện xung đột mệnh đề rỗng `()`, `_pure_literal_eliminate`, chọn biến tất định (`FIXED_ORDER` hoặc `JEROSLOW_WANG`), đệ quy quay lui và điền `False` cho biến tự do để luôn trả về phép gán đầy đủ. |
| `Source/agent/deductive_agent.py` | Kiểm tra hệ quả logic bằng phản chứng (`KB_t ∧ ¬C_i` và `KB_t ∧ C_i`), cài đặt thêm tối ưu **Witness-Guided Pruning** giảm gần một nửa số lần gọi SAT. |
| `Source/agent/uniqueness.py` | Kiểm tra tính duy nhất nghiệm toàn cục bằng cách giải lần 1 tìm nghiệm $M^*$, sau đó nối thêm **mệnh đề chặn (blocking clause)** chỉ phủ định $N^2$ biến sơ cấp rồi giải lần 2. |
| `Source/agent/hint.py` | Gợi ý không gian lận: tìm ô đầu tiên bị ép buộc, sau đó thử rút bỏ lần lượt từng clue đang mở (**Deletion-based MUS**) để tìm tập clue tối thiểu giải thích tại sao ô đó chứng minh được. |

---

## Phần 2: 10 Câu Hỏi Vấn Đáp Trọng Tâm & Câu Trả Lời Điểm Tuyệt Đối

### Câu 1: Tại sao biết `KB_t` thỏa được (có nghiệm $M$ với $C_i = \text{True}$) vẫn KHÔNG được kết luận nhân vật $i$ là Criminal?
* **Trả lời:** Vì một mô hình thỏa $M$ chỉ là **một khả năng có thể xảy ra** (possible world). Nhân vật $i$ chỉ chắc chắn là Criminal khi $C_i = \text{True}$ trong **mọi** mô hình thỏa của $KB_t$ (tức $KB_t \models C_i$). Muốn chứng minh $KB_t \models C_i$ bằng SAT solver, ta dùng phương pháp **phản chứng**: giả sử ngược lại nhân vật $i$ là Innocent ($KB_t \land \neg C_i$). Nếu công thức này **UNSAT** (vô nghiệm), nghĩa là không tồn tại bất kỳ thế giới hợp lệ nào mà $i$ vô tội $\implies i$ bắt buộc là Criminal.

### Câu 2: Nếu trong đáp án ẩn nhân vật `B2` là Criminal, người chơi đoán mò bấm `Criminal` cho `B2` ngay từ đầu thì code xử lý thế nào?
* **Trả lời:** `GameEngine.submit_verdict` không so sánh trực tiếp với đáp án ẩn trước, mà gọi bộ kiểm tra hệ quả logic trên $KB_t$ công khai. Vì cả $KB_t \land \neg C_{B2}$ và $KB_t \land C_{B2}$ đều `SAT` (trạng thái `UNKNOWN`), `GameEngine` **từ chối ngay với mã `NOT_PROVABLE`** và giữ nguyên thẻ úp. Mã `CONTRADICTED` chỉ trả về khi $KB_t$ đã chứng minh được kết quả **ngược lại** (ví dụ $KB_t \models \neg C_{B2}$ mà người chơi lại chọn `Criminal`).

### Câu 3: Giải thích công thức chuyển `AT_MOST(k, R)` và `AT_LEAST(k, R)` sang CNF theo cách tổ hợp trực tiếp?
* **Trả lời:**
  * `AT_MOST(k, R)` ($\sum_{i \in R} C_i \le k$): Không được phép có bất kỳ nhóm $k + 1$ người nào trong $R$ cùng là tội phạm. Do đó, với mọi tập con $S \subseteq R$ có kích thước $|S| = k + 1$, ta có ràng buộc $\neg(\bigwedge_{i \in S} C_i) \equiv \bigvee_{i \in S} \neg C_i$. Số mệnh đề sinh ra là $\binom{|R|}{k+1}$.
  * `AT_LEAST(k, R)` ($\sum_{i \in R} C_i \ge k$): Tương đương với tối đa $|R| - k$ người là Innocent ($\neg C_i$), tức không được có $|R| - k + 1$ người cùng Innocent $\implies$ mọi tập con $S \subseteq R$ kích thước $|R| - k + 1$ phải có ít nhất 1 tội phạm: $\bigvee_{i \in S} C_i$. Số mệnh đề là $\binom{|R|}{|R|-k+1}$.
  * `EXACTLY(k, R)` là hội (nối danh sách mệnh đề) của `AT_MOST(k, R)` và `AT_LEAST(k, R)`.

### Câu 4: Tại sao trong thực nghiệm của nhóm, mã hóa Combinatorial lại chạy nhanh hơn Sinz Sequential Counter trên lưới 3×3 đến 5×5?
* **Trả lời:** Bộ đếm tuần tự Sinz có ưu thế tiệm cận $O(|R|\cdot k)$ khi $|R|$ lớn (ví dụ hàng chục/trăm biến), vì tổ hợp $\binom{|R|}{k+1}$ sẽ bùng nổ mũ. Tuy nhiên trong game Griductive, kích thước vùng $|R|$ rất nhỏ (hàng/cột tối đa 5 ô, vùng lân cận tối đa 8 ô, $\binom{8}{4} = 70$ mệnh đề). Sinz sinh thêm rất nhiều biến phụ $s_{i,j}$ (trung bình ~146 biến phụ trên bài test) khiến vòng lặp Unit Propagation trong Python phải duyệt và rút gọn nhiều biến hơn gấp ~4.4 lần so với Combinatorial!

### Câu 5: Quá trình Unit Propagation trong `dpll.py` hoạt động chính xác như thế nào? Khi nào phát hiện xung đột?
* **Trả lời:** Hàm `_unit_propagate` lặp liên tục: tìm mệnh đề có độ dài bằng 1 là `(lit,)`, gán biến tương ứng sao cho `lit = True` (`propagations += 1`), sau đó rút gọn toàn bộ tập mệnh đề:
  1. Mệnh đề nào chứa literal đang `True` thì đã thỏa $\to$ xóa bỏ mệnh đề đó.
  2. Trong các mệnh đề còn lại, literal nào đang `False` (`-lit`) thì bị gạch bỏ khỏi mệnh đề.
  3. **Xung đột (Conflict)** xảy ra ngay khi một mệnh đề bị gạch hết sạch các literal trở thành mệnh đề rỗng `()`! Khi đó nhánh đệ quy trả về `None` (`UNSAT`) và quay lui (`backtracks += 1`).

### Câu 6: Nếu công thức CNF thỏa được nhưng có biến không xuất hiện trong mệnh đề nào (biến tự do), DPLL trả về gì?
* **Trả lời:** Theo yêu cầu Mục 4.3 (*"Returning SAT with a complete assignment"*), khi danh sách mệnh đề rỗng (tất cả đã thỏa), DPLL duyệt qua toàn bộ dải biến `1..total_vars`; biến nào chưa có trong `assignment` sẽ được gán tất định `False`, đảm bảo kết quả trả về luôn là một phép gán đầy đủ.

### Câu 7: Trong `UniquenessChecker`, tại sao mệnh đề chặn (blocking clause) CHỈ lấy trên các biến sơ cấp $C_1 \dots C_{N^2}$ mà không đưa biến phụ vào?
* **Trả lời:** Vì tính duy nhất nghiệm của một màn chơi Griductive được định nghĩa trên trạng thái Tội phạm/Vô tội của $N^2$ nhân vật. Trong một số phép mã hóa (như Sinz Sequential Counter khi tổng thực tế nhỏ hơn $k$), một vài biến phụ $s_{i,j}$ có thể nhận cả `True` lẫn `False` mà vẫn thỏa công thức cho **cùng một nghiệm nhân vật**. Nếu đưa cả biến phụ vào blocking clause, SAT solver có thể chỉ đổi giá trị biến phụ rồi báo nhầm là có nghiệm thứ hai!

### Câu 8: Kỹ thuật `Witness-Guided Pruning` của nhóm giảm 43.7% số lần gọi SAT bằng nguyên lý nào? Có làm mất tính chính xác không?
* **Trả lời:** Hoàn toàn không mất tính chính xác (tương đương toán học 100%). Mỗi lần SAT solver trả về một mô hình thỏa $M$ của $KB_t$, mô hình $M$ đó đồng thời là **bằng chứng sống (witness)** chứng minh rằng với mọi ô chưa mở $j$, giá trị $C_j = M(C_j)$ chắc chắn khả thỏa cùng $KB_t$! Do đó:
  * Nếu qua các lần gọi trước, ô $j$ đã từng thấy một mô hình có $C_j = \text{True}$ VÀ một mô hình khác có $C_j = \text{False}$, thì chắc chắn cả 2 nhánh đều `SAT` $\implies$ kết luận ngay `UNKNOWN` mà tốn **0 lần gọi SAT**!
  * Nếu ô $j$ mới thấy $C_j = \text{True}$, ta chỉ cần gọi **1 truy vấn duy nhất** kiểm tra nhánh đối lập $KB_t \land \neg C_j$ thay vì gọi 2 truy vấn!

### Câu 9: Nhóm đã cài đặt những phần mở rộng (Extensions) nào? Mã hóa Compound và Connectivity ra sao?
* **Trả lời:** Nhóm cài trọn bộ **5 họ extensions** khác biệt bao phủ toàn bộ gợi ý Mục 3.2 và Hình 1 đề bài:
  1. *Advanced Regions* (`INTERSECTION`, `COMMON_NEIGHBORS`, `CORNERS`, `BOUNDARY`, `BETWEEN`, `DIRECTIONAL`, `PROFESSION`).
  2. *Regional Count Comparison* (`MORE_CRIMINALS`, `EQUAL_CRIMINALS` triệt tiêu phần giao $R_1 \cap R_2$ và đặt biến phụ đảo dấu $\bar{A}_j \leftrightarrow \neg C_j$).
  3. *Parity* (`ODD`/`EVEN`) dùng biến phụ trung gian **Tseitin XOR** $z_m \leftrightarrow (z_{m-1} \oplus C_{i_m})$, tốn $4(|R|-2)+2$ mệnh đề 3-SAT thay vì $2^{|R|-1}$ mệnh đề.
  4. *Compound Clues* (`AND`, `OR`, `IMPLIES`): với `OR(F₁, F₂)`, dùng biến chọn dương $(s_1 \lor s_2) \land (\neg s_1 \lor D) \land (\neg s_2 \lor E)$ đảm bảo tương đương khả thỏa ngay cả khi $F_1, F_2$ chứa biến phụ nội bộ; với `IMPLIES(A, B)` chuyển thành `OR(¬A, B)` qua phép phủ định cấu trúc De Morgan.
  5. *Orthogonal Connectivity* (`CONNECTED` kề cạnh trên lưới): với dải 1 chiều (hàng/cột/tia như ô D5 Hình 1), cấm mọi bộ ba rời rạc `1...0...1` bằng $(\neg l_a \lor l_b \lor \neg l_c)$ (0 biến phụ); với vùng 2 chiều tổng quát, chọn gốc chuẩn chỉ số nhỏ nhất $r_i \leftrightarrow (l_i \land \bigwedge_{p < i} \neg l_p)$ và lan truyền khoảng cách BFS $d_{i,t}$ trong $m-1$ bước!

### Câu 10: Chức năng `Hint` tìm ra clue liên quan bằng cách nào khi không được phép đọc đáp án ẩn?
* **Trả lời:** Sau khi tìm được nhân vật $i^*$ bị ép buộc (ví dụ $KB_t \land \neg C_{i^*}$ là `UNSAT`), `HintEngine` dùng thuật toán **Deletion-based MUS (Minimal Unsatisfiable Subset)**: duyệt qua từng clue công khai $c$ đang mở, thử tạm bỏ $c$ ra khỏi $KB_t$ rồi chạy lại DPLL trên $(KB_t \setminus \{c\}) \land \neg C_{i^*}$. Nếu vẫn `UNSAT` nghĩa là không cần $c$ vẫn chứng minh được $\to$ loại bỏ $c$; nếu biến thành `SAT` nghĩa là $c$ bắt buộc phải có mặt $\to$ giữ lại $c$ để highlight lên màn hình!
