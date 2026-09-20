from src.custom_chunking import HeadingChunker
from src.agent import KnowledgeBaseAgent
from src.store import EmbeddingStore
from src.models import Document
from bench import load_documents
import ast
import json
import re
from pathlib import Path


def test_heading_preserves_parent_and_budget():
    chunks = HeadingChunker(70).chunk('# Chính sách\n## Người bán\n' + 'phản hồi trong 2 ngày. ' * 15)
    assert len(chunks) > 1
    assert all(c.startswith('# Chính sách\n## Người bán\n') for c in chunks)
    assert all(len(c) <= 70 for c in chunks)
    assert 'phản hồi' in ''.join(chunks)


def test_filtered_results_are_exact_agent_context():
    store = EmbeddingStore(embedding_fn=lambda _: [1.0])
    store.add_documents([Document('buyer', 'BUYER_ONLY', {'audience': 'buyer'}),
                         Document('seller', 'SELLER_ONLY', {'audience': 'seller'})])
    agent = KnowledgeBaseAgent(store, lambda prompt: prompt)
    result = agent.answer_from_results('deadline?', store.search_with_filter(
        'deadline?', metadata_filter={'audience': 'seller'}))
    assert 'SELLER_ONLY' in result
    assert 'BUYER_ONLY' not in result


def test_corpus_metadata_excluded_from_content():
    docs = load_documents()
    assert len(docs) == 9
    assert len({d.id for d in docs}) == 9
    assert all('source_sha256:' not in d.content for d in docs)
    assert all(d.metadata['source_url'].startswith('https://') for d in docs)


def test_queries_and_filters_match_nam_exactly():
    root = Path(__file__).resolve().parents[1]
    raw = (root / 'ket_qua_benchmark (nam).txt').read_bytes()
    text = raw.decode('utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig')
    pairs = re.findall(r'Query: (.+)\r?\nMetadata filter: ([^\r\n]+)', text)
    queries = json.loads((root / 'benchmark_queries.json').read_text(encoding='utf-8'))['queries']
    assert len(pairs) == len(queries) == 5
    for (question, filter_text), query in zip(pairs, queries):
        assert query['question'] == question.rstrip('\r')
        assert query['filter'] == (None if filter_text == 'none' else ast.literal_eval(filter_text))


def test_gold_evidence_exists_in_eligible_documents():
    root = Path(__file__).resolve().parents[1]
    queries = json.loads((root / 'benchmark_queries.json').read_text(encoding='utf-8'))['queries']
    docs = load_documents()
    for query in queries:
        context = '\n'.join(d.content for d in docs if d.id in query['gold_docs']
                            and all(d.metadata.get(k) == v for k, v in (query['filter'] or {}).items()))
        assert all(token.casefold() in context.casefold() for token in query['evidence']), query['id']
