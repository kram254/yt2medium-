"""
seo_optimizer.py
=================

Deep SEO optimization utilities for yt2medium.

This module is inspired by patterns found in the community
"claude-seo-skills" and "marketingskills" skill packs: keyword density
analysis, heading hierarchy checks, readability scoring, AI-assisted
metadata generation, Medium-specific formatting optimization, and
pre-writing content briefs.

It plugs into the app's existing AI manager pattern:

    ai_manager.generate_content(prompt, context, model)

All public functions are defensive: they catch exceptions internally and
return sensible, non-crashing fallback values so a failure here never
breaks the surrounding content-generation pipeline.

No external dependencies are required beyond the Python standard library
(re, json, math, collections).
"""

import re
import json
import math
from collections import Counter

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "when",
    "at", "by", "for", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "to",
    "from", "up", "down", "in", "out", "on", "off", "over", "under",
    "again", "further", "once", "here", "there", "all", "any", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
    "can", "will", "just", "don", "should", "now", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "having", "do",
    "does", "did", "doing", "of", "as", "it", "its", "this", "that",
    "these", "those", "i", "you", "he", "she", "we", "they", "them",
    "his", "her", "their", "our", "your", "my", "me", "him", "us",
    "which", "who", "whom", "what", "how", "why", "also", "would",
    "could", "may", "might", "must", "shall",
}

MEDIUM_META_LIMIT = 155
MEDIUM_TITLE_LIMIT = 60


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe(default):
    """Decorator factory returning `default` (or default()) on any exception."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - defensive by design
                print(f"[seo_optimizer] {func.__name__} failed: {exc}")
                return default() if callable(default) else default
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


def _strip_markdown(text):
    """Remove markdown syntax to get plain readable text."""
    if not text:
        return ""
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_>#`~-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _get_headings(blog_text):
    """Extract markdown-style headings as list of (level, text)."""
    headings = []
    if not blog_text:
        return headings
    for line in blog_text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)", line.strip())
        if m:
            headings.append((len(m.group(1)), m.group(2).strip()))
    return headings


def _split_sentences(text):
    text = text.strip()
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def _split_words(text):
    return re.findall(r"[A-Za-z']+", text.lower())


def _count_syllables(word):
    """Very simple heuristic syllable counter (no external libs)."""
    word = word.lower().strip()
    word = re.sub(r"[^a-z]", "", word)
    if not word:
        return 0
    vowels = "aeiouy"
    count = 0
    prev_was_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    if word.endswith("le") and len(word) > 2 and word[-3] not in vowels:
        count += 1
    return max(count, 1)


def _flesch_kincaid_grade(text):
    """Compute Flesch-Kincaid Grade Level without external libraries."""
    sentences = _split_sentences(text)
    words = _split_words(text)
    if not sentences or not words:
        return 0.0
    num_sentences = len(sentences)
    num_words = len(words)
    num_syllables = sum(_count_syllables(w) for w in words)
    grade = (
        0.39 * (num_words / num_sentences)
        + 11.8 * (num_syllables / num_words)
        - 15.59
    )
    return round(max(grade, 0.0), 1)


def _extract_keywords(text, top_n=10):
    words = _split_words(text)
    filtered = [w for w in words if w not in STOPWORDS and len(w) > 2]
    total = len(words) or 1
    counts = Counter(filtered)

    # Also consider simple 2-word phrases (bigrams) for phrase-level SEO signal.
    bigrams = []
    for i in range(len(filtered) - 1):
        bigrams.append(f"{filtered[i]} {filtered[i + 1]}")
    bigram_counts = Counter(bigrams)

    density = {}
    for word, count in counts.most_common(top_n):
        density[word] = round((count / total) * 100, 2)

    top_bigrams = {
        phrase: round((count / total) * 100, 2)
        for phrase, count in bigram_counts.most_common(3)
        if count > 1
    }
    density.update(top_bigrams)
    return density


def _truncate_to_limit(text, limit):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    truncated = text[:limit].rsplit(" ", 1)[0]
    return truncated.rstrip(",.;:") + "..."


def _generate_meta_description(plain_text, limit=MEDIUM_META_LIMIT):
    sentences = _split_sentences(plain_text)
    if not sentences:
        return ""
    candidate = sentences[0]
    for s in sentences[1:]:
        if len(candidate) >= limit - 20:
            break
        candidate = f"{candidate} {s}"
    return _truncate_to_limit(candidate, limit)


def _call_ai(ai_manager, prompt, context=None, model=None):
    """Uniform call into the app's ai_manager.generate_content signature."""
    if ai_manager is None:
        raise ValueError("ai_manager is required")
    return ai_manager.generate_content(prompt, context, model)


