"""Reproduce the individual exercises without a team corpus or API key.

Run from the repository root: python personal_experiments.py
Predictions are read from a separate file written before the first experiment.
The sample-document comparison is preparation, not the team's benchmark.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from src import ChunkingStrategyComparator, FixedSizeChunker, MockEmbedder, compute_similarity


ROOT = Path(__file__).resolve().parent
REPORT_DIR = ROOT / "report"
SAMPLE_DOCUMENTS = (
    "data/vector_store_notes.md",
    "data/rag_system_design.md",
    "data/vi_retrieval_notes.md",
)


def run_experiments() -> dict:
    predictions = json.loads((REPORT_DIR / "similarity_predictions.json").read_text(encoding="utf-8"))
    embedder = MockEmbedder(dim=64)
    pairs = []
    for pair in predictions["pairs"]:
        score = compute_similarity(embedder(pair["sentence_a"]), embedder(pair["sentence_b"]))
        observed = "cao" if score >= predictions["high_threshold"] else "thấp"
        pairs.append({**pair, "score": score, "observed": observed, "matches_prediction": observed == pair["prediction"]})

    chunking_math = []
    for overlap in (50, 100):
        expected = math.ceil((10000 - overlap) / (500 - overlap))
        actual = len(FixedSizeChunker(chunk_size=500, overlap=overlap).chunk("a" * 10000))
        chunking_math.append({"length": 10000, "chunk_size": 500, "overlap": overlap, "formula_count": expected, "actual_count": actual})

    baseline = []
    comparator = ChunkingStrategyComparator()
    for relative_path in SAMPLE_DOCUMENTS:
        content = (ROOT / relative_path).read_text(encoding="utf-8")
        stats = comparator.compare(content, chunk_size=200)
        baseline.append({
            "document": relative_path,
            "character_count": len(content),
            "strategies": {
                name: {"count": values["count"], "avg_length": values["avg_length"], "chunks": values["chunks"]}
                for name, values in stats.items()
            },
        })

    return {
        "backend": embedder._backend_name,
        "embedding_dimensions": embedder.dim,
        "limitation": "Mock embeddings are deterministic hash-based vectors, not semantic representations. These results are not a team retrieval benchmark.",
        "comparison_rule": predictions["comparison_rule"],
        "predicted_highest_pair": predictions["predicted_highest_pair"],
        "predicted_lowest_pair": predictions["predicted_lowest_pair"],
        "actual_highest_pair": max(pairs, key=lambda item: item["score"])["id"],
        "actual_lowest_pair": min(pairs, key=lambda item: item["score"])["id"],
        "similarity_pairs": pairs,
        "chunking_math": chunking_math,
        "sample_baseline": baseline,
    }


def main() -> None:
    results = run_experiments()
    json_path = REPORT_DIR / "ket_qua_thi_nghiem_canhan.json"
    text_path = REPORT_DIR / "ket_qua_thi_nghiem_canhan.txt"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "THÍ NGHIỆM CÁ NHÂN TRƯỚC KHI LẬP NHÓM",
        f"Backend: {results['backend']} (64 chiều)",
        "Mock không biểu diễn ngữ nghĩa. Đây không phải benchmark chính thức của nhóm.",
        results["comparison_rule"],
        "",
        "BÀI TOÁN CHUNKING",
    ]
    for item in results["chunking_math"]:
        lines.append(f"overlap={item['overlap']}: công thức={item['formula_count']}, chạy code={item['actual_count']}")
    lines.extend(["", "5 CẶP CÂU (dự đoán lưu trước trong similarity_predictions.json)"])
    for item in results["similarity_pairs"]:
        lines.extend([
            f"Cặp {item['id']}: dự đoán={item['prediction']}, cosine={item['score']:.6f}, khớp quy ước={item['matches_prediction']}",
            f"  A: {item['sentence_a']}",
            f"  B: {item['sentence_b']}",
        ])
    lines.append(f"Cặp cao nhất: {results['actual_highest_pair']}; thấp nhất: {results['actual_lowest_pair']}")
    lines.extend(["", "BASELINE THỬ TRÊN TÀI LIỆU KỸ THUẬT MẪU (chunk_size=200)"])
    for item in results["sample_baseline"]:
        lines.append(f"{item['document']} ({item['character_count']} ký tự)")
        for name, stats in item["strategies"].items():
            lines.append(f"  {name}: count={stats['count']}, avg_length={stats['avg_length']:.2f}")
    text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved: {json_path.relative_to(ROOT)}")
    print(f"Saved: {text_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
