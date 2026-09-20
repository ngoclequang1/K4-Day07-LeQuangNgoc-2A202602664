"""Render reports from the current Nam benchmark; never reuse old results."""
import hashlib
import json
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bench import load_documents
from src.chunking import ChunkingStrategyComparator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--update-group', action='store_true', help='Regenerate the old group draft explicitly')
    args = parser.parse_args()
    spec_path = ROOT / 'benchmark_queries.json'
    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    result = json.loads((ROOT / 'report/benchmark_results.json').read_text(encoding='utf-8'))
    assert result['spec_sha256'] == hashlib.sha256(spec_path.read_bytes()).hexdigest(), 'Rerun bench.py first'
    docs = load_documents()
    assert [d.metadata for d in docs] == result['corpus'], 'Corpus changed; rerun benchmark'
    assert spec['personal_strategy'] == result['personal_strategy'] == 'fixed'
    rows = [r for r in result['strategies']['fixed']['rows'] if r['filtered']]
    count = sum(r['evidence_present'] for r in rows)
    personal_path = ROOT / 'report/REPORT_CANHAN.md'
    personal = personal_path.read_text(encoding='utf-8').split('## 5. Kết quả truy xuất')[0]
    section = '''## 5. Kết quả truy xuất của tôi — benchmark của Nam

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
.\\.venv\\Scripts\\python.exe -X utf8 scripts/prepare_shopee_corpus.py
.\\.venv\\Scripts\\python.exe -X utf8 scripts/use_nam_benchmark.py
.\\.venv\\Scripts\\python.exe -X utf8 bench.py
.\\.venv\\Scripts\\python.exe -X utf8 scripts/update_shopee_reports.py
.\\.venv\\Scripts\\python.exe -m pytest tests/ -v
```

Lần đầu cần `requirements-local.txt` và chạy `scripts/download_embedding_model.py`. Prepare dùng bản crawl đã lưu; khi trang thay đổi cần rà soát lại bản tóm lược. Log mới: [ket_qua_benchmark.txt](../ket_qua_benchmark.txt), [benchmark_results.json](benchmark_results.json). Hash spec và corpus được lưu để tránh trộn kết quả khác phiên bản.

### Câu hỏi, gold answer và kết quả fixed-size

Gold answer là đáp án được đối chiếu từ corpus hiện tại, **không phải đáp án chuẩn do Nam cung cấp** vì file của Nam không có gold. Q3/Q4 tổng hợp nhiều tài liệu, nên công cụ hỗ trợ `gold_docs` thay vì chỉ một doc_id.

| Câu | Câu hỏi nguyên văn | Filter | Đáp án chuẩn |
|---|---|---|---|
'''
    for q in spec['queries']:
        section += f"| {q['id']} | {q['question']} | {q['filter'] or 'Không'} | {q['gold_answer']} |\n"
    section += '\n| Câu | Top-1 | Cosine | Hạng đủ toàn bộ bằng chứng | Các chuỗi bằng chứng còn thiếu trong top-3 |\n|---|---|---:|---|---|\n'
    for row in rows:
        top = row['results'][0]
        section += f"| {row['query']['id']} | `{top['id']}` | {top['score']:.6f} | {row['evidence_rank'] or 'Chưa đủ'} | {', '.join(row['missing_evidence']) or 'Không'} |\n"
    section += f'\n**{count}/5 câu đủ toàn bộ chuỗi bằng chứng trong top-3** theo cấu hình filter của Nam. Đây là kiểm tra đủ ý, không đồng nghĩa chỉ {count} câu có đoạn liên quan. Các câu còn lại có thể có bằng chứng một phần.\n'
    section += '''
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
'''
    for name, info in result['strategies'].items():
        yes, no = ([r for r in info['rows'] if r['filtered']], [r for r in info['rows'] if not r['filtered']])
        section += f"| {name} | {info['count']} | {info['avg_length']:.2f} | {sum(r['evidence_present'] for r in yes)}/5 | {sum(r['retrieval_score_proxy'] for r in yes)} | {sum(r['retrieval_score_proxy'] for r in no)} |\n"
    section += '''
Không so các score này với bộ 5 câu tiếng Việt cũ. Câu hỏi tiếng Anh trên corpus tiếng Việt và câu hỏi nhiều vế làm thay đổi độ khó; chưa có thí nghiệm đối chứng riêng để định lượng ảnh hưởng của ngôn ngữ.

### Có và không có metadata filter — Q2

| Chiến lược | Top-3 bỏ filter | Top-3 theo Nam (seller) | Đủ bằng chứng trước → sau |
|---|---|---|---|
'''
    for name, info in result['strategies'].items():
        pair = [r for r in info['rows'] if r['query']['id'] == 'Q2']
        cells = ['; '.join(f"`{x['id']}` ({x['score']:.4f})" for x in r['results']) for r in pair]
        section += f"| {name} | {cells[0]} | {cells[1]} | {pair[0]['evidence_present']} → {pair[1]['evidence_present']} |\n"
    section += '''
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
'''
    personal_path.write_text(personal + section, encoding='utf-8')

    # The completed group synthesis includes other members; preserve it by default.
    if not args.update_group:
        return

    group_path = ROOT / 'report/REPORT_NHOM.md'
    group = group_path.read_text(encoding='utf-8')
    start = group.index('| # | Câu hỏi (Query)')
    end = group.index('### Tổng hợp chất lượng', start)
    table = '| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Tài liệu chứa bằng chứng |\n|---|---|---|---|\n'
    for q in spec['queries']:
        table += f"| {q['id']} | {q['question']} | {q['gold_answer']} | {', '.join(q['gold_docs'])} |\n"
    table += '\nDùng [benchmark_queries.json](../benchmark_queries.json) theo câu hỏi/filter của Nam: Q1/Q3 buyer, Q2/Q5 seller, Q4 không lọc. Gold đối chiếu từ corpus cập nhật; file Nam không có gold. Xem mục 5 [báo cáo cá nhân](REPORT_CANHAN.md) để đối chiếu chunk và kết quả mới.\n\n'
    group = group[:start] + table + group[end:]
    marker = '\n## Phụ lục dữ liệu đã chuẩn bị trên máy Lê Quang Ngọc\n'
    group = group.split(marker)[0] + marker
    group += '\nCorpus mới có 9 bản tóm lược từ 6 nguồn. Lê Quang Ngọc: Fixed-Size 350 ký tự, overlap35, top-k3, multilingual MiniLM; theo nguyên lý trong data/chunking_experiment_report.md (file không ấn định tham số). Heading và recursive là baseline trên cùng máy, chưa thay cho kết quả thành viên khác. Nam cần chạy lại corpus/model/gold chung vì file cũ có 7 tài liệu và không ghi model/hash. Kết quả và phân tích filter Q2 xem [REPORT_CANHAN mục 5](REPORT_CANHAN.md).\n\n'
    group += '| Tài liệu baseline | Chiến lược | Số chunk | Ký tự TB |\n|---|---|---:|---:|\n'
    baseline = {}
    for doc in docs[:3]:
        baseline[doc.id] = ChunkingStrategyComparator().compare(doc.content, chunk_size=350)
        for name, stats in baseline[doc.id].items():
            group += f"| {doc.id} | {name} | {stats['count']} | {stats['avg_length']:.2f} |\n"
    group_path.write_text(group, encoding='utf-8')
    (ROOT / 'report/shopee_baseline.json').write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
