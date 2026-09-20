"""Import exact queries and filters from Nam; freeze reviewed gold evidence."""
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
raw = (ROOT / 'ket_qua_benchmark (nam).txt').read_bytes()
source = raw.decode('utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig').replace('\r\n', '\n')
pairs = re.findall(r'Query: (.+)\nMetadata filter: (.+)', source)
assert len(pairs) == 5
golds = [
    ('buyer-return-conditions', ['buyer-return-conditions'],
     '15 ngày từ khi đơn cập nhật giao thành công; thực phẩm tươi sống/đông lạnh 24 giờ. Quá hạn chỉ được xem xét hỗ trợ.',
     ['15 ngày', 'giao hàng thành công', '24 giờ', 'Quá hạn']),
    ('seller-return-handling', ['seller-return-handling', 'seller-return-shipping'],
     'Theo dõi thông báo Shopee, đối chiếu hàng hoàn. Khi không đồng ý quyết định hoặc hàng hoàn có vấn đề, phản hồi trong 2 ngày lịch từ thông báo, trừ thời hạn khác; không phản hồi được coi là đồng ý.',
     ['thông báo', '2 ngày lịch', 'thời hạn khác', 'đồng ý']),
    ('buyer-return-conditions', ['buyer-return-conditions', 'buyer-refund-processing'],
     'Duyệt trả hàng chưa đồng nghĩa giải ngân ngay: tùy xác nhận nhận hàng, chấp thuận hoàn không trả hàng, hoặc quyết định hoàn sớm của Shopee. Tiền về tùy phương thức: thẻ 7–14 ngày làm việc, Napas 2–5 ngày làm việc, ví khoảng 24 giờ; COD/chuyển khoản về ngân hàng khoảng 2 ngày làm việc. Tính từ chấp nhận hoàn tiền, có thể phụ thuộc ngân hàng.',
     ['xác nhận nhận hàng', 'không cần trả hàng', '7–14 ngày làm việc', '2–5 ngày làm việc', '24 giờ', '2 ngày làm việc', 'chấp nhận hoàn tiền']),
    ('buyer-return-conditions', ['buyer-return-conditions', 'buyer-received-wrong-item'],
     'Các lý do: chưa nhận/thiếu hàng, giả/nhái, lỗi/hư, sai, khác mô tả, hết hạn, người bán đồng ý; không còn nhu cầu có điều kiện riêng. Bằng chứng tùy trường hợp: ảnh/video rõ tình trạng, mã vận đơn, số lượng, lịch sử trao đổi. Chưa nhận hàng không cần bằng chứng theo hướng dẫn Shopee.',
     ['hàng giả/nhái', 'hết hạn', 'điều kiện riêng', 'mã vận đơn', 'ảnh', 'không cần']),
    ('seller-return-shipping', ['seller-return-shipping'],
     'Phí phụ thuộc lỗi, loại yêu cầu và hình thức gửi: người bán chịu theo mục 7.1 nhưng có miễn trừ; người mua không trả phí lấy tại nhà/bưu cục, tự sắp xếp ứng phí rồi được hoàn/hỗ trợ theo điều kiện Mall/ngoài Mall. Người bán đối chiếu kiện và phản hồi vấn đề trong 2 ngày lịch từ thông báo, trừ thời hạn khác.',
     ['Người bán chịu phí', 'Miễn phí người bán', 'người mua không trả phí', 'người mua ứng phí', 'Shopee Xu', 'đối chiếu hàng hoàn', '2 ngày lịch', 'thời hạn khác']),
]
queries = []
for i, ((question, filter_text), (doc, docs, answer, evidence)) in enumerate(zip(pairs, golds), 1):
    queries.append(dict(id=f'Q{i}', question=question,
        filter=None if filter_text == 'none' else ast.literal_eval(filter_text),
        gold_doc=doc, gold_docs=docs, gold_answer=answer, evidence=evidence))
spec = dict(name='Shopee — benchmark Nam v2', source_file='ket_qua_benchmark (nam).txt',
    corpus='data/shopee-return-refund', personal_strategy='fixed', chunk_size=350, overlap=35, top_k=3,
    queries=queries)
(ROOT / 'benchmark_queries.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Imported 5 exact Nam queries and filters')
