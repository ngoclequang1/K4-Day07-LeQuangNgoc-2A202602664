"""Build the reviewed lab corpus from a successful crawl and bounded summaries.

The bodies below are concise paraphrases checked against the downloaded pages,
not verbatim copies or a complete statement of Shopee policies. Source section
headings are retained where possible. Run crawl_shopee.py first.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "shopee-return-refund"
DOCUMENTS = [
    {
        "doc_id": "buyer-return-conditions", "source_id": "return-policy",
        "title": "Điều kiện, thời hạn yêu cầu và điều kiện hoàn tiền", "audience": "buyer", "category": "returns-policy",
        "source_section": "Mục 3.1, 3.2 và 9.1–9.3", "document_version": "effective-2026-03-11",
        "checks": ["15 (mười lăm)", "24 giờ", "9.1.", "9.3."],
        "content": """# 3. Điều kiện yêu cầu trả hàng/hoàn tiền

Thời hạn gửi yêu cầu là 15 ngày từ khi đơn cập nhật giao hàng thành công; thực phẩm tươi sống hoặc đông lạnh: 24 giờ. Quá hạn, Shopee có thể xem xét hỗ trợ, không mặc nhiên chấp thuận.

Lý do gồm chưa nhận hoặc thiếu hàng, hàng giả/nhái, lỗi/hư hỏng, giao sai, khác rõ mô tả, hết hạn; hoặc người bán đồng ý (Shopee xác nhận lại). Trả vì không còn nhu cầu có điều kiện riêng tại mục 4, không áp dụng mọi người mua/sản phẩm.

# 9. Hoàn tiền đối với sản phẩm hoàn trả

Không phải cứ duyệt trả hàng là giải ngân ngay. Các trường hợp gồm người bán xác nhận nhận hàng hoàn; chấp nhận đề xuất không cần trả hàng; Shopee quyết định hoàn ngay; hoặc đơn đủ điều kiện và Shopee quyết định hoàn khi đơn vị vận chuyển xác nhận nhận hàng hoàn.

Một số người mua không có lịch sử vi phạm có thể được hoàn sớm theo quyết định Shopee. Shopee tự động hoàn nếu người bán không phản hồi trong thời hạn quy định. Thời gian tiền về phụ thuộc phương thức thanh toán.
""",
    },
    {
        "doc_id": "seller-return-shipping", "source_id": "return-policy",
        "title": "Phí vận chuyển hoàn trả và xử lý kiện hàng", "audience": "seller", "category": "shipping-policy",
        "source_section": "Mục 5, 7 và 8", "document_version": "effective-2026-03-11",
        "checks": ["7.1.", "7.2.", "8.1.", "8.2.", "02 ngày lịch"],
        "content": """# 7. Chi phí vận chuyển hoàn trả của người bán

Người bán chịu phí chiều hoàn cho yêu cầu được duyệt không do lỗi người mua/đơn vị vận chuyển, đơn giao thất bại và ngoại lệ Shopee quy định, có các miễn trừ tại mục 7.2.

Miễn phí người bán: trả một phần đơn; chưa nhận hàng được duyệt; lỗi vận chuyển; hoàn không cần trả hàng; giao thất bại qua kênh tự vận chuyển; người mua tự sắp xếp gửi trả.

# 8. Chi phí hoàn trả của người mua

Lấy tại nhà/gửi bưu cục: người mua không trả phí. Tự sắp xếp: người mua ứng phí; hàng Mall được hoàn phí, ngoài Mall có thể được hỗ trợ một phần bằng Shopee Xu khi đủ điều kiện. Không có một bên trả phí cố định cho mọi trường hợp.

# 5. Quyền của người bán

