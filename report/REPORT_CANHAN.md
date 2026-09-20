# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Quang Ngọc

**MSSV:** 2A202602664

**Nhóm:** Chưa lập nhóm

**Ngày cập nhật:** 2026-09-20

**Trạng thái:** Đã chuẩn bị phần cá nhân không phụ thuộc nhóm; chưa nộp bài.

> Báo cáo được soạn với sự hỗ trợ của Codex dựa trên mã nguồn và kết quả chạy thực tế. Người học cần đọc hiểu, rà soát phần diễn giải và xác nhận thông tin cá nhân trước khi nộp. Mục 5 chờ corpus và câu hỏi chung; chưa có kết quả thi đua hoặc trải nghiệm demo nhóm để báo cáo.

Phần cá nhân có tối đa 60 điểm: khởi động (5), hướng tiếp cận (10), code (30), dự đoán độ tương tự (5), kết quả truy xuất trên bộ câu hỏi chung (10). Hoàn thiện nội dung không đồng nghĩa đã được giảng viên chấm điểm.

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Bài tập 1.1)

**Độ tương tự cosine cao nghĩa là gì?**

Hai vector có cosine gần 1 khi cùng hướng. Với mô hình embedding biểu diễn ngữ nghĩa tốt, điều này thường cho thấy hai đoạn văn có nội dung hoặc ý định gần nhau dù khác từ vựng; riêng mock embedding của lab không có tính chất ngữ nghĩa này.

**Ví dụ dự kiến có độ tương tự CAO với embedding ngữ nghĩa:**

- Câu A: “Tôi muốn trả lại sản phẩm bị lỗi.”
- Câu B: “Tôi cần hoàn trả món hàng không hoạt động.”
- Lý do: cả hai cùng diễn đạt nhu cầu trả hàng do sản phẩm có vấn đề.

**Ví dụ dự kiến có độ tương tự THẤP với embedding ngữ nghĩa:**

- Câu A: “Khách hàng muốn biết quy trình hoàn tiền.”
- Câu B: “Đội bóng đang luyện tập để thi đấu cuối tuần.”
- Lý do: câu đầu nói về dịch vụ mua hàng, câu sau nói về thể thao.

**Tại sao dùng cosine thay cho khoảng cách Euclid?**

Cosine tập trung vào hướng vector nên không đổi khi nhân một vector với hệ số dương. Khoảng cách Euclid còn chịu ảnh hưởng của độ lớn vector; tuy nhiên khi cả hai vector đã chuẩn hóa về độ dài 1 thì hai cách đo cho cùng thứ tự gần/xa, vì `distance² = 2 - 2 × cosine`. Vì vậy cosine không phải luôn tốt hơn Euclid trong mọi cấu hình.

### Bài toán Chunking (Bài tập 1.2)

Với tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`:

```text
step = 500 - 50 = 450
count = ceil((10000 - 50) / (500 - 50))
      = ceil(9950 / 450)
      = 23 chunks
```

Nếu tăng `overlap=100`:

```text
step = 500 - 100 = 400
count = ceil((10000 - 100) / (500 - 100))
      = ceil(9900 / 400)
      = 25 chunks
