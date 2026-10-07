import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from chatbot.domain.requests import Source

WORD_PATTERN = re.compile(r"[a-z0-9_]+")
STOP_WORDS = {"a", "an", "and", "do", "how", "i", "in", "is", "it", "the", "to", "what"}


@dataclass(frozen=True, slots=True)
class Evidence:
    text: str
    source: Source
    score: float


class DocumentIndex:
    def __init__(self, database: sqlite3.Connection) -> None:
        self._database = database

    @classmethod
    def from_cache(cls, cache_path: Path) -> "DocumentIndex":
        try:
            with cache_path.open(encoding="utf-8") as cache_handle:
                cache = json.load(cache_handle)
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"could not load documentation cache: {cache_path}") from error
        if not isinstance(cache, dict):
            raise ValueError("documentation cache must contain a JSON object")

        database = sqlite3.connect(":memory:")
        database.execute("CREATE VIRTUAL TABLE documents USING fts5(guide, section, body, url)")
        for guide, guide_data in cache.items():
            if not isinstance(guide_data, dict) or not isinstance(guide_data.get("content"), dict):
                continue
            url = str(guide_data.get("url", ""))
            for section, body in guide_data["content"].items():
                if isinstance(body, str) and body.strip():
                    database.execute(
                        "INSERT INTO documents(guide, section, body, url) VALUES (?, ?, ?, ?)",
                        (guide, section, body, url),
                    )
        database.commit()
        return cls(database)

    def search(self, query: str, *, limit: int = 3) -> list[Evidence]:
        terms = _terms(query)
        if not terms:
            return []
        match_query = " OR ".join(terms)
        rows = self._database.execute(
            "SELECT guide, section, body, url FROM documents WHERE documents MATCH ? LIMIT ?",
            (match_query, limit * 3),
        ).fetchall()
        query_terms = set(terms)
        evidence: list[Evidence] = []
        for guide, section, body, url in rows:
            document_terms = set(_terms(f"{guide} {section} {body}"))
            title_terms = set(_terms(f"{guide} {section}"))
            body_score = len(query_terms & document_terms) / len(query_terms)
            title_score = len(query_terms & title_terms) / len(query_terms)
            score = body_score + title_score
            evidence.append(
                Evidence(
                    text=body,
                    source=Source(guide=guide, section=section, url=url),
                    score=score,
                )
            )
        evidence.sort(key=lambda item: item.score, reverse=True)
        return evidence[:limit]

    def close(self) -> None:
        self._database.close()


def _terms(text: str) -> list[str]:
    return [term for term in WORD_PATTERN.findall(text.lower()) if term not in STOP_WORDS]