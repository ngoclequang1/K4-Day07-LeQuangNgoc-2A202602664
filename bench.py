"""Shared Shopee benchmark. No API key, no gold answers passed to the agent."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from src.chunking import FixedSizeChunker, RecursiveChunker
from src.custom_chunking import HeadingChunker
from src.embeddings import LocalEmbedder, MockEmbedder, LOCAL_EMBEDDING_MODEL
from src.models import Document
from src.store import EmbeddingStore
from src.agent import KnowledgeBaseAgent

ROOT = Path(__file__).resolve().parent


def load_documents():
    documents = []
    for path in sorted((ROOT / 'data/shopee-return-refund').glob('*.md')):
        raw = path.read_text(encoding='utf-8')
        _, front, body = raw.split('---', 2)
        metadata = {k.strip(): json.loads(v.strip()) for line in front.strip().splitlines()
                    for k, v in [line.split(':', 1)]}
        assert metadata['doc_id'] == path.stem
        assert metadata['audience'] in ('buyer', 'seller', 'both')
        for key in ('source_url', 'retrieved_at', 'document_version', 'category'):
            assert metadata[key]
        metadata['corpus_sha256'] = hashlib.sha256(raw.encode()).hexdigest()
        documents.append(Document(path.stem, body.strip(), metadata))
    return documents


def extractive_backend(prompt):
    """Return context excerpts with citations; this is NOT a generative LLM."""
    context = prompt.split('Context:\n', 1)[1].split('\n\nQuestion:', 1)[0]
    blocks = re.split(r'(?=\[\d+\] Source:)', context)
    return '\n\n'.join('[' + block.split(']', 1)[0][1:] + '] ' + block.split('\n', 1)[1].strip()
                         for block in blocks if block.strip())


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--embedding', choices=['local', 'mock'], default='local')
    args = parser.parse_args()
    spec = json.loads((ROOT / 'benchmark_queries.json').read_text(encoding='utf-8'))
    docs = load_documents()
    size = spec['chunk_size']
    overlap = spec.get('overlap', size // 10)
    personal_strategy = spec['personal_strategy']
    strategies = {'fixed': FixedSizeChunker(size, overlap),
                  'recursive': RecursiveChunker(chunk_size=size), 'heading': HeadingChunker(size)}
    chunks = {name: [Document(f'{doc.id}::{i:02}', part, doc.metadata)
                     for doc in docs for i, part in enumerate(chunker.chunk(doc.content), 1)]
              for name, chunker in strategies.items()}
    texts = sorted({d.content for group in chunks.values() for d in group}
                   | {q['question'] for q in spec['queries']})
    backend = LOCAL_EMBEDDING_MODEL if args.embedding == 'local' else 'mock-nonsemantic'
    cache_key = hashlib.sha256(json.dumps([backend, texts], ensure_ascii=False).encode()).hexdigest()
    cache = ROOT / '.cache' / f'benchmark-vectors-{cache_key}.json'
    if cache.exists():
        vectors = json.loads(cache.read_text(encoding='utf-8'))
    else:
        if args.embedding == 'local':
            from huggingface_hub import snapshot_download
            model_path = snapshot_download(LOCAL_EMBEDDING_MODEL, local_files_only=True,
                                           allow_patterns=['*.json', '*.safetensors', '*.txt', '*.model'],
                                           ignore_patterns=['onnx/*', 'openvino/*'])
            embedder = LocalEmbedder(model_path)
        else:
            embedder = MockEmbedder()
        values = (embedder.model.encode(texts, normalize_embeddings=True, show_progress_bar=True).tolist()
                  if args.embedding == 'local' else [embedder(t) for t in texts])
        vectors = dict(zip(texts, values))
        cache.parent.mkdir(exist_ok=True)
        cache.write_text(json.dumps(vectors, ensure_ascii=False), encoding='utf-8')
    output = {'timestamp': datetime.now(timezone.utc).isoformat(), 'embedding': backend,
              'answer_backend': 'extractive-offline, NOT generative LLM',
              'spec_sha256': hashlib.sha256((ROOT / 'benchmark_queries.json').read_bytes()).hexdigest(),
              'personal_strategy': personal_strategy, 'overlap': overlap,
              'chunk_size': size, 'top_k': spec['top_k'],
              'corpus': [d.metadata for d in docs], 'strategies': {}}
    for name, group in chunks.items():
        store = EmbeddingStore(embedding_fn=vectors.__getitem__)
        store.add_documents(group)
        agent = KnowledgeBaseAgent(store, extractive_backend)
        rows = []
        for query in spec['queries']:
            for filtered in (False, True):
                results = store.search_with_filter(query['question'], spec['top_k'],
                                                   query['filter'] if filtered else None)
                answer = agent.answer_from_results(query['question'], results)
                gold_docs = query.get('gold_docs', [query['gold_doc']])
                gold_context = '\n'.join(r['content'] for r in results if r['metadata']['doc_id'] in gold_docs)
                coverage = all(token.casefold() in gold_context.casefold() for token in query['evidence'])
                rank = next((i for i, r in enumerate(results, 1) if r['metadata']['doc_id'] in gold_docs), None)
                evidence_rank = next((i for i in range(1, len(results) + 1)
                    if all(token.casefold() in '\n'.join(r['content'] for r in results[:i]
                        if r['metadata']['doc_id'] in gold_docs).casefold()
                        for token in query['evidence'])), None)
                rows.append({'query': query, 'filtered': filtered,
                             'effective_filter': query['filter'] if filtered else None, 'results': results,
                             'missing_evidence': [token for token in query['evidence'] if token.casefold() not in gold_context.casefold()],
                             'answer': answer, 'gold_rank': rank, 'evidence_present': coverage,
                             'evidence_rank': evidence_rank,
                             'retrieval_score_proxy': (2 if evidence_rank == 1 else 1) if evidence_rank else 0})
        output['strategies'][name] = {'count': len(group),
            'avg_length': sum(len(d.content) for d in group) / len(group), 'rows': rows}
    (ROOT / 'report/benchmark_results.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = [f'Personal strategy: {personal_strategy}; chunk_size={size}; overlap={overlap}',
             f'Embedding: {backend}', f"Answer backend: {output['answer_backend']}",
             'Evidence checks are retrieval proxies, not final answer grading.']
    for name, info in output['strategies'].items():
        lines.append(f"\n{name}: {info['count']} chunks; average={info['avg_length']:.2f} characters")
        for row in info['rows']:
            lines.append(f"\n{row['query']['id']} mode={'Nam' if row['filtered'] else 'no_filter'} filter={row['effective_filter']}: {row['query']['question']}")
            lines.append(f"Gold: {row['query']['gold_answer']} | evidence={row['evidence_present']} | proxy={row['retrieval_score_proxy']}")
            for r in row['results']:
                lines.append(f"{r['id']} score={r['score']:.6f} source={r['metadata']['source_url']}\n{r['content']}")
            lines.append('Agent excerpts:\n' + row['answer'])
    (ROOT / 'ket_qua_benchmark.txt').write_text('\n'.join(lines), encoding='utf-8')
    for name, info in output['strategies'].items():
        rows = [r for r in info['rows'] if r['filtered']]
        print(name, 'chunks=', info['count'], 'evidence@3=', sum(r['evidence_present'] for r in rows), '/5')


if __name__ == '__main__':
    run()
