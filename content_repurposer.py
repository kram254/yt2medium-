"""
content_repurposer.py

Content repurposing utilities for the yt2medium Flask app.

Inspired by the content-repurposer community skill, this module takes a
single long-form blog post (typically generated from a YouTube video
transcript) and repurposes it into multiple platform-native formats:
Twitter/X threads, LinkedIn posts, email newsletters, slide carousels,
and short-video scripts.

All functions are designed to be safe to call: on any failure (AI manager
error, malformed response, etc.) they catch the exception and return a
sensible, well-formed default rather than raising.

Integration contract:
    ai_manager.generate_content(prompt: str, context: str, model: str | None) -> str

The returned string from generate_content is expected to be plain text
(ideally JSON when we ask for JSON), which each function attempts to parse.
If parsing fails, a heuristic fallback builds the result from the raw text.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

# Words/phrases that are banned from all generated platform copy because they
# read as generic "AI slop" rather than natural, platform-native voice.
AI_SLOP_WORDS: List[str] = [
    "delve", "delve into", "leverage", "leveraging", "robust", "utilize",
    "utilizing", "foster", "fostering", "seamless", "seamlessly",
    "elevate", "elevating", "unlock", "unlocking", "unleash", "game-changer",
    "game changer", "in today's fast-paced world", "in this digital age",
    "landscape", "tapestry", "testament to", "navigate", "navigating",
    "underscore", "underscores", "paradigm", "synergy", "synergize",
    "holistic", "revolutionize", "revolutionizing", "cutting-edge",
    "at the end of the day", "it is important to note", "dive in",
    "dive deep", "embark", "embark on", "journey", "unparalleled",
    "boasts", "plethora", "myriad", "realm", "furthermore", "moreover",
    "in conclusion", "empower", "empowering", "harness", "harnessing",
]

_SLOP_BAN_INSTRUCTION = (
    "STRICT STYLE RULES:\n"
    "- Do NOT use any of these words/phrases (AI slop): "
    + ", ".join(AI_SLOP_WORDS) + ".\n"
    "- Write like a real person on this specific platform, not like a "
    "corporate blog or a press release.\n"
    "- Use short, punchy sentences. Avoid filler and throat-clearing.\n"
    "- No generic openers like 'In today's world' or 'Have you ever "
    "wondered'.\n"
)


def _safe_generate(
    ai_manager: Any,
    prompt: str,
    context: str,
    model: Optional[str],
    default_factory: Callable[[], Any],
) -> Any:
    """Call ai_manager.generate_content safely, falling back on any error.

    Returns the raw string response from the AI manager, or the result of
    default_factory() if the call fails or the ai_manager is unusable.
    """
    try:
        if ai_manager is None or not hasattr(ai_manager, "generate_content"):
            logger.warning("ai_manager is missing or invalid; using fallback")
            return default_factory()
        response = ai_manager.generate_content(prompt, context, model)
        if not response or not isinstance(response, str):
            logger.warning("ai_manager returned empty/invalid response; using fallback")
            return default_factory()
        return response
    except Exception:
        logger.exception("ai_manager.generate_content failed; using fallback")
        return default_factory()


def _extract_json(raw: str) -> Optional[Dict[str, Any]]:
    """Try to extract a JSON object from a raw AI response string."""
    if not raw:
        return None
    text = raw.strip()
    # Strip markdown code fences like ```json ... ```
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    else:
        # Fallback: find the first '{' and last '}' to grab the JSON blob.
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def _clean_blog_text(blog_text: Any) -> str:
    if not blog_text or not isinstance(blog_text, str):
        return ""
    return blog_text.strip()


def _truncate(text: str, max_len: int) -> str:
    if text is None:
        return ""
    text = str(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _first_sentence_snippet(blog_text: str, max_len: int = 200) -> str:
    if not blog_text:
        return "Here's what you need to know."
    sentences = re.split(r"(?<=[.!?])\s+", blog_text.strip())
    snippet = sentences[0] if sentences else blog_text
    return _truncate(snippet, max_len)


def _default_hashtags_from_text(blog_text: str, limit: int = 5) -> List[str]:
    """Very rough heuristic hashtag generator used only as a last-resort fallback."""
    words = re.findall(r"[A-Za-z]{4,}", blog_text or "")
    stop = {
        "this", "that", "with", "from", "your", "have", "will", "about",
        "into", "they", "them", "what", "when", "which", "there", "these",
        "those", "video", "youtube",
    }
    seen: List[str] = []
    for w in words:
        lw = w.lower()
        if lw in stop or lw in seen:
            continue
        seen.append(lw)
        if len(seen) >= limit:
            break
    return [f"#{w.capitalize()}" for w in seen] if seen else ["#Content"]


# ---------------------------------------------------------------------------
# 1. Twitter / X thread
# ---------------------------------------------------------------------------

def repurpose_to_twitter_thread(
    blog_text: str,
    ai_manager: Any,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Repurpose a blog post into a Twitter/X thread.

    Args:
        blog_text: Source blog post text.
        ai_manager: Object exposing generate_content(prompt, context, model).
        model: Optional model override passed through to ai_manager.

    Returns:
        dict with keys: thread (list[str]), hook_tweet (str),
        thread_count (int), hashtags (list[str]).

    Never raises: returns a sensible default structure on any failure.
    """
    blog_text = _clean_blog_text(blog_text)

    def default() -> str:
        hook = _first_sentence_snippet(blog_text)
        return json.dumps({
            "thread": [
                f"🧵 1/ {hook}",
                "2/ Here's the breakdown, thread style.",
                "3/ That's it. Follow for more like this.",
            ],
            "hook_tweet": f"🧵 1/ {hook}",
            "hashtags": _default_hashtags_from_text(blog_text),
        })

    prompt = (
        "You are repurposing a blog post into a native Twitter/X thread.\n\n"
        + _SLOP_BAN_INSTRUCTION
        + "\nTHREAD RULES:\n"
        "- The first tweet is the hook: it must stop the scroll and use the "
        "🧵 emoji to signal a thread.\n"
        "- Number every tweet like '1/', '2/', '3/' etc.\n"
        "- Each tweet must be under 280 characters, including the number "
        "and emoji.\n"
        "- Aim for 6-12 tweets covering the key ideas of the blog post, one "
        "idea per tweet.\n"
        "- End the final tweet with a clear call to action (follow, reply, "
        "or check out the link).\n\n"
        "Return ONLY valid JSON with this exact shape:\n"
        "{\n"
        '  "thread": ["tweet 1 text", "tweet 2 text", ...],\n'
        '  "hook_tweet": "the exact text of tweet 1",\n'
        '  "hashtags": ["#Tag1", "#Tag2"]\n'
        "}\n"
    )
    context = f"BLOG POST:\n{blog_text}"

    raw = _safe_generate(ai_manager, prompt, context, model, default)
    data = _extract_json(raw)

    if not data or "thread" not in data:
        data = _extract_json(default()) or {}

    thread = data.get("thread") or []
    if not isinstance(thread, list) or not thread:
        thread = [f"🧵 1/ {_first_sentence_snippet(blog_text)}"]
    thread = [_truncate(str(t), 280) for t in thread]

    hook_tweet = data.get("hook_tweet") or (thread[0] if thread else "")
    hook_tweet = _truncate(str(hook_tweet), 280)

    hashtags = data.get("hashtags")
    if not isinstance(hashtags, list) or not hashtags:
        hashtags = _default_hashtags_from_text(blog_text)

    return {
        "thread": thread,
        "hook_tweet": hook_tweet,
        "thread_count": len(thread),
        "hashtags": hashtags,
    }


