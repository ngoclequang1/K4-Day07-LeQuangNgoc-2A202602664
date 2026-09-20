# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Quang Ngọc

**MSSV:** 2A202602664

**Nhóm:** G63

**Ngày cập nhật:** 2026-09-20

**Trạng thái:** Đã chạy corpus và benchmark Shopee; đã bổ sung báo cáo cá nhân; chưa nộp bài.

> Báo cáo được soạn với sự hỗ trợ của Codex dựa trên mã nguồn và kết quả chạy thực tế. Người học cần đọc hiểu, rà soát phần diễn giải và xác nhận thông tin cá nhân trước khi nộp. Mục 5 dùng kết quả chạy thực tế trên corpus Shopee. Chưa có kết quả của các thành viên khác hoặc trải nghiệm demo nhóm để báo cáo.

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

## 5. Kết quả truy xuất của tôi — benchmark của Nam

### Bộ câu hỏi và dữ liệu dùng chung

Dùng **nguyên văn 5 câu tiếng Anh và filter** từ [ket_qua_benchmark (nam).txt](../ket_qua_benchmark%20(nam).txt), lưu trong [benchmark_queries.json](../benchmark_queries.json). Q1/Q3 lọc buyer, Q2/Q5 lọc seller, **Q4 không lọc**. Không dịch câu hỏi trước khi embedding. File của Nam được giữ nguyên.

Corpus hiện có **9 tài liệu tóm lược từ 6 nguồn Shopee**, lấy ngày 20/09/2026. So với lần trước, thêm `buyer-return-conditions.md` (hạn yêu cầu, lý do, điều kiện giải ngân) và `seller-return-shipping.md` (phí và xử lý kiện); bổ sung trường hợp chưa nhận hàng không cần bằng chứng vào tài liệu bằng chứng. Nguồn bổ sung là các mục 3, 5, 7–9 của bản chính sách đã crawl, hiệu lực 11/03/2026. Không lấy đáp án từ trí nhớ hoặc suy đoán.

Xem [sources.csv](../data/shopee-return-refund/sources.csv), [crawl log](shopee_crawl_log.json), [corpus audit](shopee_corpus_audit.json). Metadata gồm audience, category, source_url, retrieved_at, document_version, source_sha256. Frontmatter không được embedding. Tài liệu là bản tóm lược đối chiếu, không phải toàn văn; `public-source` không phải giấy phép mở. HTML gốc nằm trong `.cache/shopee/` và không commit.

**Giới hạn so sánh với Nam:** file Nam ghi 7 tài liệu, 14 chunk nhưng không ghi model, phiên bản corpus, gold answer hay nội dung chunk. Lần này có 9 tài liệu. Vì vậy đã đồng bộ câu hỏi/filter, nhưng chưa thể xếp hạng hai thành viên từ hai file hiện tại. Cần Nam nhận cùng corpus/đáp án chuẩn/model rồi chạy lại. Không suy rằng Nam dùng mock chỉ từ các score thấp.

### Chiến lược và cách chạy

