import re
import unicodedata

from app.schemas import SearchResult

NO_RELEVANT_INFO = "No relevant information found in the uploaded documents."
MIN_SIMILARITY_THRESHOLD = 0.55
FIELD_FACT_THRESHOLD = 0.45
FIELD_INTENT_PATTERNS: dict[str, tuple[str, ...]] = {
    "projektvezető": (
        "projektvezető",
        "projektvezeto",
        "projekt manager",
        "project manager",
        "felelős",
        "felelos",
    ),
    "költségkeret": (
        "költségkeret",
        "koltsegkeret",
        "költség",
        "koltseg",
        "budget",
    ),
    "határidő": (
        "határidő",
        "hatarido",
        "hatarideje",
        "deadline",
        "due date",
    ),
    "szerződés lejárata": (
        "szerzodes lejarata",
        "szerzodes lejarat",
        "szerzodes vege",
        "contract expiration",
        "contract expiry",
    ),
    "kapcsolattartó": (
        "kapcsolattarto",
        "kapcsolattartoja",
        "contact person",
        "contact",
    ),
    "havi díj": (
        "havi dij",
        "monthly fee",
        "havidij",
    ),
    "kockázatok": (
        "kockazatok",
        "kockazat",
        "risks",
        "risk list",
    ),
    "nyitott feladatok": (
        "nyitott feladatok",
        "open tasks",
        "todo",
    ),
}


_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "for",
    "from",
    "how",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "who",
    "why",
    # Hungarian question/connector words.
    "a",
    "az",
    "és",
    "hogy",
    "ki",
    "kik",
    "mi",
    "mit",
    "mikor",
    "milyen",
    "mennyi",
    "mekkora",
    "hol",
    "van",
    "volt",
}


def _query_tokens(query: str) -> list[str]:
    raw = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+", query.lower())
    return [token for token in raw if token not in _STOPWORDS and len(token) > 1]


def _candidate_lines(text: str) -> list[str]:
    # Keep both line-level and sentence-level candidates for explicit extraction.
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if sentence.strip()
    ]
    return lines + sentences


def _score_candidate(
    candidate: str, tokens: list[str], query_lower: str
) -> tuple[float, int, int]:
    lower = candidate.lower()
    token_hits = sum(1 for token in tokens if re.search(rf"\b{re.escape(token)}\b", lower))
    token_ratio = token_hits / max(len(tokens), 1)
    # Prefer explicit "field: value" style facts only when query terms are present.
    colon_bonus = 0.1 if ":" in candidate and token_hits > 0 else 0.0
    # Prefer shorter, direct candidates to avoid dumping chunks.
    brevity_bonus = 0.05 if len(candidate) <= 180 else 0.0
    # Bonus if the whole query text appears (for exact matches).
    exact_bonus = 0.2 if query_lower and query_lower in lower else 0.0
    score = token_ratio + colon_bonus + brevity_bonus + exact_bonus
    return (score, token_hits, len(candidate))


def _is_source_relevant(source: SearchResult) -> bool:
    return source.score >= MIN_SIMILARITY_THRESHOLD


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    ascii_folded = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[a-z0-9]+", ascii_folded))


def _stem_hu_token(token: str) -> str:
    # Very small heuristic stemmer for Hungarian field-question variants.
    # Handles common possessive/accusative/case endings used in questions.
    suffixes = (
        "ainak",
        "einek",
        "anak",
        "enek",
        "je",
        "ja",
        "ot",
        "et",
        "at",
        "t",
        "ban",
        "ben",
        "hoz",
        "hez",
        "hoz",
        "ra",
        "re",
        "rol",
        "tol",
        "nal",
        "nel",
        "nak",
        "nek",
    )
    for suffix in suffixes:
        if token.endswith(suffix) and len(token) - len(suffix) >= 5:
            return token[: -len(suffix)]
    return token


def _normalize_and_stem_tokens(text: str) -> list[str]:
    base_tokens = _normalize_text(text).split()
    return [_stem_hu_token(token) for token in base_tokens]


def _detect_query_field_intent(query: str) -> str | None:
    query_tokens = set(_normalize_and_stem_tokens(query))
    for field_name, patterns in FIELD_INTENT_PATTERNS.items():
        for pattern in patterns:
            pattern_tokens = set(_normalize_and_stem_tokens(pattern))
            if pattern_tokens and pattern_tokens.issubset(query_tokens):
                return field_name
        # Fallback to contains for multi-word English synonyms.
        normalized = _normalize_text(query)
        if any(_normalize_text(pattern) in normalized for pattern in patterns):
            return field_name
    return None


