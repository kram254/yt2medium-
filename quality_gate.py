"""
quality_gate.py — Pre-publish quality gate for the yt2medium Flask app.

Combines checks inspired by community skills (slop-cop, de-slop,
authenticity-check, content-similarity-checker) into a single pure-Python
scoring system used before publishing a generated Medium post.

No external dependencies: only re, math, collections, string from stdlib.
All public functions are defensive (try/except) and return sensible
defaults on error so a bug here never blocks the publish pipeline outright
(callers should treat missing/([]) results as "check unavailable").
"""

import re
import math
import string
from collections import Counter

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_VOWELS = "aeiouy"

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[A-Za-z']+")
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")


def _sentences(text):
    text = (text or "").strip()
    if not text:
        return []
    parts = _SENTENCE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def _words(text):
    return _WORD_RE.findall(text or "")


def _paragraphs(text):
    text = (text or "").strip()
    if not text:
        return []
    parts = _PARAGRAPH_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def _count_syllables(word):
    """Rough heuristic syllable counter (no dictionary)."""
    word = word.lower().strip(string.punctuation)
    if not word:
        return 0
    if len(word) <= 3:
        return 1

    # strip common silent-e endings
    word = re.sub(r"(?:[^laeiouy])e$", "", word)
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    return max(1, count)


def _safe_div(a, b, default=0.0):
    try:
        if b == 0:
            return default
        return a / b
    except Exception:
        return default


# ---------------------------------------------------------------------------
# 1. AI authenticity / "slop" detector
# ---------------------------------------------------------------------------

BANNED_WORDS = [
    "delve", "foster", "leverage", "utilize", "facilitate", "empower",
    "streamline", "robust", "cutting-edge", "paradigm shift", "game changer",
    "tapestry", "realm", "beacon", "multifaceted", "meticulous", "intricate",
    "paramount", "transformative", "elevate", "embark", "supercharge",
    "harness", "ever-evolving",
]

_AI_PATTERNS = [
    {
        "name": "binary_contrast",
        "regex": re.compile(
            r"\bIt'?s\s+not\s+(?:just\s+)?[^.?!]{1,60}[.?!]\s*It'?s\s+[^.?!]{1,60}[.?!]",
            re.IGNORECASE,
        ),
        "severity": "high",
    },
    {
        "name": "throat_clearing_opener",
        "regex": re.compile(
            r"\b(?:Here'?s\s+the\s+thing|Let'?s\s+be\s+honest|At\s+the\s+end\s+of\s+the\s+day|"
            r"In\s+today'?s\s+(?:fast-paced|digital)\s+world)\b",
            re.IGNORECASE,
        ),
        "severity": "medium",
    },
    {
        "name": "faux_insight_setup",
        "regex": re.compile(
            r"\b(?:What\s+nobody\s+tells\s+you|What\s+(?:most|many)\s+people\s+(?:don'?t|do\s+not)\s+"
            r"(?:realize|understand|know)|The\s+truth\s+(?:is|no\s+one\s+tells\s+you))\b",
            re.IGNORECASE,
        ),
        "severity": "high",
    },
    {
        "name": "colon_reveal",
        "regex": re.compile(
            r"\b(?:The\s+best\s+part|The\s+result|The\s+catch|The\s+kicker|Here'?s\s+the\s+kicker)\s*:",
            re.IGNORECASE,
        ),
        "severity": "medium",
    },
    {
        "name": "dramatic_fragment",
        "regex": re.compile(
            r"[.!?]\s+[A-Z][a-z]{1,20}\.\s",
        ),
        "severity": "low",
    },
    {
        "name": "importance_puffery",
        "regex": re.compile(
            r"\b(?:marks\s+a\s+pivotal\s+moment|stands?\s+as\s+a\s+testament|"
            r"represents?\s+a\s+(?:significant|major)\s+(?:shift|milestone)|"
            r"underscores?\s+the\s+importance)\b",
            re.IGNORECASE,
        ),
        "severity": "high",
    },
    {
        "name": "weasel_attribution",
        "regex": re.compile(
            r"\b(?:experts\s+agree|studies\s+show|research\s+suggests|many\s+believe|"
            r"industry\s+leaders\s+say)\b",
            re.IGNORECASE,
        ),
        "severity": "medium",
    },
    {
        "name": "fake_profound_kicker",
        "regex": re.compile(
            r"\b(?:and\s+that\s+changes\s+everything|the\s+rest,?\s+as\s+they\s+say,?\s+is\s+history|"
            r"only\s+time\s+will\s+tell)\.?\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        "severity": "medium",
    },
    {
        "name": "summary_recap_ending",
        "regex": re.compile(
            r"\b(?:In\s+conclusion|To\s+sum\s+up|In\s+summary|Overall,?\s+it'?s\s+clear|"
            r"At\s+the\s+end\s+of\s+the\s+day,?\s+it'?s\s+clear)\b",
            re.IGNORECASE,
        ),
        "severity": "medium",
    },
]


def _find_em_dash_overuse(text):
    dashes = re.findall(r"—|--", text or "")
    word_count = max(1, len(_words(text)))
    ratio = len(dashes) / word_count
    if ratio > 0.01 and len(dashes) >= 3:
        return {
            "pattern_name": "em_dash_overuse",
            "example_text": f"{len(dashes)} em-dashes found",
            "severity": "medium" if ratio < 0.02 else "high",
        }
    return None


def _find_synonym_cycling(text):
    """Detect near-synonym clusters used repeatedly (heuristic)."""
    clusters = [
        ["important", "crucial", "vital", "essential", "critical", "significant"],
        ["fast", "rapid", "swift", "quick", "speedy"],
        ["big", "huge", "massive", "enormous", "vast"],
    ]
    lower = (text or "").lower()
    hits = []
    for cluster in clusters:
        present = [w for w in cluster if re.search(r"\b" + re.escape(w) + r"\b", lower)]
        if len(present) >= 3:
            hits.append(present)
    if hits:
        example = ", ".join(hits[0])
        return {
            "pattern_name": "synonym_cycling",
            "example_text": f"Multiple near-synonyms used: {example}",
            "severity": "low",
        }
    return None


def _sentence_structure_repetition(sentences):
    """Detect repeated sentence lengths / opening structure."""
    if len(sentences) < 5:
        return None
    lengths = [len(_words(s)) for s in sentences]
    length_counts = Counter(lengths)
    most_common_len, count = length_counts.most_common(1)[0]
    ratio = count / len(sentences)

    openers = []
    for s in sentences:
        w = _words(s)
        openers.append(w[0].lower() if w else "")
    opener_counts = Counter(openers)
    most_common_opener, opener_count = (
        opener_counts.most_common(1)[0] if opener_counts else ("", 0)
    )
    opener_ratio = _safe_div(opener_count, len(sentences))

    findings = []
    if ratio > 0.35:
        findings.append(
            {
                "pattern_name": "sentence_length_repetition",
                "example_text": f"{count} of {len(sentences)} sentences are ~{most_common_len} words long",
                "severity": "low" if ratio < 0.5 else "medium",
            }
        )
    if opener_ratio > 0.3 and most_common_opener:
        findings.append(
            {
                "pattern_name": "sentence_opener_repetition",
                "example_text": f"'{most_common_opener}' starts {opener_count} sentences",
                "severity": "low" if opener_ratio < 0.45 else "medium",
            }
        )
    return findings


def _paragraph_uniformity(paragraphs):
    if len(paragraphs) < 4:
        return None
    lengths = [len(_sentences(p)) for p in paragraphs]
    if not lengths:
        return None
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std = math.sqrt(variance)
    if mean > 0 and std / mean < 0.15 and mean > 1:
        return {
            "pattern_name": "paragraph_uniformity",
            "example_text": f"All {len(paragraphs)} paragraphs have ~{mean:.1f} sentences (very uniform)",
            "severity": "low",
        }
    return None


_SEVERITY_PENALTY = {"low": 3, "medium": 6, "high": 10}


def check_ai_authenticity(blog_text):
    """
    Pure-Python heuristic AI-authenticity / "slop" detector.

    Returns:
        {
            "authenticity_score": 0-100 (100 = very human),
            "ai_patterns_found": [{"pattern_name", "example_text", "severity"}, ...]
        }
    """
    try:
        text = blog_text or ""
        findings = []

        for pattern in _AI_PATTERNS:
            for match in pattern["regex"].finditer(text):
                snippet = match.group(0).strip()
                snippet = snippet[:140]
                findings.append(
                    {
                        "pattern_name": pattern["name"],
                        "example_text": snippet,
                        "severity": pattern["severity"],
                    }
                )
                # cap per-pattern findings to keep the report readable
                if sum(1 for f in findings if f["pattern_name"] == pattern["name"]) >= 5:
                    break

        # banned words
        lower_text = text.lower()
        for banned in BANNED_WORDS:
            hits = list(re.finditer(r"\b" + re.escape(banned) + r"\b", lower_text))
            if hits:
                findings.append(
                    {
                        "pattern_name": "banned_word",
                        "example_text": f"'{banned}' used {len(hits)} time(s)",
                        "severity": "medium" if len(hits) > 1 else "low",
                    }
                )

        em_dash_finding = _find_em_dash_overuse(text)
        if em_dash_finding:
            findings.append(em_dash_finding)

        synonym_finding = _find_synonym_cycling(text)
        if synonym_finding:
            findings.append(synonym_finding)

        sentences = _sentences(text)
        structure_findings = _sentence_structure_repetition(sentences)
        if structure_findings:
            findings.extend(structure_findings)

        paragraphs = _paragraphs(text)
        uniformity_finding = _paragraph_uniformity(paragraphs)
        if uniformity_finding:
            findings.append(uniformity_finding)

        score = 100
        for f in findings:
            score -= _SEVERITY_PENALTY.get(f.get("severity", "low"), 3)
        score = max(0, min(100, score))

        return {
            "authenticity_score": score,
            "ai_patterns_found": findings,
        }
    except Exception:
        return {"authenticity_score": 50, "ai_patterns_found": []}


# ---------------------------------------------------------------------------
# 2. Content similarity (TF-IDF cosine similarity from scratch)
# ---------------------------------------------------------------------------

_STOPWORDS = set(
    """
    a an the and or but if then else for of to in on at by with as is are was
    were be been being this that these those it its it's from into about
    over under again further once here there when where why how all any
    both each few more most other some such no nor not only own same so than
    too very can will just don should now i you he she we they them his her
    their our your my me
    """.split()
)


def _tokenize(text):
    words = [w.lower() for w in _words(text)]
    return [w for w in words if w not in _STOPWORDS and len(w) > 1]


def _tf(tokens):
    counts = Counter(tokens)
    total = max(1, len(tokens))
    return {term: count / total for term, count in counts.items()}


def _build_idf(all_token_lists):
    n_docs = max(1, len(all_token_lists))
    df = Counter()
    for tokens in all_token_lists:
        for term in set(tokens):
            df[term] += 1
    idf = {}
    for term, count in df.items():
        idf[term] = math.log((1 + n_docs) / (1 + count)) + 1
    return idf


def _tfidf_vector(tokens, idf):
    tf = _tf(tokens)
    return {term: freq * idf.get(term, 0.0) for term, freq in tf.items()}


def _cosine_similarity(vec_a, vec_b):
    common_terms = set(vec_a.keys()) & set(vec_b.keys())
    dot = sum(vec_a[t] * vec_b[t] for t in common_terms)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def check_content_similarity(new_text, existing_posts):
    """
    Pure-Python TF-IDF + cosine-similarity duplicate-content checker.

    existing_posts: iterable of dicts like {"title": str, "text": str}
                     (also tolerates {"post_title": str, "body": str}, etc.)

    Returns:
        {
            "is_duplicate": bool,
            "max_similarity": float 0-1,
            "similar_posts": [{"post_title", "similarity_score"}, ...]
        }
    """
    try:
        existing_posts = existing_posts or []
        new_tokens = _tokenize(new_text or "")

        docs = []
        titles = []
        for post in existing_posts:
            if isinstance(post, dict):
                title = post.get("title") or post.get("post_title") or "Untitled"
                body = post.get("text") or post.get("body") or post.get("content") or ""
            else:
                title = "Untitled"
                body = str(post)
            docs.append(_tokenize(body))
            titles.append(title)

        if not docs or not new_tokens:
            return {
                "is_duplicate": False,
                "max_similarity": 0.0,
                "similar_posts": [],
            }

        all_token_lists = docs + [new_tokens]
        idf = _build_idf(all_token_lists)
        new_vec = _tfidf_vector(new_tokens, idf)

        similar_posts = []
        for title, tokens in zip(titles, docs):
            doc_vec = _tfidf_vector(tokens, idf)
            sim = _cosine_similarity(new_vec, doc_vec)
            similar_posts.append({"post_title": title, "similarity_score": round(sim, 4)})

        similar_posts.sort(key=lambda x: x["similarity_score"], reverse=True)
        max_similarity = similar_posts[0]["similarity_score"] if similar_posts else 0.0

        return {
            "is_duplicate": max_similarity > 0.7,
            "max_similarity": max_similarity,
            "similar_posts": similar_posts[:10],
        }
    except Exception:
        return {"is_duplicate": False, "max_similarity": 0.0, "similar_posts": []}


# ---------------------------------------------------------------------------
# 3. Readability (Flesch-Kincaid, passive voice heuristic)
# ---------------------------------------------------------------------------

_PASSIVE_AUX_RE = re.compile(
    r"\b(?:was|were|is|are|been|being|be)\s+(?:\w+ly\s+)?(\w+ed|\w+en)\b",
    re.IGNORECASE,
)


def check_readability(blog_text):
    """
    Pure-Python readability metrics (no textstat/nltk).

    Returns:
        {
            "flesch_reading_ease": float,
            "grade_level": float,
            "avg_sentence_length": float,
            "avg_word_length": float,
            "complex_word_percentage": float,
            "passive_voice_estimate": float,
            "verdict": "easy"|"medium"|"hard"
        }
    """
    try:
        text = blog_text or ""
        sentences = _sentences(text)
        words = _words(text)

        n_sentences = max(1, len(sentences))
        n_words = max(1, len(words))

        syllable_counts = [_count_syllables(w) for w in words]
        n_syllables = sum(syllable_counts)

        avg_sentence_length = n_words / n_sentences
        avg_word_length = sum(len(w) for w in words) / n_words

        complex_words = [w for w, s in zip(words, syllable_counts) if s >= 3]
        complex_word_percentage = 100 * len(complex_words) / n_words

        flesch = (
            206.835
            - 1.015 * avg_sentence_length
            - 84.6 * (n_syllables / n_words)
        )
        flesch = max(0.0, min(100.0, flesch))

        grade_level = (
            0.39 * avg_sentence_length + 11.8 * (n_syllables / n_words) - 15.59
        )
        grade_level = max(0.0, grade_level)

        passive_matches = len(_PASSIVE_AUX_RE.findall(text))
        passive_voice_estimate = 100 * _safe_div(passive_matches, n_sentences)
        passive_voice_estimate = min(100.0, passive_voice_estimate)

        if flesch >= 60:
            verdict = "easy"
        elif flesch >= 30:
            verdict = "medium"
        else:
            verdict = "hard"

        return {
            "flesch_reading_ease": round(flesch, 2),
            "grade_level": round(grade_level, 2),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "avg_word_length": round(avg_word_length, 2),
            "complex_word_percentage": round(complex_word_percentage, 2),
            "passive_voice_estimate": round(passive_voice_estimate, 2),
            "verdict": verdict,
        }
    except Exception:
        return {
            "flesch_reading_ease": 50.0,
            "grade_level": 10.0,
            "avg_sentence_length": 0.0,
            "avg_word_length": 0.0,
            "complex_word_percentage": 0.0,
            "passive_voice_estimate": 0.0,
            "verdict": "medium",
        }


# ---------------------------------------------------------------------------
# 4. Structure check
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S+", re.MULTILINE)
_CODE_BLOCK_RE = re.compile(r"```")
_LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+\.\s+)\S+", re.MULTILINE)
_CONCLUSION_HEADING_RE = re.compile(
    r"^\s{0,3}#{1,6}\s*(conclusion|final\s+thoughts|wrap[\s-]?up|summary|takeaways?)\b",
    re.IGNORECASE | re.MULTILINE,
)


def check_structure(blog_text):
    """
    Pure-Python structural quality check for a Medium-style blog post.

    Returns:
        {
            "has_title": bool,
            "has_introduction": bool,
            "has_subheadings": bool,
            "subheading_count": int,
            "has_conclusion": bool,
            "has_code_blocks": bool,
            "has_lists": bool,
            "word_count": int,
            "estimated_read_time": str,
            "structure_score": 0-100
        }
    """
    try:
        text = blog_text or ""
        lines = [l for l in text.splitlines() if l.strip()]

        has_title = False
        if lines:
            first_line = lines[0].strip()
            has_title = bool(re.match(r"^#\s+\S+", first_line)) or (
                0 < len(first_line) <= 120 and not first_line.endswith((".", "!", "?"))
            )

        paragraphs = _paragraphs(text)
        # skip a markdown title line if present when finding the intro paragraph
        body_paragraphs = paragraphs
        if paragraphs and re.match(r"^#\s+\S+", paragraphs[0].strip()):
            body_paragraphs = paragraphs[1:]
        first_body_paragraph = body_paragraphs[0] if body_paragraphs else ""
        has_introduction = 0 < len(_sentences(first_body_paragraph)) < 4

        subheadings = _HEADING_RE.findall(text)
        # exclude the title itself (an H1 at the very top) from subheading count
        subheading_count = len(subheadings)
        if lines and re.match(r"^#\s+\S+", lines[0].strip()):
            subheading_count = max(0, subheading_count - 1)
        has_subheadings = subheading_count > 0

        has_conclusion = bool(_CONCLUSION_HEADING_RE.search(text)) or bool(
            re.search(
                r"\b(?:in\s+conclusion|to\s+sum\s+up|final\s+thoughts|wrapping\s+up)\b",
                text,
                re.IGNORECASE,
            )
        )

        has_code_blocks = bool(_CODE_BLOCK_RE.search(text))
        has_lists = bool(_LIST_RE.search(text))

        word_count = len(_words(text))
        minutes = max(1, round(word_count / 200))
        estimated_read_time = f"{minutes} min read"

        score = 0
        score += 15 if has_title else 0
        score += 15 if has_introduction else 0
        score += 20 if has_subheadings else 0
        score += 15 if has_conclusion else 0
        score += 10 if has_code_blocks else 0
        score += 10 if has_lists else 0
        score += 15 if word_count >= 500 else round(15 * word_count / 500)
        score = max(0, min(100, score))

        return {
            "has_title": has_title,
            "has_introduction": has_introduction,
            "has_subheadings": has_subheadings,
            "subheading_count": subheading_count,
            "has_conclusion": has_conclusion,
            "has_code_blocks": has_code_blocks,
            "has_lists": has_lists,
            "word_count": word_count,
            "estimated_read_time": estimated_read_time,
            "structure_score": score,
        }
    except Exception:
        return {
            "has_title": False,
            "has_introduction": False,
            "has_subheadings": False,
            "subheading_count": 0,
            "has_conclusion": False,
            "has_code_blocks": False,
            "has_lists": False,
            "word_count": 0,
            "estimated_read_time": "0 min read",
            "structure_score": 0,
        }


# ---------------------------------------------------------------------------
# 5. Combined quality gate
# ---------------------------------------------------------------------------

_WEIGHTS = {
    "authenticity": 0.30,
    "readability": 0.25,
    "structure": 0.25,
    "originality": 0.20,
}


def _readability_score(readability_result):
    """Map readability metrics to a 0-100 'quality' score (not raw Flesch)."""
    try:
        flesch = readability_result.get("flesch_reading_ease", 50.0)
        passive = readability_result.get("passive_voice_estimate", 0.0)
        # ideal Flesch for a blog post is roughly 50-70; penalize extremes
        if 50 <= flesch <= 70:
            base = 100
        elif flesch < 50:
            base = max(0, 100 - (50 - flesch) * 1.5)
        else:
            base = max(0, 100 - (flesch - 70) * 1.0)
        passive_penalty = min(30, passive * 0.6)
        return max(0, min(100, base - passive_penalty))
    except Exception:
        return 50.0


def _build_recommendations(authenticity, similarity, readability, structure):
    recs = []

    if authenticity.get("authenticity_score", 100) < 70:
        top_patterns = Counter(
            f["pattern_name"] for f in authenticity.get("ai_patterns_found", [])
        ).most_common(2)
        if top_patterns:
            names = ", ".join(p.replace("_", " ") for p, _ in top_patterns)
            recs.append(f"Reduce AI-sounding phrasing, especially: {names}.")
        else:
            recs.append("Rewrite sections to sound more human and less templated.")

    if similarity.get("is_duplicate"):
        top = similarity.get("similar_posts", [{}])[0]
        recs.append(
            f"This post is very similar to '{top.get('post_title', 'an existing post')}' "
            f"({round(top.get('similarity_score', 0) * 100)}% similar) — differentiate the angle or content."
        )
    elif similarity.get("max_similarity", 0) > 0.5:
        recs.append("Content overlaps notably with an existing post — consider adding unique analysis or examples.")

    if readability.get("verdict") == "hard":
        recs.append("Simplify sentence structure and vocabulary to improve readability (Flesch score is low).")
    if readability.get("passive_voice_estimate", 0) > 20:
        recs.append("Reduce passive voice — rewrite passive constructions as active sentences.")

    if not structure.get("has_subheadings"):
        recs.append("Add subheadings to break the post into scannable sections.")
    if not structure.get("has_introduction"):
        recs.append("Tighten the opening paragraph into a short, focused introduction (under 4 sentences).")
    if not structure.get("has_conclusion"):
        recs.append("Add a clear conclusion or takeaways section.")
    if structure.get("word_count", 0) < 500:
        recs.append("Expand the post — it's shorter than the ~500 words typical for a solid Medium article.")

    if not recs:
        recs.append("Quality checks look solid — consider a final proofread before publishing.")

    return recs[:5]


def _grade_from_score(score):
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def run_quality_gate(blog_text, existing_posts=None):
    """
    Runs all quality checks and produces a single weighted verdict.

    Returns:
        {
            "overall_score": 0-100,
            "passed": bool,
            "checks": {
                "authenticity": {...},
                "similarity": {...},
                "readability": {...},
                "structure": {...},
            },
            "recommendations": [str, ...] (up to 5),
            "grade": "A"|"B"|"C"|"D"|"F"
        }
    """
    try:
        existing_posts = existing_posts or []

        authenticity = check_ai_authenticity(blog_text)
        similarity = check_content_similarity(blog_text, existing_posts)
        readability = check_readability(blog_text)
        structure = check_structure(blog_text)

        authenticity_score = authenticity.get("authenticity_score", 50)
        readability_score = _readability_score(readability)
        structure_score = structure.get("structure_score", 50)
        originality_score = max(0, 100 - similarity.get("max_similarity", 0.0) * 100)

        overall_score = (
            authenticity_score * _WEIGHTS["authenticity"]
            + readability_score * _WEIGHTS["readability"]
            + structure_score * _WEIGHTS["structure"]
            + originality_score * _WEIGHTS["originality"]
        )
        overall_score = round(max(0, min(100, overall_score)), 2)

        recommendations = _build_recommendations(
            authenticity, similarity, readability, structure
        )

        return {
            "overall_score": overall_score,
            "passed": overall_score >= 60,
            "checks": {
                "authenticity": authenticity,
                "similarity": similarity,
                "readability": readability,
                "structure": structure,
            },
            "recommendations": recommendations,
            "grade": _grade_from_score(overall_score),
        }
    except Exception:
        return {
            "overall_score": 0.0,
            "passed": False,
            "checks": {
                "authenticity": {"authenticity_score": 0, "ai_patterns_found": []},
                "similarity": {"is_duplicate": False, "max_similarity": 0.0, "similar_posts": []},
                "readability": {
                    "flesch_reading_ease": 0.0,
                    "grade_level": 0.0,
                    "avg_sentence_length": 0.0,
                    "avg_word_length": 0.0,
                    "complex_word_percentage": 0.0,
                    "passive_voice_estimate": 0.0,
                    "verdict": "hard",
                },
                "structure": {
                    "has_title": False,
                    "has_introduction": False,
                    "has_subheadings": False,
                    "subheading_count": 0,
                    "has_conclusion": False,
                    "has_code_blocks": False,
                    "has_lists": False,
                    "word_count": 0,
                    "estimated_read_time": "0 min read",
                    "structure_score": 0,
                },
            },
            "recommendations": ["Quality gate encountered an error — review the post manually before publishing."],
            "grade": "F",
        }


# ---------------------------------------------------------------------------
# 6. Human-readable report
# ---------------------------------------------------------------------------

def format_quality_report(gate_result):
    """
    Renders a run_quality_gate() result as a Markdown report string.
    """
    try:
        gate_result = gate_result or {}
        overall_score = gate_result.get("overall_score", 0)
        grade = gate_result.get("grade", "F")
        passed = gate_result.get("passed", False)
        checks = gate_result.get("checks", {}) or {}

        authenticity = checks.get("authenticity", {}) or {}
        similarity = checks.get("similarity", {}) or {}
        readability = checks.get("readability", {}) or {}
        structure = checks.get("structure", {}) or {}

        lines = []
        lines.append("# Quality Gate Report")
        lines.append("")
        status = "PASSED" if passed else "FAILED"
        lines.append(f"**Overall Score:** {overall_score}/100 (Grade {grade}) — **{status}**")
        lines.append("")

        lines.append("## Authenticity")
        lines.append(f"- Score: {authenticity.get('authenticity_score', 'N/A')}/100")
        patterns = authenticity.get("ai_patterns_found", [])
        if patterns:
            lines.append(f"- {len(patterns)} AI-pattern issue(s) found:")
            for p in patterns[:10]:
                lines.append(
                    f"  - [{p.get('severity', 'low')}] {p.get('pattern_name', '')}: "
                    f"\"{p.get('example_text', '')}\""
                )
        else:
            lines.append("- No AI-sounding patterns detected.")
        lines.append("")

        lines.append("## Originality")
        lines.append(f"- Max similarity to existing posts: {round(similarity.get('max_similarity', 0.0) * 100, 1)}%")
        lines.append(f"- Duplicate flag: {'YES' if similarity.get('is_duplicate') else 'no'}")
        similar_posts = similarity.get("similar_posts", [])
        if similar_posts:
            lines.append("- Closest matches:")
            for sp in similar_posts[:3]:
                lines.append(
                    f"  - {sp.get('post_title', 'Untitled')}: "
                    f"{round(sp.get('similarity_score', 0.0) * 100, 1)}%"
                )
        lines.append("")

        lines.append("## Readability")
        lines.append(f"- Flesch Reading Ease: {readability.get('flesch_reading_ease', 'N/A')} ({readability.get('verdict', 'N/A')})")
        lines.append(f"- Grade Level: {readability.get('grade_level', 'N/A')}")
        lines.append(f"- Avg Sentence Length: {readability.get('avg_sentence_length', 'N/A')} words")
        lines.append(f"- Avg Word Length: {readability.get('avg_word_length', 'N/A')} chars")
        lines.append(f"- Complex Words: {readability.get('complex_word_percentage', 'N/A')}%")
        lines.append(f"- Estimated Passive Voice: {readability.get('passive_voice_estimate', 'N/A')}%")
        lines.append("")

        lines.append("## Structure")
        lines.append(f"- Title: {'yes' if structure.get('has_title') else 'no'}")
        lines.append(f"- Introduction: {'yes' if structure.get('has_introduction') else 'no'}")
        lines.append(f"- Subheadings: {structure.get('subheading_count', 0)}")
        lines.append(f"- Conclusion: {'yes' if structure.get('has_conclusion') else 'no'}")
        lines.append(f"- Code blocks: {'yes' if structure.get('has_code_blocks') else 'no'}")
        lines.append(f"- Lists: {'yes' if structure.get('has_lists') else 'no'}")
        lines.append(f"- Word count: {structure.get('word_count', 0)} ({structure.get('estimated_read_time', 'N/A')})")
        lines.append(f"- Structure Score: {structure.get('structure_score', 'N/A')}/100")
        lines.append("")

        lines.append("## Top Recommendations")
        recommendations = gate_result.get("recommendations", [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"{i}. {rec}")
        else:
            lines.append("No recommendations.")

        return "\n".join(lines)
    except Exception:
        return "# Quality Gate Report\n\nUnable to generate report due to an internal error."