Khi nhận kiện, đối chiếu hàng hoàn. Nếu chưa nhận, hàng không phù hợp hoặc hư/mất, hay không đồng ý hoàn tiền, phản hồi Shopee trong 2 ngày lịch từ thông báo, trừ thời hạn khác Shopee quy định. Không phản hồi đúng hạn được xem là đồng ý.
""",
    },
    {
        "doc_id": "buyer-return-request", "source_id": "buyer-request",
        "title": "Người mua tạo yêu cầu trả hàng và hoàn tiền", "audience": "buyer", "category": "returns-policy",
        "source_section": "Hướng dẫn gửi yêu cầu; lưu ý xử lý", "document_version": "not-stated",
        "checks": ["3 - 5 ngày", "Email", "Chờ giao hàng"],
        "content": """# 1. Hướng dẫn gửi yêu cầu Trả hàng/Hoàn tiền

Trong ứng dụng, người mua vào mục Tôi, mở thẻ Chờ giao hàng hoặc Đã giao, chọn đơn và bấm Trả hàng/Hoàn tiền. Tiếp đó chọn tình huống, sản phẩm và lý do; với thiếu hàng, chọn phương án xử lý phù hợp.

Biểu mẫu cần mô tả sự cố, ảnh hoặc video chứng minh và email liên hệ. Kiểm tra thông tin rồi gửi. Cũng có thể tạo yêu cầu qua mục trò chuyện với Shopee.

# 2. Lưu ý

Thời gian xử lý thường khoảng 3–5 ngày làm việc. Kết quả được gửi qua thông báo cập nhật đơn hàng hoặc email. Nếu cần trả sản phẩm, chọn bưu tá đến lấy hoặc gửi tại bưu cục; bên bán hoặc Shopee sẽ kiểm tra hàng nhận lại.
""",
    },
    {
        "doc_id": "buyer-refund-processing", "source_id": "refund-blog",
        "title": "Người mua nhận và kiểm tra tiền hoàn", "audience": "buyer", "category": "refund-policy",
        "source_section": "Cách nhận tiền hoàn; theo dõi tình trạng", "document_version": "published-2026-09-15",
        "checks": ["15/09/2026", "7 – 14 ngày", "2 – 5 ngày"],
        "content": """# Cách nhận tiền hoàn trả hàng trên Shopee

Thời gian dưới đây tính từ khi Shopee chấp nhận hoàn tiền và có thể phụ thuộc ngân hàng:

- Thanh toán bằng thẻ tín dụng hoặc thẻ ghi nợ: tiền quay về thẻ trong 7–14 ngày làm việc. Apple Pay và Google Pay cũng hoàn về thẻ liên kết trong khoảng này.
- Thẻ Napas: khoảng 2–5 ngày làm việc.
- Ví ShopeePay: khoảng 24 giờ nếu ví hoạt động bình thường.
- COD hoặc chuyển khoản: hoàn về ngân hàng khoảng 2 ngày làm việc; nếu nhận qua ShopeePay, khoảng 24 giờ khi ví hoạt động bình thường.
- SPayLater: khoảng 24 giờ, kiểm tra phần giao dịch.

# Cách theo dõi tình trạng Trả hàng/Hoàn tiền

Mở chi tiết yêu cầu trong đơn hàng để xem tiến độ. Cũng có thể kiểm tra thông báo cập nhật đơn, email hoặc trò chuyện với Shopee.
""",
    },
    {
        "doc_id": "buyer-warranty-claim", "source_id": "regulations",
        "title": "Điều kiện bảo hành dành cho người mua", "audience": "buyer", "category": "warranty-policy",
        "source_section": "III.4: điều kiện và quyền của người mua", "document_version": "updated-2025-01-03",
        "checks": ["03/01/2025", "Còn tem/phiếu bảo hành", "liên hệ trực tiếp"],
        "content": """# 4. Chính sách bảo hành

Người mua cần đối chiếu chính sách riêng của sản phẩm với người bán hoặc nhà sản xuất. Các điều kiện cơ bản gồm: còn hạn, giữ tem hoặc phiếu bảo hành và lỗi kỹ thuật không do người sử dụng gây ra.

