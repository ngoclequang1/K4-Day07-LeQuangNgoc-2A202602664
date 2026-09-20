CORPUS SHOPEE — phiên bản thu thập 2026-09-20

9 tài liệu Markdown là bản tóm lược đã đối chiếu từ 6 trang Shopee công khai.
Không phải toàn văn chính sách; hai tài liệu bảo hành dùng chung một nguồn,
nhưng tách phạm vi người mua/người bán. Benchmark chỉ áp dụng phạm vi này.
Giữ các tiêu đề mục được chọn từ nguồn; nội dung bên dưới được diễn giải.

Nguồn, phiên bản, ngày lấy và audience: sources.csv và frontmatter từng MD.
Nhật ký crawl/robots/HTTP: ../../report/shopee_crawl_log.json
Kiểm kê/hash bản tóm lược: ../../report/shopee_corpus_audit.json
HTML gốc và bản trước khi cập nhật: ../../.cache/shopee/ (không commit).
public-source chỉ mô tả nguồn truy cập công khai, không phải giấy phép mở.
not-stated nghĩa là trang không nêu phiên bản, không tự suy ngày hiệu lực.

Tái lập từ thư mục gốc, theo thứ tự:
  .\.venv\Scripts\python.exe -X utf8 scripts/crawl_shopee.py
  .\.venv\Scripts\python.exe -X utf8 scripts/prepare_shopee_corpus.py
  .\.venv\Scripts\python.exe scripts/download_embedding_model.py
  .\.venv\Scripts\python.exe -X utf8 scripts/use_nam_benchmark.py
  .\.venv\Scripts\python.exe -X utf8 bench.py

prepare_shopee_corpus.py dùng bản diễn giải đã rà soát cùng các neo kiểm chứng,
không tự động tạo tóm tắt mới. Nếu nguồn đổi phải rà soát lại trước khi dùng.
Mỗi thành viên giữ nguyên corpus và benchmark_queries.json trong cùng lần so sánh.
Chiến lược Lê Quang Ngọc: Fixed-Size, tối đa 350 ký tự, overlap35, bước315.
Hai baseline: heading350, recursive350. Top-k=3, cùng model embedding.
Agent hiện trả trích đoạn có nguồn, chưa dùng LLM sinh câu trả lời.

Benchmark hiện dùng đúng 5 câu tiếng Anh/filter từ ket_qua_benchmark (nam).txt.
Q1/Q3 lọc buyer; Q2/Q5 lọc seller; Q4 không lọc.
Thêm buyer-return-conditions và seller-return-shipping để có điều khoản cho
câu hỏi của Nam. File Nam cũ có 7 tài liệu: cần chạy lại cùng corpus 9 tài liệu,
model và gold answer trước khi so sánh kết quả giữa các thành viên.
