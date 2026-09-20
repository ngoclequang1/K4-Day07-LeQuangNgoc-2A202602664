# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách trả hàng và hoàn tiền trên Shopee.

**Tại sao nhóm chọn chủ đề này?**
> *Viết 2-3 câu:*

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| | | | |
| | | | |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Tài liệu chứa bằng chứng |
|---|---|---|---|
| Q1 | How long does a buyer have to request a return or refund? | 15 ngày từ khi đơn cập nhật giao thành công; thực phẩm tươi sống/đông lạnh 24 giờ. Quá hạn chỉ được xem xét hỗ trợ. | buyer-return-conditions |
| Q2 | What must a seller do after a buyer opens a return request? | Theo dõi thông báo Shopee, đối chiếu hàng hoàn. Khi không đồng ý quyết định hoặc hàng hoàn có vấn đề, phản hồi trong 2 ngày lịch từ thông báo, trừ thời hạn khác; không phản hồi được coi là đồng ý. | seller-return-handling, seller-return-shipping |
| Q3 | When is the buyer's refund released after a return is approved? | Duyệt trả hàng chưa đồng nghĩa giải ngân ngay: tùy xác nhận nhận hàng, chấp thuận hoàn không trả hàng, hoặc quyết định hoàn sớm của Shopee. Tiền về tùy phương thức: thẻ 7–14 ngày làm việc, Napas 2–5 ngày làm việc, ví khoảng 24 giờ; COD/chuyển khoản về ngân hàng khoảng 2 ngày làm việc. Tính từ chấp nhận hoàn tiền, có thể phụ thuộc ngân hàng. | buyer-return-conditions, buyer-refund-processing |
| Q4 | Which reasons and evidence can support a return or refund claim? | Các lý do: chưa nhận/thiếu hàng, giả/nhái, lỗi/hư, sai, khác mô tả, hết hạn, người bán đồng ý; không còn nhu cầu có điều kiện riêng. Bằng chứng tùy trường hợp: ảnh/video rõ tình trạng, mã vận đơn, số lượng, lịch sử trao đổi. Chưa nhận hàng không cần bằng chứng theo hướng dẫn Shopee. | buyer-return-conditions, buyer-received-wrong-item |
| Q5 | Who pays return shipping and what should the seller do with the parcel? | Phí phụ thuộc lỗi, loại yêu cầu và hình thức gửi: người bán chịu theo mục 7.1 nhưng có miễn trừ; người mua không trả phí lấy tại nhà/bưu cục, tự sắp xếp ứng phí rồi được hoàn/hỗ trợ theo điều kiện Mall/ngoài Mall. Người bán đối chiếu kiện và phản hồi vấn đề trong 2 ngày lịch từ thông báo, trừ thời hạn khác. | seller-return-shipping |

Dùng [benchmark_queries.json](../benchmark_queries.json) theo câu hỏi/filter của Nam: Q1/Q3 buyer, Q2/Q5 seller, Q4 không lọc. Gold đối chiếu từ corpus cập nhật; file Nam không có gold. Xem mục 5 [báo cáo cá nhân](REPORT_CANHAN.md) để đối chiếu chunk và kết quả mới.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |

## Phụ lục dữ liệu đã chuẩn bị trên máy Lê Quang Ngọc

Corpus mới có 9 bản tóm lược từ 6 nguồn. Lê Quang Ngọc: Fixed-Size 350 ký tự, overlap35, top-k3, multilingual MiniLM; theo nguyên lý trong data/chunking_experiment_report.md (file không ấn định tham số). Heading và recursive là baseline trên cùng máy, chưa thay cho kết quả thành viên khác. Nam cần chạy lại corpus/model/gold chung vì file cũ có 7 tài liệu và không ghi model/hash. Kết quả và phân tích filter Q2 xem [REPORT_CANHAN mục 5](REPORT_CANHAN.md).

| Tài liệu baseline | Chiến lược | Số chunk | Ký tự TB |
|---|---|---:|---:|
| buyer-received-wrong-item | fixed_size | 3 | 254.67 |
| buyer-received-wrong-item | by_sentences | 4 | 172.00 |
| buyer-received-wrong-item | recursive | 3 | 231.33 |
| buyer-refund-processing | fixed_size | 3 | 275.67 |
| buyer-refund-processing | by_sentences | 3 | 251.33 |
| buyer-refund-processing | recursive | 4 | 189.25 |
| buyer-return-conditions | fixed_size | 4 | 272.75 |
| buyer-return-conditions | by_sentences | 4 | 245.00 |
| buyer-return-conditions | recursive | 4 | 246.50 |