Khi đủ điều kiện, liên hệ trung tâm bảo hành; nếu không thể đến trực tiếp, hỏi người bán hoặc nhà sản xuất để nhận hướng dẫn. Người mua được khiếu nại nếu bị từ chối trái với cam kết đã công bố.
""",
    },
    {
        "doc_id": "buyer-received-wrong-item", "source_id": "buyer-evidence",
        "title": "Bằng chứng của người mua khi nhận sai hoặc thiếu hàng", "audience": "buyer", "category": "returns-policy",
        "source_section": "Mục 2 và 4: hàng có vấn đề và quy định bằng chứng", "document_version": "not-stated",
        "checks": ["5MB", "100 MB", "24 giờ"],
        "content": """# 2. Đã nhận được hàng nhưng hàng có vấn đề

Nếu chưa nhận hàng, người mua không cần cung cấp bằng chứng; Shopee đối chiếu hệ thống theo dõi đơn.

Với hàng sai mẫu, thiếu hoặc hỏng, nên quay liên tục lúc mở gói: hình ảnh rõ, thấy kiện hàng, mã vận đơn, số lượng và tình trạng sản phẩm. Khi gửi trả, nên ghi lại quá trình đóng gói để đối chiếu sau này.

# 4. Quy định về bằng chứng

Mỗi ảnh tối đa 5 MB; mỗi video tối đa 100 MB và dài không quá 1 phút. Nội dung cần rõ lỗi; có thể bổ sung lịch sử trao đổi. Tệp lớn có thể được gửi qua liên kết công khai theo hướng dẫn của Shopee.

Nếu được yêu cầu bổ sung bằng chứng, người mua có 24 giờ. Quá thời hạn, Shopee đánh giá dựa vào tài liệu đã nhận.
""",
    },
    {
        "doc_id": "seller-return-handling", "source_id": "return-policy",
        "title": "Người bán phản hồi quyết định trả hàng và hoàn tiền", "audience": "seller", "category": "returns-policy",
        "source_section": "Mục 5: quyền của người bán", "document_version": "effective-2026-03-11",
        "checks": ["11/3/2026", "02 ngày lịch", "không có khiếu nại"],
        "content": """# 5. Quyền của người bán

Shopee thông báo yêu cầu hoặc quyết định trả hàng/hoàn tiền cho người bán qua ứng dụng, email hoặc tin nhắn.

Nếu không đồng ý quyết định hoàn tiền, chưa nhận hàng trả về hoặc hàng hoàn có vấn đề, người bán cần phản hồi trong 2 ngày lịch kể từ lúc nhận thông báo; áp dụng thời hạn khác nếu Shopee quy định riêng tại thời điểm xử lý.

Nếu không phản hồi đúng hạn, Shopee xem người bán đã đồng ý và không khiếu nại quyết định. Trong một số trường hợp, Shopee có thể hoàn tiền mà không yêu cầu người mua gửi trả hàng.
""",
    },
    {
        "doc_id": "seller-refund-dispute", "source_id": "disputes",
        "title": "Trách nhiệm người bán khi giải quyết tranh chấp", "audience": "seller", "category": "refund-policy",
        "source_section": "Mục 1: trách nhiệm cung cấp thông tin và phân loại tranh chấp", "document_version": "published-2024-03-15",
        "checks": ["15/3/2024", "07 ngày làm việc", "không phải là khiếu nại"],
        "content": """# 1. Quy định chung về giải quyết tranh chấp

Người bán cần phối hợp thương lượng và cung cấp hồ sơ sản phẩm đầy đủ, chính xác, trung thực. Nếu vụ việc vượt thẩm quyền của Shopee, các bên được hướng dẫn giải quyết tại cơ quan có thẩm quyền.

Khiếu nại trả hàng/hoàn tiền được xử lý theo chính sách riêng về trả hàng/hoàn tiền. Mốc 7 ngày làm việc kể từ khi nhận đủ hồ sơ trong quy trình này dành cho tranh chấp khác; vụ việc phức tạp có thể kéo dài. Không áp dụng mốc đó như thời hạn chung cho mọi yêu cầu hoàn tiền.
""",
    },
    {
        "doc_id": "seller-warranty-obligations", "source_id": "regulations",
        "title": "Nghĩa vụ bảo hành của người bán", "audience": "seller", "category": "warranty-policy",
        "source_section": "III.4: nghĩa vụ của người bán và vai trò Shopee", "document_version": "updated-2025-01-03",
        "checks": ["03/01/2025", "phần mô tả", "trừ trường hợp"],
        "content": """# 4. Chính sách bảo hành