def _extract_json(raw_text):
    """Best-effort extraction of a JSON object from an AI response."""
    if not raw_text:
        raise ValueError("empty AI response")
    text = raw_text.strip()
    text = re.sub(r"^```(json)?", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"```$", "", text.strip())
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError("could not extract JSON from AI response")


# ---------------------------------------------------------------------------
# 1. analyze_seo_deep
# ---------------------------------------------------------------------------

def _default_analysis():
    return {
        "keyword_density": {},
        "heading_structure": {
            "h1_count": 0,
            "h2_count": 0,
            "h3_count": 0,
            "hierarchy_valid": False,
            "recommendations": ["Unable to analyze headings."],
        },
        "meta_description": "",
        "readability_grade": 0.0,
        "content_gaps": ["Analysis failed; unable to determine content gaps."],
        "internal_linking_suggestions": [],
        "word_count": 0,
        "paragraph_count": 0,
        "avg_sentence_length": 0.0,
        "overall_score": 0,
    }


@_safe(_default_analysis)
def analyze_seo_deep(blog_text, target_keywords=None):
    """
    Perform a deep, rule-based SEO analysis of a blog post's text.

    Args:
        blog_text (str): The full markdown/plain text of the blog post.
        target_keywords (list[str] | None): Optional list of keywords the
            author is targeting, used to check coverage/density.

    Returns:
        dict: {
            "keyword_density": {keyword: percentage, ...},
            "heading_structure": {...},
            "meta_description": str,
            "readability_grade": float,
            "content_gaps": [str, ...],
            "internal_linking_suggestions": [str, ...],
            "word_count": int,
            "paragraph_count": int,
            "avg_sentence_length": float,
            "overall_score": int (0-100),
        }
    """
    if not blog_text or not blog_text.strip():
        return _default_analysis()

    plain_text = _strip_markdown(blog_text)
    words = _split_words(plain_text)
    word_count = len(words)

    paragraphs = [p for p in re.split(r"\n\s*\n", blog_text) if p.strip()]
    paragraph_count = len(paragraphs) or 1

    sentences = _split_sentences(plain_text)
    avg_sentence_length = round(word_count / len(sentences), 1) if sentences else 0.0

    keyword_density = _extract_keywords(plain_text, top_n=10)

    # Target keyword coverage check.
    target_keywords = target_keywords or []
    missing_targets = []
    for kw in target_keywords:
        kw_lower = kw.lower().strip()
        if kw_lower and kw_lower not in plain_text.lower():
            missing_targets.append(kw)

    # Heading structure.
    headings = _get_headings(blog_text)
    h1_count = sum(1 for lvl, _ in headings if lvl == 1)
    h2_count = sum(1 for lvl, _ in headings if lvl == 2)
    h3_count = sum(1 for lvl, _ in headings if lvl == 3)

    heading_recommendations = []
    if h1_count == 0:
        heading_recommendations.append("Add exactly one H1 title heading.")
    elif h1_count > 1:
        heading_recommendations.append("Use only one H1; demote extras to H2.")
    if h2_count == 0:
        heading_recommendations.append("Add H2 subheadings to break up content sections.")
    expected_h2 = max(1, word_count // 300)
    if h2_count < expected_h2:
        heading_recommendations.append(
            f"Consider adding more H2 subheadings (~1 per 300 words); "
            f"found {h2_count}, expected around {expected_h2}."
        )
    hierarchy_valid = h1_count == 1 and h2_count >= 1

    heading_structure = {
        "h1_count": h1_count,
        "h2_count": h2_count,
        "h3_count": h3_count,
        "hierarchy_valid": hierarchy_valid,
        "recommendations": heading_recommendations or ["Heading structure looks solid."],
    }

    meta_description = _generate_meta_description(plain_text)
    readability_grade = _flesch_kincaid_grade(plain_text)

    # Content gap detection.
    content_gaps = []
    if h1_count == 0:
        content_gaps.append("Missing a clear H1 / title heading.")
    if not re.search(r"\b(conclusion|takeaway|tl;?dr|summary)\b", plain_text, re.IGNORECASE):
        content_gaps.append("No conclusion, summary, or TL;DR section detected.")
    if "?" not in blog_text:
        content_gaps.append("No questions used — consider an FAQ or rhetorical question for engagement.")
    if not re.search(r"\[[^\]]*\]\([^)]*\)", blog_text):
        content_gaps.append("No links detected — add internal/external links for SEO authority.")
    if word_count < 600:
        content_gaps.append(f"Content is short ({word_count} words); aim for 1000+ for stronger SEO.")
    if missing_targets:
        content_gaps.append(
            "Target keywords not found in content: " + ", ".join(missing_targets)
        )
    if not re.search(r"!\[.*?\]\(.*?\)", blog_text):
        content_gaps.append("No images detected — add at least one relevant image.")
    if not content_gaps:
        content_gaps.append("No major content gaps detected.")

    # Internal linking suggestions: derive anchor text from top keywords/headings.
    internal_linking_suggestions = []
    for kw in list(keyword_density.keys())[:5]:
        internal_linking_suggestions.append(
            f"Link the phrase \"{kw}\" to a related article covering that topic."
        )
    for _, heading_text in headings[:3]:
        if heading_text:
            internal_linking_suggestions.append(
                f"Consider linking \"{heading_text}\" to a deeper-dive resource."
            )

    # Overall score (0-100), weighted heuristic.
    score = 100
    if h1_count != 1:
        score -= 15
    if h2_count < expected_h2:
        score -= 10
    if word_count < 600:
        score -= 15
    elif word_count < 1000:
        score -= 5
    if readability_grade > 12:
        score -= 10
    elif readability_grade > 9:
        score -= 5
    if avg_sentence_length > 25:
        score -= 10
    if missing_targets:
        score -= min(20, 5 * len(missing_targets))
    if "No links detected" in " ".join(content_gaps):
        score -= 10
    if "No conclusion" in " ".join(content_gaps):
        score -= 10
    score = max(0, min(100, score))

    return {
        "keyword_density": keyword_density,
        "heading_structure": heading_structure,
        "meta_description": meta_description,
        "readability_grade": readability_grade,
        "content_gaps": content_gaps,
        "internal_linking_suggestions": internal_linking_suggestions or [
            "Add 2-3 internal links to related content once available."
        ],
        "word_count": word_count,
        "paragraph_count": paragraph_count,
        "avg_sentence_length": avg_sentence_length,
        "overall_score": score,
    }


# ---------------------------------------------------------------------------
# 2. generate_seo_metadata
# ---------------------------------------------------------------------------

def _default_metadata():
    return {
        "title_variants": [],
        "meta_description": "",
        "focus_keywords": [],
        "tags": [],
        "og_description": "",
        "slug": "",
    }


@_safe(_default_metadata)
def generate_seo_metadata(blog_text, ai_manager, model=None):
    """
    Use the AI manager to generate SEO metadata for a blog post.

    Args:
        blog_text (str): Full text of the blog post.
        ai_manager: Object exposing generate_content(prompt, context, model).
        model (str | None): Optional model identifier to pass through.

    Returns:
        dict: {
            "title_variants": [str, str, str],  # each < 60 chars
            "meta_description": str,            # < 155 chars
            "focus_keywords": [str, ...],        # 5 keywords
            "tags": [str, ...],                  # 5 Medium tags
            "og_description": str,
            "slug": str,
        }
    """
    if not blog_text or not blog_text.strip():
        return _default_metadata()

    plain_text = _strip_markdown(blog_text)
    excerpt = plain_text[:4000]

    prompt = (
        "You are an SEO specialist optimizing a blog post for Medium and "
        "search engines. Based on the article content below, generate SEO "
        "metadata and respond with ONLY a valid JSON object (no markdown "
        "fences, no commentary) matching exactly this schema:\n\n"
        "{\n"
        '  "title_variants": ["title1", "title2", "title3"],\n'
        '  "meta_description": "string under 155 characters",\n'
        '  "focus_keywords": ["kw1", "kw2", "kw3", "kw4", "kw5"],\n'
        '  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],\n'
        '  "og_description": "string optimized for social sharing",\n'
        '  "slug": "url-friendly-slug"\n'
        "}\n\n"
        "Rules:\n"
        "- Each title_variant must be under 60 characters and compelling/clickable.\n"
        "- meta_description must be under 155 characters and include a primary keyword.\n"
        "- focus_keywords: exactly 5, ordered by relevance.\n"
        "- tags: exactly 5, short (1-3 words), suited to Medium's tag system.\n"
        "- slug: lowercase, hyphen-separated, no stopwords, under 60 characters.\n\n"
        f"ARTICLE CONTENT:\n{excerpt}"
    )

    raw = _call_ai(ai_manager, prompt, excerpt, model)
    data = _extract_json(raw)

    title_variants = [
        _truncate_to_limit(t, MEDIUM_TITLE_LIMIT)
        for t in (data.get("title_variants") or [])[:3]
    ]
    meta_description = _truncate_to_limit(
        data.get("meta_description", ""), MEDIUM_META_LIMIT
    )
    focus_keywords = list(data.get("focus_keywords") or [])[:5]
    tags = list(data.get("tags") or [])[:5]
    og_description = _truncate_to_limit(data.get("og_description", ""), 200)
    slug = re.sub(r"[^a-z0-9-]", "", data.get("slug", "").lower().replace(" ", "-"))

    result = {
        "title_variants": title_variants,
        "meta_description": meta_description,
        "focus_keywords": focus_keywords,
        "tags": tags,
        "og_description": og_description,
        "slug": slug,
    }

    # Fallback fill-ins if AI omitted fields.
    if not result["meta_description"]:
        result["meta_description"] = _generate_meta_description(plain_text)
    if not result["focus_keywords"]:
        result["focus_keywords"] = list(_extract_keywords(plain_text, top_n=5).keys())
    if not result["title_variants"]:
        first_heading = _get_headings(blog_text)
        fallback_title = first_heading[0][1] if first_heading else plain_text[:50]
        result["title_variants"] = [_truncate_to_limit(fallback_title, MEDIUM_TITLE_LIMIT)]

    return result


# ---------------------------------------------------------------------------
# 3. optimize_for_medium
# ---------------------------------------------------------------------------

def optimize_for_medium(blog_text, ai_manager, model=None):
    """
    Run an AI optimization pass tailored to Medium's algorithm and reader
    behavior: strategic subheadings, a tight opening hook, a TL;DR/key
    takeaway section, and engagement-oriented formatting.

    Args:
        blog_text (str): Original blog post text (markdown).
        ai_manager: Object exposing generate_content(prompt, context, model).
        model (str | None): Optional model identifier to pass through.

    Returns:
        str: The optimized blog post text. Falls back to the original
             blog_text if the AI call fails or returns nothing usable.
    """
    if not blog_text or not blog_text.strip():
        return blog_text or ""

    try:
        return _optimize_for_medium_impl(blog_text, ai_manager, model)
    except Exception as exc:  # noqa: BLE001 - defensive by design
        print(f"[seo_optimizer] optimize_for_medium failed: {exc}")
        return blog_text


def _optimize_for_medium_impl(blog_text, ai_manager, model=None):
    analysis = analyze_seo_deep(blog_text)
    needs_subheadings = analysis["heading_structure"]["h2_count"] < max(
        1, analysis["word_count"] // 300
    )
    has_tldr = not any(
        "no conclusion" in gap.lower() or "tl;dr" in gap.lower()
        for gap in analysis["content_gaps"]
    )

    first_para_match = re.split(r"\n\s*\n", blog_text.strip(), maxsplit=1)
    first_para = first_para_match[0] if first_para_match else ""
    first_para_sentences = len(_split_sentences(_strip_markdown(first_para)))
    hook_ok = first_para_sentences <= 3 and first_para_sentences > 0

    instructions = [
        "Rewrite and restructure the following Medium blog post to maximize "
        "reader engagement and algorithmic performance on Medium, while "
        "preserving all factual content, code blocks, and meaning.",
        "Requirements:",
    ]
    if needs_subheadings:
        instructions.append(
            "- Insert clear, benefit-driven H2 subheadings roughly every "
            "300 words if they are missing or too sparse."
        )
    if not hook_ok:
        instructions.append(
            "- Rewrite the opening paragraph so it is a strong hook of 3 "
            "sentences or fewer that immediately states the reader's benefit."
        )
    if not has_tldr:
        instructions.append(
            "- Add a short 'TL;DR' or 'Key Takeaways' section (bulleted) "
            "near the top, right after the introduction."
        )
    instructions.append(
        "- Improve pacing for Medium's read-ratio: short paragraphs (2-4 "
        "sentences), varied sentence length, and a strong concluding call "
        "to action or thought-provoking closer."
    )
    instructions.append(
        "- Do not remove existing code blocks, links, or images. Preserve "
        "markdown formatting."
    )
    instructions.append(
        "- Return ONLY the final optimized blog post text in markdown, with "
        "no explanations, preambles, or commentary."
    )

    prompt = "\n".join(instructions) + f"\n\nORIGINAL POST:\n{blog_text}"

    optimized = _call_ai(ai_manager, prompt, blog_text, model)
    optimized = (optimized or "").strip()

    if not optimized or len(optimized) < max(50, len(blog_text) // 4):
        # AI returned something too short/empty to trust — keep original.
        return blog_text

    return optimized


# ---------------------------------------------------------------------------
# 4. generate_content_brief
# ---------------------------------------------------------------------------

def _default_brief(topic=""):
    return {
        "topic": topic,
        "primary_keywords": [],
        "secondary_keywords": [],
        "outline": [],
        "competitor_angle_analysis": "",
        "target_word_count": 1200,
        "tone": "conversational and informative",
        "audience": "general technical readers",
    }


def generate_content_brief(topic, ai_manager, model=None):
    """
    Generate an AI-powered pre-writing content brief for a given topic.

    Args:
        topic (str): The subject/topic of the intended blog post (e.g. the
            YouTube video title or subject).
        ai_manager: Object exposing generate_content(prompt, context, model).
        model (str | None): Optional model identifier to pass through.

    Returns:
        dict: {
            "topic": str,
            "primary_keywords": [str, ...],
            "secondary_keywords": [str, ...],
            "outline": [{"heading": str, "level": "H2"|"H3", "notes": str}, ...],
            "competitor_angle_analysis": str,
            "target_word_count": int,
            "tone": str,
            "audience": str,
        }
    """
    if not topic or not topic.strip():
        return _default_brief(topic or "")

    try:
        return _generate_content_brief_impl(topic, ai_manager, model)
    except Exception as exc:  # noqa: BLE001 - defensive by design
        print(f"[seo_optimizer] generate_content_brief failed: {exc}")
        return _default_brief(topic)


def _generate_content_brief_impl(topic, ai_manager, model=None):
    prompt = (
        "You are a content strategist creating a pre-writing SEO brief for "
        "a Medium blog post. Respond with ONLY a valid JSON object (no "
        "markdown fences, no commentary) matching exactly this schema:\n\n"
        "{\n"
        '  "primary_keywords": ["kw1", "kw2"],\n'
        '  "secondary_keywords": ["kw1", "kw2", "kw3"],\n'
        '  "outline": [\n'
        '    {"heading": "string", "level": "H2", "notes": "what to cover"},\n'
        '    {"heading": "string", "level": "H3", "notes": "what to cover"}\n'
        "  ],\n"
        '  "competitor_angle_analysis": "string describing how competing '
        'articles typically cover this topic and how to differentiate",\n'
        '  "target_word_count": 1200,\n'
        '  "tone": "string describing recommended tone",\n'
        '  "audience": "string describing target audience"\n'
        "}\n\n"
        "Guidelines:\n"
        "- 2-3 primary keywords, 3-5 secondary/long-tail keywords.\n"
        "- Outline should have 4-8 entries mixing H2 and H3, in logical "
        "reading order, covering intro through conclusion/CTA.\n"
        "- competitor_angle_analysis should be 2-4 sentences of practical "
        "differentiation advice, not generic filler.\n"
        "- target_word_count should be realistic for the topic's depth "
        "(typically between 800 and 2500).\n\n"
        f"TOPIC: {topic}"
    )

    raw = _call_ai(ai_manager, prompt, topic, model)
    data = _extract_json(raw)

    brief = _default_brief(topic)
    brief["primary_keywords"] = list(data.get("primary_keywords") or [])
    brief["secondary_keywords"] = list(data.get("secondary_keywords") or [])

    outline_raw = data.get("outline") or []
    outline = []
    for item in outline_raw:
        if isinstance(item, dict):
            outline.append({
                "heading": str(item.get("heading", "")).strip(),
                "level": str(item.get("level", "H2")).strip().upper() or "H2",
                "notes": str(item.get("notes", "")).strip(),
            })
        elif isinstance(item, str):
            outline.append({"heading": item, "level": "H2", "notes": ""})
    brief["outline"] = outline

    brief["competitor_angle_analysis"] = str(
        data.get("competitor_angle_analysis", "")
    ).strip()

    try:
        brief["target_word_count"] = int(data.get("target_word_count", 1200))
    except (TypeError, ValueError):
        brief["target_word_count"] = 1200

    brief["tone"] = str(data.get("tone") or brief["tone"]).strip()
    brief["audience"] = str(data.get("audience") or brief["audience"]).strip()

    return brief