def _is_field_fact_candidate(candidate: str, query_intent_field: str | None) -> bool:
    if not query_intent_field:
        return False
    if ":" not in candidate:
        return False
    left, right = candidate.split(":", 1)
    field_tokens = set(_normalize_and_stem_tokens(left))
    value = right.strip()
    if not value:
        return False

    expected_patterns = FIELD_INTENT_PATTERNS.get(query_intent_field, ())
    for pattern in expected_patterns:
        pattern_tokens = set(_normalize_and_stem_tokens(pattern))
        if pattern_tokens and pattern_tokens.issubset(field_tokens):
            return True
    return False


def _extract_multiline_field_value(
    lines: list[str], start_index: int, field_name: str
) -> str | None:
    current = lines[start_index].strip()
    if ":" not in current:
        return None
    left, right = current.split(":", 1)
    if not _is_field_fact_candidate(f"{left.strip()}:{right.strip()}", field_name):
        return None

    initial_value = right.strip()
    if initial_value:
        return f"{left.strip()}: {initial_value}"

    # Multi-line field: capture following indented/bulleted content until next heading.
    collected: list[str] = []
    for next_line in lines[start_index + 1 :]:
        line = next_line.strip()
        if not line:
            if collected:
                break
            continue
        if ":" in line and not line.startswith(("-", "*", "•")):
            break
        cleaned = re.sub(r"^[-*•]\s*", "", line).strip()
        if cleaned:
            collected.append(cleaned)

    if not collected:
        return None
    return f"{left.strip()}: {'; '.join(collected)}"


def _extract_list_after_heading(
    lines: list[str], query_intent_field: str
) -> str | None:
    if query_intent_field not in {"kockázatok", "nyitott feladatok"}:
        return None

    expected_patterns = FIELD_INTENT_PATTERNS.get(query_intent_field, ())
    for index, raw in enumerate(lines):
        line = raw.strip()
        if ":" not in line:
            continue
        heading = line.split(":", 1)[0].strip()
        heading_tokens = set(_normalize_and_stem_tokens(heading))
        heading_matches = False
        for pattern in expected_patterns:
            pattern_tokens = set(_normalize_and_stem_tokens(pattern))
            if pattern_tokens and pattern_tokens.issubset(heading_tokens):
                heading_matches = True
                break
        if not heading_matches:
            continue

        items: list[str] = []
        for next_line in lines[index + 1 :]:
            value = next_line.strip()
            if not value:
                if items:
                    break
                continue
            if ":" in value and not value.startswith(("-", "*", "•")):
                break
            bullet = re.sub(r"^[-*•]\s*", "", value).strip()
            if bullet:
                items.append(bullet)

        if items:
            return f"{heading}: " + "; ".join(items)
    return None


def _extract_direct_answer(query: str, sources: list[SearchResult]) -> str | None:
    tokens = _query_tokens(query)
    query_lower = query.strip().lower()
    query_intent_field = _detect_query_field_intent(query)
    if not tokens and not query_lower:
        return None

    best_text: str | None = None
    best_score = (-1.0, -1, 10_000)

    for source in sources:
        if source.score < FIELD_FACT_THRESHOLD:
            continue
        lines = [line for line in source.content.splitlines()]

        # 1) List extraction after known headings.
        list_answer = _extract_list_after_heading(lines, query_intent_field or "")
        if list_answer:
            return list_answer

        # 2) Field extraction including multiline values.
        if query_intent_field:
            for idx in range(len(lines)):
                field_answer = _extract_multiline_field_value(
                    lines, idx, query_intent_field
                )
                if field_answer:
                    return field_answer

        # If query asks for a known field but no matching field exists in relevant chunks,
        # do not fallback to random sentence extraction.
        if query_intent_field:
            continue

        for candidate in _candidate_lines(source.content):
            if _is_field_fact_candidate(candidate, query_intent_field):
                return candidate

            if not _is_source_relevant(source):
                continue

            score, token_hits, length = _score_candidate(candidate, tokens, query_lower)
            # Do not extract random fields: require substantial query-term overlap.
            min_hits = 1 if len(tokens) <= 1 else 2
            if token_hits < min_hits:
                continue
            if score < 0.7:
                continue
            candidate_rank = (score, token_hits, -length)
            if candidate_rank > best_score:
                best_score = candidate_rank
                best_text = candidate

    return best_text


def build_answer(query: str, sources: list[SearchResult]) -> str:
    if not sources:
        return NO_RELEVANT_INFO

    direct = _extract_direct_answer(query, sources)
    if direct:
        return direct

    return NO_RELEVANT_INFO