```

Chạy `FixedSizeChunker` xác nhận lần lượt **23** và **25** chunk. Overlap lớn hơn làm bước trượt nhỏ đi, tăng số chunk và lượng nội dung lặp; đổi lại, thông tin sát ranh giới có thêm cơ hội xuất hiện đầy đủ trong một chunk. Chi phí lưu trữ và embedding cũng tăng theo.

Lệnh tái lập bài toán này và thí nghiệm ở mục 4:

```powershell
.\.venv\Scripts\python.exe -X utf8 personal_experiments.py
```

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm Chunking

**`SentenceChunker.chunk`**

Dùng regex `(?<=[.!?])\s+` để tách tại khoảng trắng sau dấu kết câu; lookbehind giữ lại dấu câu. Sau đó loại khoảng trắng hai đầu và gom tối đa `max_sentences_per_chunk` câu bằng dấu cách; văn bản rỗng hoặc chỉ có khoảng trắng trả `[]`.

Cách tách đơn giản này có thể nhận sai chữ viết tắt như `TS.` hoặc `v.v.`, và chưa nhận diện đầy đủ dấu kết câu trước dấu ngoặc kép. Bộ chia giới hạn số câu, không bảo đảm giới hạn số ký tự; một câu rất dài vẫn tạo chunk dài.

**`RecursiveChunker.chunk` / `_split`**

Ưu tiên separator `['\n\n', '\n', '. ', ' ', '']`, từ ranh giới đoạn đến từ và ký tự. Nếu đoạn còn dài thì tiếp tục với separator nhỏ hơn, đồng thời gom các mảnh liền kề khi tổng độ dài không vượt `chunk_size` để tránh tạo quá nhiều mảnh vụn.

Các trường hợp dừng: văn bản rỗng trả `[]`; đoạn vừa kích thước trả nguyên đoạn; hết separator hoặc gặp separator rỗng thì cắt cứng theo số ký tự. Thuật toán giữ nội dung và separator, nên ghép các chunk theo thứ tự khôi phục văn bản gốc; `chunk_size <= 0` báo `ValueError`. Bộ chia này chưa có overlap và có thể phải cắt giữa từ nếu không tìm được ranh giới phù hợp.

**`compute_similarity`**

Tính tích vô hướng rồi chia cho tích hai norm. Nếu một vector có norm bằng 0 thì trả `0.0`; vector khác số chiều bị từ chối, và kết quả được giới hạn trong `[-1, 1]` để xử lý sai số dấu phẩy động.

**`ChunkingStrategyComparator.compare`**

Chạy ba chiến lược trên cùng văn bản, trả các khóa `fixed_size`, `by_sentences`, `recursive`; mỗi khóa có `count`, `avg_length`, `chunks`. Văn bản rỗng cho số lượng và độ dài trung bình bằng 0. Cấu hình so sánh dùng fixed-size overlap bằng 10% kích thước, tối đa 50 ký tự; sentence gom 3 câu; recursive dùng kích thước được truyền vào.

### Lớp EmbeddingStore

**`add_documents` + `search`**

Store dùng danh sách trong bộ nhớ, mỗi `Document` tương ứng một record chứa ID, content, metadata và embedding. Việc chunking diễn ra trước khi gọi store; metadata được sao chép sâu để thao tác trên dữ liệu đầu vào hoặc kết quả tìm kiếm không sửa nhầm dữ liệu đã lưu.

`search` nhúng truy vấn rồi tính dot product với các vector, sắp xếp giảm dần và lấy tối đa `top_k`. Dot product tương đương cosine khi vector đã chuẩn hóa, như `MockEmbedder` đang dùng. Điểm bằng nhau giữ thứ tự thêm; kết quả gồm `id`, `content`, `metadata`, `score`, không kèm vector dài. Store rỗng hoặc `top_k <= 0` trả `[]`.

**`search_with_filter` + `delete_document`**

Lọc tất cả điều kiện metadata trước khi tính top-k. Nếu chọn top-k rồi mới lọc, các kết quả sai đối tượng có thể chiếm hết vị trí dù store còn tài liệu hợp lệ; tìm kiếm có lọc và không lọc cùng dùng `_search_records` để giữ cách xếp hạng nhất quán.

`metadata['doc_id']` giữ ID tài liệu gốc nếu đã được cung cấp, còn khi thiếu thì dùng `Document.id`. `delete_document` loại tất cả record có cùng `doc_id` và trả `True` khi thực sự xóa được; khi chia một file thành nhiều chunk, cần gán ID gốc này cho mọi chunk.

Hạn chế: store không lưu bền vững sau khi kết thúc chương trình và tìm kiếm tuyến tính theo số record. Không dùng ChromaDB trong phần lõi của lab.

### KnowledgeBaseAgent

**`answer`**

Agent giữ store và `llm_fn`, truy xuất top-k rồi tạo context đánh số `[1]`, `[2]`, `[3]` kèm nguồn, ID tài liệu và ID chunk. Prompt yêu cầu chỉ dùng context, coi tài liệu là dữ liệu tham khảo, trích dẫn số nguồn và nói rõ khi thiếu thông tin; cuối prompt là câu hỏi trước khi gọi `llm_fn`.

Khi không có kết quả, agent trả thông báo thiếu dữ liệu mà không gọi LLM. Prompt chưa bảo đảm một LLM bất kỳ luôn tuân thủ; chữ ký `answer` giữ theo đề nên chưa nhận metadata filter. Khi làm benchmark cần xử lý truy xuất có lọc trong công cụ benchmark và bảo đảm câu trả lời sử dụng chính các chunk đã lọc.

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

**Môi trường thực tế:** Windows, Python **3.10.11**, pytest **9.1.1**, python-dotenv **1.2.2**, mock embedding 64 chiều. Python 3.11 là chuẩn repo nhưng đường dẫn 3.11 được đăng ký trên máy không còn tồn tại; hướng dẫn codelab cho phép tiếp tục với Python 3.10+. File `.python-version` và `requirements.txt` được giữ nguyên.

**Số lượng test vượt qua: 42 / 42.** Không còn `TODO` hoặc `NotImplementedError` trong `src/` tại lần kiểm tra này.

Lệnh chạy từ thư mục gốc:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

Output thực tế, cũng lưu ở [pytest_output.txt](pytest_output.txt):

```text
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-9.1.1, pluggy-1.6.0 -- C:\AI in Action Lab\Lab 07\K4-Day07-LeQuangNgoc-2A202602664\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\AI in Action Lab\Lab 07\K4-Day07-LeQuangNgoc-2A202602664
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.16s ==============================
```

**Kiểm tra demo:** `main.py "Chunking là gì?"` chạy thành công, nạp 5 tài liệu mẫu và thực hiện tìm kiếm cùng lời gọi agent. File mẫu `customer_support_playbook.txt` không có trong repo được bỏ qua theo thiết kế; xem [demo_output.txt](demo_output.txt).

Demo dùng embedding và LLM giả lập. Demo chạy thành công xác nhận luồng tích hợp, chưa chứng minh agent trả lời chính xác về chính sách thương mại điện tử.

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Năm cặp câu và dự đoán được lưu trong [similarity_predictions.json](similarity_predictions.json) trước khi chạy. Dự đoán dựa trên ý nghĩa: cặp 5 cao nhất vì hai câu trùng nhau, cặp 4 thấp nhất vì khác chủ đề rõ rệt.

**Backend thực tế:** `MockEmbedder(dim=64)`, không cần API key. Thí nghiệm đặt trước quy ước `cosine >= 0.5` là cao, còn lại là thấp để đối chiếu cột “Đúng?”; đây không phải ngưỡng chuẩn đánh giá retrieval. Các câu ví dụ không được dùng làm bằng chứng về chính sách của bất kỳ sàn nào.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng theo quy ước? |
|---|---|---|---|---:|---|
| 1 | Tôi muốn trả lại sản phẩm bị lỗi. | Tôi cần hoàn trả món hàng không hoạt động. | cao | -0.043455 | Không |
| 2 | Người bán cần phản hồi yêu cầu bảo hành. | Cửa hàng phải trả lời đề nghị sửa chữa trong thời gian bảo hành. | cao | -0.083983 | Không |
| 3 | Khách hàng muốn biết quy trình hoàn tiền. | Đội bóng đang luyện tập để thi đấu cuối tuần. | thấp | -0.046237 | Có |
| 4 | Hóa đơn được dùng để đối chiếu thông tin mua hàng. | Sao Mộc là một hành tinh trong Hệ Mặt Trời. | thấp | 0.232198 | Có |
| 5 | Tôi cần kiểm tra tình trạng đơn hàng. | Tôi cần kiểm tra tình trạng đơn hàng. | cao | 1.000000 | Có |

Kết quả đầy đủ: [ket_qua_thi_nghiem_canhan.txt](ket_qua_thi_nghiem_canhan.txt) và [ket_qua_thi_nghiem_canhan.json](ket_qua_thi_nghiem_canhan.json).

**Nhận xét từ kết quả:** cặp 2 có ý nghĩa gần nhau nhưng có điểm thấp nhất, còn cặp 4 khác chủ đề đạt điểm cao hơn cả cặp 1 và 2. Mock băm chuỗi rồi sinh vector giả ngẫu nhiên, không học ngữ nghĩa; vì vậy không thể dùng các điểm này để kết luận rằng embedding ngữ nghĩa không hiểu tiếng Việt. Cặp 5 đạt 1 đúng dự đoán vì cùng chuỗi đầu vào tạo cùng vector; cần chạy lại bằng embedder thật nếu muốn đánh giá sự tương đồng về ý nghĩa.

### Chuẩn bị thêm: so sánh chunking trên tài liệu mẫu

Đã chạy ba chiến lược trên ba tài liệu kỹ thuật có sẵn để quan sát cấu trúc chunk. Đây là thử nghiệm cá nhân; các tài liệu này không thay thế corpus chính sách thương mại điện tử của nhóm.

Cấu hình: fixed-size `chunk_size=200`, `overlap=20`; sentence `max_sentences_per_chunk=3`; recursive `chunk_size=200`, không overlap. Độ dài tính theo ký tự, không phải token.

| Tài liệu mẫu | Chiến lược | Số chunk | Độ dài trung bình |
|---|---|---:|---:|
| vector_store_notes.md | fixed_size | 14 | 195.64 |
| vector_store_notes.md | by_sentences | 8 | 308.13 |
| vector_store_notes.md | recursive | 16 | 154.94 |
| rag_system_design.md | fixed_size | 15 | 198.67 |
| rag_system_design.md | by_sentences | 5 | 537.80 |
| rag_system_design.md | recursive | 18 | 150.00 |
| vi_retrieval_notes.md | fixed_size | 10 | 184.70 |
| vi_retrieval_notes.md | by_sentences | 5 | 331.60 |
| vi_retrieval_notes.md | recursive | 13 | 128.23 |

Sentence tạo ít chunk hơn nhưng độ dài trung bình vượt 200 ký tự vì chỉ giới hạn số câu. Recursive giữ ranh giới có sẵn nên không lấp đầy mọi chunk; fixed-size có độ dài gần mục tiêu và lặp nội dung do overlap. Chưa thể chọn chiến lược truy xuất tốt nhất chỉ từ số lượng và độ dài: cần bộ câu hỏi chung và kiểm tra đoạn nào thực sự chứa đáp án.

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

**Chưa thực hiện vì chưa lập nhóm.** Chưa có corpus chung 5–10 tài liệu chính sách đã xác minh, 5 câu hỏi chung, gold answer hoặc phân công chiến lược. Thí nghiệm ở mục 4 không được tính thay cho benchmark này.

Các việc cần làm sau khi có nhóm:

- [ ] Thống nhất corpus và đúng 5 câu hỏi cùng gold answer, xác định chunk chứa bằng chứng.
- [ ] Chốt chiến lược cá nhân khác các thành viên; bảo đảm nhóm có người thử heading/section.
- [ ] Tạo `bench.py` nạp corpus, tách frontmatter, chunk ngoài store và giữ metadata trên mọi chunk.
- [ ] Chạy 5 câu hỏi, lưu top-3 gồm ID chunk, nguồn, nội dung, score và câu trả lời agent vào `ket_qua_benchmark.txt`.
- [ ] So sánh câu hỏi cần lọc `audience` với/không filter trên ba chiến lược, kiểm tra nội dung có chứa đáp án.
- [ ] Phân tích ít nhất một lỗi truy xuất thật và đề xuất cải thiện.
- [ ] Bổ sung bảng kết quả dưới đây và bài học thực tế từ demo nhóm.

| # | Câu hỏi chung | Top-1 chunk | Score | Liên quan? | Câu trả lời agent |
|---|---|---|---|---|---|
| 1 | Chờ nhóm thống nhất | Chưa chạy | Chưa đo | Chưa đánh giá | Chưa có |
| 2 | Chờ nhóm thống nhất | Chưa chạy | Chưa đo | Chưa đánh giá | Chưa có |
| 3 | Chờ nhóm thống nhất | Chưa chạy | Chưa đo | Chưa đánh giá | Chưa có |
| 4 | Chờ nhóm thống nhất | Chưa chạy | Chưa đo | Chưa đánh giá | Chưa có |
| 5 | Chờ nhóm thống nhất | Chưa chạy | Chưa đo | Chưa đánh giá | Chưa có |

**Số câu có chunk liên quan trong top-3:** Chưa đo.

**Điều học được từ thành viên/nhóm khác qua demo:** Chưa có hoạt động nhóm để ghi nhận.

## Tự đánh giá tiến độ phần cá nhân

| Tiêu chí | Điểm tối đa | Trạng thái và bằng chứng |
|---|---:|---|
| Khởi động | 5 | Đã giải thích, tính toán và kiểm tra số chunk bằng code |
| Hướng tiếp cận | 10 | Đã mô tả cách triển khai cùng hạn chế thực tế |
| Hoàn thiện code | 30 | 42/42 test pass, demo chạy thành công |
| Dự đoán độ tương tự | 5 | Đã lưu dự đoán trước khi chạy, đủ 5 cặp và phân tích giới hạn mock |
| Kết quả truy xuất của tôi | 10 | Chờ corpus, câu hỏi và chiến lược chung của nhóm |
| **Tổng** | **60** | **Đã chuẩn bị các hạng mục tương ứng tối đa 50 điểm; 10 điểm phụ thuộc benchmark nhóm. Đây không phải điểm đã được chấm.** |

Trước khi nộp, người học cần rà soát lời giải, thực hành giải thích lại thuật toán và bổ sung những phần phụ thuộc nhóm ở mục 5.
