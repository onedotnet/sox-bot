import json
import re
from dataclasses import dataclass

import httpx


@dataclass
class Chunk:
    source_file: str
    heading: str
    content: str
    chunk_index: int


class KnowledgeIndexer:
    def __init__(self, api_key: str, base_url: str = "https://api.soxai.io/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def chunk_markdown(self, content: str, source_file: str) -> list[Chunk]:
        """Split markdown by ## headings, skipping chunks < 50 chars."""
        sections = re.split(r"(?m)^##\s+", content)
        chunks: list[Chunk] = []
        chunk_index = 0

        for section in sections:
            if not section.strip():
                continue

            lines = section.split("\n", 1)
            heading = lines[0].strip() if lines else ""
            body = lines[1].strip() if len(lines) > 1 else ""

            # If section has no heading (content before first ##)
            if not heading and body:
                body = section.strip()

            if len(body) < 50:
                continue

            chunks.append(
                Chunk(
                    source_file=source_file,
                    heading=heading,
                    content=body,
                    chunk_index=chunk_index,
                )
            )
            chunk_index += 1

        return chunks

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Call SoxAI text-embedding-3-small API to get embeddings."""
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": "text-embedding-3-small", "input": texts},
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]
