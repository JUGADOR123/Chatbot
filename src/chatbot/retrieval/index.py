import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from chatbot.domain.requests import Source

WORD_PATTERN = re.compile(r"[a-z0-9_]+")
STOP_WORDS = {"a", "an", "and", "do", "how", "i", "in", "is", "it", "the", "to", "what"}
CATEGORY_TERMS = {
    "installation": {"download", "extract", "launch", "java", "install"},
    "server_creation": {"create", "template", "import", "modpack", "mrpack"},
    "server_management": {"start", "stop", "launch", "console", "world", "version"},
    "addons": {"mod", "plugin", "addon", "modpack", "fabric", "forge", "paper"},
    "networking": {"join", "connect", "friends", "playit", "port", "firewall", "ip", "network"},
    "backups": {"backup", "restore", "recover", "save"},
    "access_control": {"operator", "op", "ban", "whitelist", "permission", "access"},
    "troubleshooting": {"error", "issue", "problem", "crash", "cannot", "failed", "working"},
    "telepath": {"telepath", "remote", "pair", "pairing", "vps", "cloud"},
}


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
            with cache_path.open(encoding="utf-8-sig") as cache_handle:
                cache = json.load(cache_handle)
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"could not load documentation cache: {cache_path}") from error
        if not isinstance(cache, dict):
            raise ValueError("documentation cache must contain a JSON object")

        database = sqlite3.connect(":memory:")
        database.execute("CREATE VIRTUAL TABLE documents USING fts5(guide, section, body, url, category)")
        for guide, guide_data in cache.items():
            if not isinstance(guide_data, dict) or not isinstance(guide_data.get("content"), dict):
                continue
            url = str(guide_data.get("url", ""))
            for section, body in guide_data["content"].items():
                if isinstance(body, str) and body.strip():
                    database.execute(
                        "INSERT INTO documents(guide, section, body, url, category) VALUES (?, ?, ?, ?, ?)",
                        (guide, section, body, url, _guide_category(guide)),
                    )
        _load_curated_documents(database, cache_path.parent / "end-user" / "catalog.json")
        database.commit()
        return cls(database)

    def search(self, query: str, *, limit: int = 3) -> list[Evidence]:
        terms = _terms(query)
        if not terms:
            return []
        match_query = " OR ".join(terms)
        rows = self._database.execute(
            "SELECT guide, section, body, url, category FROM documents WHERE documents MATCH ? LIMIT ?",
            (match_query, limit * 100),
        ).fetchall()
        query_terms = set(terms)
        evidence: list[Evidence] = []
        for guide, section, body, url, category in rows:
            document_terms = set(_terms(f"{guide} {section} {body}"))
            title_terms = set(_terms(f"{guide} {section}"))
            body_score = len(query_terms & document_terms) / len(query_terms)
            title_score = len(query_terms & title_terms) / len(query_terms)
            category_terms = CATEGORY_TERMS.get(category, set())
            category_score = 0.25 * len(query_terms & category_terms)
            score = body_score + title_score + category_score
            evidence.append(
                Evidence(
                    text=body,
                    source=Source(guide=guide, section=section, url=url, category=category),
                    score=score,
                )
            )
        evidence.sort(key=lambda item: item.score, reverse=True)
        return evidence[:limit]

    def close(self) -> None:
        self._database.close()


def _terms(text: str) -> list[str]:
    return [term for term in WORD_PATTERN.findall(text.lower()) if term not in STOP_WORDS]


def _guide_category(guide: str) -> str:
    normalized = guide.lower()
    categories = {
        "getting started": "installation",
        "server manager": "server_management",
        "back-ups": "backups",
        "access control": "access_control",
        "add-ons": "addons",
        "settings": "networking",
        "telepath": "telepath",
    }
    return categories.get(normalized, "general")


def _load_curated_documents(database: sqlite3.Connection, catalog_path: Path) -> None:
    if not catalog_path.is_file():
        return
    try:
        with catalog_path.open(encoding="utf-8-sig") as catalog_handle:
            catalog = json.load(catalog_handle)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not load end-user documentation catalog: {catalog_path}") from error
    if not isinstance(catalog, list):
        raise ValueError("end-user documentation catalog must contain a JSON array")
    for item in catalog:
        if not isinstance(item, dict):
            continue
        document_path = catalog_path.parent / str(item.get("path", ""))
        try:
            body = document_path.read_text(encoding="utf-8")
        except OSError as error:
            raise ValueError(f"could not load end-user document: {document_path}") from error
        title = str(item.get("title", ""))
        keywords = " ".join(str(keyword) for keyword in item.get("keywords", []))
        database.execute(
            "INSERT INTO documents(guide, section, body, url, category) VALUES (?, ?, ?, ?, ?)",
            ("End-user guide", title, f"{keywords}\n{body}", str(item.get("guide_url", item.get("source_url", ""))), str(item.get("category", "general"))),
        )