Người bán phải công bố chính sách bảo hành tại phần mô tả sản phẩm và tiếp nhận bảo hành đúng cam kết của mình hoặc nhà sản xuất.

Shopee hỗ trợ trong phạm vi có thể, nhưng không trực tiếp thực hiện bảo hành cho hàng do bên bán khác cung cấp. Ngoại lệ là sản phẩm do Shopee tự đăng bán: áp dụng chính sách bảo hành được công bố cho sản phẩm đó.
""",
    },
]


def normalized(text):
    return unicodedata.normalize("NFC", text).replace("\u00a0", " ")


def main():
    logs = json.loads((ROOT / "report/shopee_crawl_log.json").read_text(encoding="utf-8"))
    sources = {row["source_id"]: row for row in logs}
    prepared = []
    for doc in DOCUMENTS:
        event = sources[doc["source_id"]]
        if event["status"] != "fetched" or not event["robots_allowed"]:
            raise ValueError(f"No successful permitted crawl for {doc['doc_id']}")
        raw = (ROOT / event["raw_cache"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != event["raw_sha256"]:
            raise ValueError("Raw cache checksum mismatch")
        source_text = normalized((ROOT / ".cache/shopee" / f"{doc['source_id']}.txt").read_text(encoding="utf-8"))
        for phrase in doc["checks"]:
            if normalized(phrase) not in source_text:
                raise ValueError(f"Source changed: {doc['doc_id']} missing {phrase!r}; review before updating corpus")
        metadata = {key: doc[key] for key in ("doc_id", "title", "audience", "category", "source_section", "document_version")}
        metadata.update({"language": "vi", "source_url": event["final_url"], "retrieved_at": event["checked_at"][:10],
                         "collection_method": "http-crawl-reviewed-summary", "content_type": "reviewed-summary",
                         "source_sha256": event["raw_sha256"], "license_or_permission": "public-source"})
        body = doc["content"].strip() + "\n"
        frontmatter = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items())
        prepared.append((doc, metadata, f"---\n{frontmatter}\n---\n\n{body}"))

    # Validate all source anchors before replacing any corpus file.
    backup = ROOT / ".cache/shopee/original-corpus"
    backup.mkdir(parents=True, exist_ok=True)
    DEST.mkdir(parents=True, exist_ok=True)
    for path in DEST.glob("*"):
        if path.is_file() and not (backup / path.name).exists():
            shutil.copy2(path, backup / path.name)
    fields = ["doc_id", "file_path", "title", "source_url", "retrieved_at", "document_version", "license_or_permission"]
    rows, audit = [], []
    for doc, metadata, text in prepared:
        path = DEST / f"{doc['doc_id']}.md"
        path.write_text(text, encoding="utf-8")
        row = {key: metadata.get(key, "") for key in fields}
        row["file_path"] = path.relative_to(ROOT).as_posix()
        rows.append(row)
        audit.append({**metadata, "file_path": row["file_path"], "body_characters": len(doc["content"].strip()),
                      "document_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()})
    with (DEST / "sources.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    # The workspace also contains a top-level inventory: update matching IDs.
    master = ROOT / "data/sources.csv"
    existing = []
    if master.exists():
        with master.open(encoding="utf-8", newline="") as file:
            existing = list(csv.DictReader(file))
    ids = {row["doc_id"] for row in rows}
    with master.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows([row for row in existing if row["doc_id"] not in ids] + rows)
    (ROOT / "report/shopee_corpus_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(rows)} reviewed summaries from {len({row['source_url'] for row in rows})} official sources.")


if __name__ == "__main__":
    main()