# ---------------------------------------------------------------------------
# 2. LinkedIn post
# ---------------------------------------------------------------------------

def repurpose_to_linkedin_post(
    blog_text: str,
    ai_manager: Any,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Repurpose a blog post into a native LinkedIn post.

    Args:
        blog_text: Source blog post text.
        ai_manager: Object exposing generate_content(prompt, context, model).
        model: Optional model override passed through to ai_manager.

    Returns:
        dict with keys: post (str), hook_line (str), hashtags (list[str]),
        cta (str).

    Never raises: returns a sensible default structure on any failure.
    """
    blog_text = _clean_blog_text(blog_text)

    def default() -> str:
        hook = _first_sentence_snippet(blog_text)
        body = (
            f"{hook}\n\nHere's the short version of what I learned, broken "
            "down so you don't have to watch the whole thing.\n\n"
            "Save this if it's useful."
        )
        return json.dumps({
            "post": body,
            "hook_line": hook,
            "hashtags": _default_hashtags_from_text(blog_text),
            "cta": "Save this if it's useful.",
        })

    prompt = (
        "You are repurposing a blog post into a native LinkedIn post.\n\n"
        + _SLOP_BAN_INSTRUCTION
        + "\nLINKEDIN RULES:\n"
        "- The first line must stop the scroll — it's the only part shown "
        "before the 'see more' cutoff, so make it count on its own.\n"
        "- Use short paragraphs and line breaks for scannability (LinkedIn "
        "readers skim).\n"
        "- Tone: professional but human, not corporate. Write like a real "
        "person sharing a real insight, not a press release.\n"
        "- Keep the whole post under 3000 characters.\n"
        "- End with one clear call to action (comment, share, follow, or "
        "check the link).\n\n"
        "Return ONLY valid JSON with this exact shape:\n"
        "{\n"
        '  "post": "full post text with \\n line breaks",\n'
        '  "hook_line": "the exact first line of the post",\n'
        '  "hashtags": ["#Tag1", "#Tag2"],\n'
        '  "cta": "the closing call to action line"\n'
        "}\n"
    )
    context = f"BLOG POST:\n{blog_text}"

    raw = _safe_generate(ai_manager, prompt, context, model, default)
    data = _extract_json(raw)

    if not data or "post" not in data:
        data = _extract_json(default()) or {}

    post = _truncate(str(data.get("post") or default()), 3000)
    hook_line = data.get("hook_line") or (post.split("\n")[0] if post else "")
    hashtags = data.get("hashtags")
    if not isinstance(hashtags, list) or not hashtags:
        hashtags = _default_hashtags_from_text(blog_text)
    cta = data.get("cta") or "Let me know your thoughts in the comments."

    return {
        "post": post,
        "hook_line": str(hook_line),
        "hashtags": hashtags,
        "cta": str(cta),
    }


# ---------------------------------------------------------------------------
# 3. Email newsletter
# ---------------------------------------------------------------------------

def repurpose_to_newsletter(
    blog_text: str,
    ai_manager: Any,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Repurpose a blog post into an email newsletter.

    Args:
        blog_text: Source blog post text.
        ai_manager: Object exposing generate_content(prompt, context, model).
        model: Optional model override passed through to ai_manager.

    Returns:
        dict with keys: subject_line (str), preview_text (str), body (str,
        markdown), cta_button_text (str), cta_url_placeholder (str).

    Never raises: returns a sensible default structure on any failure.
    """
    blog_text = _clean_blog_text(blog_text)

    def default() -> str:
        hook = _first_sentence_snippet(blog_text, 80)
        return json.dumps({
            "subject_line": _truncate(hook, 50),
            "preview_text": _truncate(f"Quick take: {hook}", 90),
            "body": (
                f"Hey,\n\n{hook}\n\nHere's the quick breakdown:\n\n"
                "- Key point one\n- Key point two\n- Key point three\n\n"
                "That's the gist of it. Full details below."
            ),
            "cta_button_text": "Read the full post",
            "cta_url_placeholder": "[LINK]",
        })

    prompt = (
        "You are repurposing a blog post into a short email newsletter.\n\n"
        + _SLOP_BAN_INSTRUCTION
        + "\nNEWSLETTER RULES:\n"
        "- Conversational tone, like an email from a person, not a "
        "marketing blast.\n"
        "- Subject line under 50 characters, no clickbait, no emoji spam.\n"
        "- Preview text under 90 characters, complements the subject line "
        "(doesn't repeat it).\n"
        "- Body should be scannable: short paragraphs, bullet points where "
        "useful, written in markdown that's ready to convert to HTML.\n"
        "- Exactly one clear call to action in the body, plus a short CTA "
        "button label.\n"
        "- Use the literal placeholder [LINK] anywhere a URL is needed.\n\n"
        "Return ONLY valid JSON with this exact shape:\n"
        "{\n"
        '  "subject_line": "under 50 chars",\n'
        '  "preview_text": "under 90 chars",\n'
        '  "body": "markdown newsletter body using [LINK] as needed",\n'
        '  "cta_button_text": "short button label"\n'
        "}\n"
    )
    context = f"BLOG POST:\n{blog_text}"

    raw = _safe_generate(ai_manager, prompt, context, model, default)
    data = _extract_json(raw)

    if not data or "body" not in data:
        data = _extract_json(default()) or {}

    subject_line = _truncate(str(data.get("subject_line") or "New post is up"), 50)
    preview_text = _truncate(str(data.get("preview_text") or "Here's the quick version."), 90)
    body = str(data.get("body") or default())
    cta_button_text = str(data.get("cta_button_text") or "Read more")

    return {
        "subject_line": subject_line,
        "preview_text": preview_text,
        "body": body,
        "cta_button_text": cta_button_text,
        "cta_url_placeholder": "[LINK]",
    }


# ---------------------------------------------------------------------------
# 4. Slide carousel
# ---------------------------------------------------------------------------

def repurpose_to_carousel(
    blog_text: str,
    ai_manager: Any,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Repurpose a blog post into a slide carousel (Instagram/LinkedIn style).

    Args:
        blog_text: Source blog post text.
        ai_manager: Object exposing generate_content(prompt, context, model).
        model: Optional model override passed through to ai_manager.

    Returns:
        dict with keys: slides (list[dict]), slide_count (int),
        cover_slide (dict), cta_slide (dict).
        Each slide dict has: slide_number, headline, body, visual_suggestion.

    Never raises: returns a sensible default structure on any failure.
    """
    blog_text = _clean_blog_text(blog_text)

    def default() -> str:
        hook = _first_sentence_snippet(blog_text, 60)
        slides = [
            {
                "slide_number": 1,
                "headline": hook,
                "body": "Swipe to see the breakdown.",
                "visual_suggestion": "Bold title text on a solid color background.",
            },
            {
                "slide_number": 2,
                "headline": "The main idea",
                "body": "One core takeaway from the post.",
                "visual_suggestion": "Simple icon or illustration supporting the idea.",
            },
            {
                "slide_number": 3,
                "headline": "That's the gist",
                "body": "Follow for more breakdowns like this.",
                "visual_suggestion": "Clear call-to-action graphic with handle/logo.",
            },
        ]
        return json.dumps({"slides": slides})

    prompt = (
        "You are repurposing a blog post into a slide carousel (like "
        "Instagram/LinkedIn carousel posts).\n\n"
        + _SLOP_BAN_INSTRUCTION
        + "\nCAROUSEL RULES:\n"
        "- One idea per slide. Never cram multiple ideas onto one slide.\n"
        "- Think visual-first: each slide needs a visual_suggestion "
        "describing what should appear on it (icon, photo style, chart, "
        "bold text layout, etc.).\n"
        "- Headlines should be large-text friendly: short, punchy, no more "
        "than ~8 words.\n"
        "- Body text per slide should be brief (1-3 short sentences max).\n"
        "- Aim for 8-12 slides total: 1 cover/hook slide, several content "
        "slides, and 1 final CTA slide.\n\n"
        "Return ONLY valid JSON with this exact shape:\n"
        "{\n"
        '  "slides": [\n'
        '    {"slide_number": 1, "headline": "...", "body": "...", '
        '"visual_suggestion": "..."},\n'
        "    ...\n"
        "  ]\n"
        "}\n"
    )
    context = f"BLOG POST:\n{blog_text}"

    raw = _safe_generate(ai_manager, prompt, context, model, default)
    data = _extract_json(raw)

    if not data or "slides" not in data:
        data = _extract_json(default()) or {}

    slides_raw = data.get("slides") or []
    if not isinstance(slides_raw, list) or not slides_raw:
        slides_raw = json.loads(default())["slides"]

    slides: List[Dict[str, Any]] = []
    for i, s in enumerate(slides_raw, start=1):
        if not isinstance(s, dict):
            continue
        slides.append({
            "slide_number": s.get("slide_number", i),
            "headline": str(s.get("headline", "")),
            "body": str(s.get("body", "")),
            "visual_suggestion": str(s.get("visual_suggestion", "")),
        })

    if not slides:
        slides = json.loads(default())["slides"]

    cover_slide = slides[0]
    cta_slide = slides[-1]

    return {
        "slides": slides,
        "slide_count": len(slides),
        "cover_slide": cover_slide,
        "cta_slide": cta_slide,
    }


# ---------------------------------------------------------------------------
# 5. Short-form video script
# ---------------------------------------------------------------------------

def repurpose_to_short_video_script(
    blog_text: str,
    ai_manager: Any,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Repurpose a blog post into a short-form video script (TikTok/Reels/Shorts).

    Args:
        blog_text: Source blog post text.
        ai_manager: Object exposing generate_content(prompt, context, model).
        model: Optional model override passed through to ai_manager.

    Returns:
        dict with keys: hook (str), body (str), cta (str),
        duration_estimate (str), b_roll_suggestions (list[str]).

    Never raises: returns a sensible default structure on any failure.
    """
    blog_text = _clean_blog_text(blog_text)

    def default() -> str:
        hook = _first_sentence_snippet(blog_text, 60)
        return json.dumps({
            "hook": f"[0:00-0:03] {hook}",
            "body": (
                "[0:03-0:45] Here's the quick breakdown of what this is "
                "about and why it matters.\n"
                "[0:45-0:55] The key takeaway you should remember."
            ),
            "cta": "[0:55-1:00] Follow for more like this.",
            "duration_estimate": "60-90 seconds",
            "b_roll_suggestions": [
                "Close-up talking head shot",
                "Text overlay of the key point",
                "Quick cut to a relevant screenshot or clip",
            ],
        })

    prompt = (
        "You are repurposing a blog post into a short-form video script "
        "(TikTok/Instagram Reels/YouTube Shorts style).\n\n"
        + _SLOP_BAN_INSTRUCTION
        + "\nSCRIPT RULES:\n"
        "- Write for speaking out loud, not for reading. Use natural, "
        "spoken phrasing and contractions.\n"
        "- The hook must grab attention in the first 3 seconds — no slow "
        "windups.\n"
        "- Include rough timestamps in the body (e.g. [0:03-0:20]) to pace "
        "the script.\n"
        "- Target a total runtime of 60-90 seconds.\n"
        "- Keep it punchy: short sentences, no filler, no long explanations.\n"
        "- Suggest concrete b-roll/visual cutaways that support the "
        "narration.\n\n"
        "Return ONLY valid JSON with this exact shape:\n"
        "{\n"
        '  "hook": "[0:00-0:03] hook line",\n'
        '  "body": "timestamped script for the main content",\n'
        '  "cta": "closing call to action line",\n'
        '  "duration_estimate": "60-90 seconds",\n'
        '  "b_roll_suggestions": ["suggestion 1", "suggestion 2"]\n'
        "}\n"
    )
    context = f"BLOG POST:\n{blog_text}"

    raw = _safe_generate(ai_manager, prompt, context, model, default)
    data = _extract_json(raw)

    if not data or "body" not in data:
        data = _extract_json(default()) or {}

    hook = str(data.get("hook") or "[0:00-0:03] Here's what you need to know.")
    body = str(data.get("body") or "Main content goes here.")
    cta = str(data.get("cta") or "Follow for more.")
    duration_estimate = str(data.get("duration_estimate") or "60-90 seconds")

    b_roll = data.get("b_roll_suggestions")
    if not isinstance(b_roll, list) or not b_roll:
        b_roll = ["Talking head shot", "Text overlay of key point"]
    b_roll = [str(x) for x in b_roll]

    return {
        "hook": hook,
        "body": body,
        "cta": cta,
        "duration_estimate": duration_estimate,
        "b_roll_suggestions": b_roll,
    }


# ---------------------------------------------------------------------------
# 6. Repurpose to all formats
# ---------------------------------------------------------------------------

def repurpose_all(
    blog_text: str,
    ai_manager: Any,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Repurpose a blog post into every supported platform format.

    Runs each individual repurpose_* function and collects the results.
    Each format is generated independently and wrapped in its own try/except
    so that a single failing format (e.g. an AI manager error) does not
    prevent the other formats from being returned.

    Args:
        blog_text: Source blog post text.
        ai_manager: Object exposing generate_content(prompt, context, model).
        model: Optional model override passed through to ai_manager.

    Returns:
        dict with keys: twitter_thread, linkedin_post, newsletter,
        carousel, short_video_script — plus an "errors" dict mapping
        any failed format name to its error message (empty if all
        succeeded).
    """
    blog_text = _clean_blog_text(blog_text)

    formats: Dict[str, Callable[[], Dict[str, Any]]] = {
        "twitter_thread": lambda: repurpose_to_twitter_thread(blog_text, ai_manager, model),
        "linkedin_post": lambda: repurpose_to_linkedin_post(blog_text, ai_manager, model),
        "newsletter": lambda: repurpose_to_newsletter(blog_text, ai_manager, model),
        "carousel": lambda: repurpose_to_carousel(blog_text, ai_manager, model),
        "short_video_script": lambda: repurpose_to_short_video_script(blog_text, ai_manager, model),
    }

    results: Dict[str, Any] = {}
    errors: Dict[str, str] = {}

    for name, fn in formats.items():
        try:
            results[name] = fn()
        except Exception as exc:  # noqa: BLE001 - intentional catch-all per format
            logger.exception("repurpose_all: format '%s' failed", name)
            errors[name] = str(exc)
            results[name] = None

    results["errors"] = errors
    return results