Chiến lược cá nhân: **Fixed-Size Chunking, 350 ký tự/chunk, overlap 35 ký tự**, theo cách chia mô tả trong [chunking_experiment_report.md](../data/chunking_experiment_report.md). File đó chỉ mô tả nguyên lý, không ấn định kích thước/overlap; 350/35 là cấu hình thí nghiệm này. `FixedSizeChunker` cắt chuỗi tại các vị trí 0, 315, 630…; chunk cuối có thể ngắn hơn. Không ưu tiên ranh giới câu hay tiêu đề, không lặp thêm tiêu đề. Baseline đối chiếu: heading350 và recursive350. Cả ba dùng cùng corpus, câu hỏi, top-k=3 và embedding thật `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, chuẩn hóa vector trước dot product.

Fixed-size đơn giản, giới hạn độ dài rõ ràng và có số chunk dự đoán được; overlap giảm mất thông tin gần ranh giới nhưng không bảo đảm giữ trọn quy trình. Có thể cắt giữa từ/câu hoặc tách điều kiện khỏi kết luận, đúng hạn chế mà báo cáo thử nghiệm nêu. Đây là ba thí nghiệm trên mã nguồn cá nhân, chưa phải ba kết quả của ba thành viên.

Agent dùng **extractive-offline**: trả các đoạn nguồn đã truy xuất, kèm số trích dẫn; chưa dùng LLM sinh câu trả lời. `answer_from_results` dùng đúng context sau lọc. Output có thể chứa thông tin thừa và thiếu đáp án, không được tính là câu trả lời sinh đã đạt chất lượng.

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/prepare_shopee_corpus.py
.\.venv\Scripts\python.exe -X utf8 scripts/use_nam_benchmark.py
.\.venv\Scripts\python.exe -X utf8 bench.py
.\.venv\Scripts\python.exe -X utf8 scripts/update_shopee_reports.py
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

Lần đầu cần `requirements-local.txt` và chạy `scripts/download_embedding_model.py`. Prepare dùng bản crawl đã lưu; khi trang thay đổi cần rà soát lại bản tóm lược. Log mới: [ket_qua_benchmark.txt](../ket_qua_benchmark.txt), [benchmark_results.json](benchmark_results.json). Hash spec và corpus được lưu để tránh trộn kết quả khác phiên bản.

### Câu hỏi, gold answer và kết quả fixed-size

Gold answer là đáp án được đối chiếu từ corpus hiện tại, **không phải đáp án chuẩn do Nam cung cấp** vì file của Nam không có gold. Q3/Q4 tổng hợp nhiều tài liệu, nên công cụ hỗ trợ `gold_docs` thay vì chỉ một doc_id.

| Câu | Câu hỏi nguyên văn | Filter | Đáp án chuẩn |
|---|---|---|---|
| Q1 | How long does a buyer have to request a return or refund? | {'audience': 'buyer'} | 15 ngày từ khi đơn cập nhật giao thành công; thực phẩm tươi sống/đông lạnh 24 giờ. Quá hạn chỉ được xem xét hỗ trợ. |
| Q2 | What must a seller do after a buyer opens a return request? | {'audience': 'seller'} | Theo dõi thông báo Shopee, đối chiếu hàng hoàn. Khi không đồng ý quyết định hoặc hàng hoàn có vấn đề, phản hồi trong 2 ngày lịch từ thông báo, trừ thời hạn khác; không phản hồi được coi là đồng ý. |
| Q3 | When is the buyer's refund released after a return is approved? | {'audience': 'buyer'} | Duyệt trả hàng chưa đồng nghĩa giải ngân ngay: tùy xác nhận nhận hàng, chấp thuận hoàn không trả hàng, hoặc quyết định hoàn sớm của Shopee. Tiền về tùy phương thức: thẻ 7–14 ngày làm việc, Napas 2–5 ngày làm việc, ví khoảng 24 giờ; COD/chuyển khoản về ngân hàng khoảng 2 ngày làm việc. Tính từ chấp nhận hoàn tiền, có thể phụ thuộc ngân hàng. |
| Q4 | Which reasons and evidence can support a return or refund claim? | Không | Các lý do: chưa nhận/thiếu hàng, giả/nhái, lỗi/hư, sai, khác mô tả, hết hạn, người bán đồng ý; không còn nhu cầu có điều kiện riêng. Bằng chứng tùy trường hợp: ảnh/video rõ tình trạng, mã vận đơn, số lượng, lịch sử trao đổi. Chưa nhận hàng không cần bằng chứng theo hướng dẫn Shopee. |
| Q5 | Who pays return shipping and what should the seller do with the parcel? | {'audience': 'seller'} | Phí phụ thuộc lỗi, loại yêu cầu và hình thức gửi: người bán chịu theo mục 7.1 nhưng có miễn trừ; người mua không trả phí lấy tại nhà/bưu cục, tự sắp xếp ứng phí rồi được hoàn/hỗ trợ theo điều kiện Mall/ngoài Mall. Người bán đối chiếu kiện và phản hồi vấn đề trong 2 ngày lịch từ thông báo, trừ thời hạn khác. |

| Câu | Top-1 | Cosine | Hạng đủ toàn bộ bằng chứng | Các chuỗi bằng chứng còn thiếu trong top-3 |
|---|---|---:|---|---|
| Q1 | `buyer-return-conditions::01` | 0.677249 | 1 | Không |
| Q2 | `seller-return-handling::01` | 0.626721 | 1 | Không |
| Q3 | `buyer-return-conditions::01` | 0.576306 | Chưa đủ | không cần trả hàng, 7–14 ngày làm việc, 2–5 ngày làm việc, 2 ngày làm việc, chấp nhận hoàn tiền |
| Q4 | `buyer-warranty-claim::02` | 0.457181 | Chưa đủ | hàng giả/nhái, hết hạn, điều kiện riêng, mã vận đơn, ảnh, không cần |
| Q5 | `seller-return-shipping::01` | 0.539798 | Chưa đủ | đối chiếu hàng hoàn, 2 ngày lịch, thời hạn khác |

**2/5 câu đủ toàn bộ chuỗi bằng chứng trong top-3** theo cấu hình filter của Nam. Đây là kiểm tra đủ ý, không đồng nghĩa chỉ 2 câu có đoạn liên quan. Các câu còn lại có thể có bằng chứng một phần.

Kiểm tra tự động chỉ tìm các chuỗi đã khai báo trong context thuộc các tài liệu gold. Proxy 2/1/0 lần lượt nghĩa là đủ bằng chứng ngay top-1 / cần top-2 hoặc top-3 / chưa đủ. Proxy nghiêm ngặt này không thay điểm rubric: câu trả lời một phần có thể được chấm khác. Không dùng doc_id hoặc cosine để tự kết luận đáp án đúng.

**Đối chiếu output thực tế của fixed-size:**

- Q1: có hạn 15 ngày, ngoại lệ 24 giờ và điều kiện xét hỗ trợ quá hạn trong top-1.
- Q2: các chuỗi kiểm tra về thông báo, 2 ngày lịch và thời hạn khác nằm ở top-1; top-2 bổ sung hậu quả không phản hồi. Cần đọc cùng các đoạn để giữ đủ điều kiện áp dụng.
- Q3: lấy nhầm đoạn thời hạn gửi yêu cầu và một phần điều kiện giải ngân; không lấy được bảng thời gian theo phương thức. Không thể dùng 15 ngày gửi yêu cầu làm thời gian tiền về.
- Q4: top-1 là bảo hành, các đoạn sau chưa chứa lý do và hướng dẫn bằng chứng cần thiết. Câu này thất bại về nội dung dù có tài liệu gold xuất hiện.
- Q5: có các điều khoản phí người bán và người mua trong top-3 nhưng thiếu hướng dẫn đối chiếu kiện, thời hạn 2 ngày lịch và ngoại lệ. Không đủ cả hai vế của câu hỏi.

### So sánh ba chiến lược

| Chiến lược | Số chunk | Ký tự TB | Đủ bằng chứng theo filter Nam | Proxy theo Nam /10 | Proxy bỏ filter /10 |
|---|---:|---:|---:|---:|---:|
| fixed | 23 | 275.30 | 2/5 | 4 | 4 |
| recursive | 27 | 216.37 | 2/5 | 3 | 2 |
| heading | 27 | 233.07 | 2/5 | 3 | 3 |

Không so các score này với bộ 5 câu tiếng Việt cũ. Câu hỏi tiếng Anh trên corpus tiếng Việt và câu hỏi nhiều vế làm thay đổi độ khó; chưa có thí nghiệm đối chứng riêng để định lượng ảnh hưởng của ngôn ngữ.

### Có và không có metadata filter — Q2

| Chiến lược | Top-3 bỏ filter | Top-3 theo Nam (seller) | Đủ bằng chứng trước → sau |
|---|---|---|---|
| fixed | `seller-return-handling::01` (0.6267); `buyer-return-conditions::02` (0.5529); `seller-return-handling::02` (0.5512) | `seller-return-handling::01` (0.6267); `seller-return-handling::02` (0.5512); `seller-refund-dispute::01` (0.5452) | True → True |
| recursive | `buyer-return-conditions::03` (0.6182); `seller-return-handling::03` (0.6090); `seller-return-handling::01` (0.6065) | `seller-return-handling::03` (0.6090); `seller-return-handling::01` (0.6065); `seller-return-handling::02` (0.5812) | False → True |
| heading | `seller-return-handling::03` (0.6414); `seller-return-handling::02` (0.6159); `seller-return-handling::01` (0.6065) | `seller-return-handling::03` (0.6414); `seller-return-handling::02` (0.6159); `seller-return-handling::01` (0.6065) | True → True |

Với recursive, bỏ filter làm mất đoạn chứa 2 ngày lịch/thời hạn khác khỏi top-3; lọc seller đưa đoạn đó trở lại. Với heading, Q2 đã có cùng top-3 seller trước lọc nên filter không cải thiện kết quả câu này. Q4 có filter `null` đúng theo Nam; hai lần chạy của Q4 đều không lọc, không được diễn giải là A/B filter.

### Phân tích lỗi và hướng cải thiện chưa thử

Lỗi chính là không bao phủ đủ các vế: Q3 cần điều kiện giải ngân cùng thời gian theo phương thức, Q4 cần lý do cùng bằng chứng, Q5 cần phí cùng xử lý kiện. Fixed-size có thể cắt giữa lời giải thích, còn overlap 35 ký tự không nối được những điều khoản ở xa nhau. Có thể thử truy vấn con cho từng vế, bổ sung chunk lân cận hoặc reranker; mọi thành viên cần thống nhất cấu hình trước khi so sánh lại. Chưa tăng top-k hoặc sửa câu hỏi để làm đẹp kết quả hiện tại.

### Kiểm thử và tiến độ cá nhân

Các mục 1–4 giữ thí nghiệm cá nhân giai đoạn trước; mục 5 được thay hoàn toàn bằng lần chạy theo Nam. Kết quả test mới lưu tại [pytest_shopee_output.txt](pytest_shopee_output.txt), gồm 42 test gốc và các test bổ sung cho heading/context/corpus/khớp câu hỏi-filter.

- [x] Đồng bộ nguyên văn 5 câu và filter của Nam.
- [x] Bổ sung điều khoản thiếu, cập nhật 9 MD, hai CSV và audit.
- [x] Chạy lại ba chiến lược bằng embedding thật; lưu đầy đủ top-3 và output.
- [x] Viết lại bảng kết quả và phân tích lỗi; không giữ kết luận 5/5 của lần trước.
- [ ] Nam và các thành viên khác chạy lại cùng corpus/model/gold để so sánh công bằng.
- [ ] Đánh giá thêm LLM sinh nếu cần chấm chất lượng câu trả lời RAG sinh.
- [ ] Thực hiện demo và ghi bài học từ trao đổi thực tế.

## Tự đánh giá tiến độ phần cá nhân

Đã cập nhật phần kỹ thuật cá nhân theo benchmark Nam. Tổng điểm tối đa vẫn là 60 theo rubric; các proxy không phải điểm giảng viên chấm. Chưa có trải nghiệm demo để ghi nhận và chưa đủ điều kiện xếp hạng giữa các thành viên.
