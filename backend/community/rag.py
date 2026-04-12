import json
import math
from dataclasses import dataclass, field

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.knowledge import KnowledgeChunk

RAG_SYSTEM = """You are a helpful assistant for SoxAI, an enterprise AI API gateway.
Answer questions using only the provided context. Be concise and accurate.
If the context doesn't contain enough information, say so clearly.
Always cite the source files when referencing specific information."""


@dataclass
class RAGResponse:
    answer: str
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.0


class RAGEngine:
    def __init__(self, api_key: str, base_url: str = "https://api.soxai.io/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _embed_query(self, query: str) -> list[float]:
        """Embed a single query string."""
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": "text-embedding-3-small", "input": [query]},
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]

    async def search(
        self, query: str, db: AsyncSession, top_k: int = 5
    ) -> list[KnowledgeChunk]:
        """Embed query, load all chunks from DB, compute cosine similarity, return top-k."""
        query_vec = self._embed_query(query)

        result = await db.execute(select(KnowledgeChunk))
        all_chunks = result.scalars().all()

        if not all_chunks:
            return []

        scored: list[tuple[float, KnowledgeChunk]] = []
        for chunk in all_chunks:
            chunk_vec = json.loads(chunk.embedding)
            sim = self._cosine_sim(query_vec, chunk_vec)
            scored.append((sim, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]

    def generate_answer(self, question: str, context_chunks: list[KnowledgeChunk]) -> RAGResponse:
        """Use Claude Sonnet with RAG_SYSTEM prompt to answer the question."""
        if not context_chunks:
            return RAGResponse(
                answer="I don't have enough information to answer this question.",
                sources=[],
                confidence=0.0,
            )

        context_parts = []
        sources = []
        for chunk in context_chunks:
            context_parts.append(f"[{chunk.source_file} - {chunk.heading}]\n{chunk.content}")
            if chunk.source_file not in sources:
                sources.append(chunk.source_file)

        context_text = "\n\n".join(context_parts)
        user_message = f"Context:\n{context_text}\n\nQuestion: {question}"

        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "claude-sonnet-4-5",
                    "messages": [
                        {"role": "system", "content": RAG_SYSTEM},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.2,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

        answer = data["choices"][0]["message"]["content"]
        confidence = min(1.0, len(context_chunks) / 5.0)

        return RAGResponse(answer=answer, sources=sources, confidence=confidence)

    @staticmethod
    def _cosine_sim(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)
