"""
No AI Slop Filter — Post-processing pass for generated blog content.
Based on https://github.com/petergyang/no-ai-slop

Removes 20+ patterns of AI slop from writing without flattening
the writer's personal voice. Applied as the final step in the
blog generation pipeline.
"""

# ── Banned words ──────────────────────────────────────────────
BANNED_WORDS = [
    "delve", "foster", "leverage", "utilize", "facilitate", "empower",
    "streamline", "robust", "cutting-edge", "paradigm shift", "game changer",
    "this is huge", "this changes everything", "tapestry", "realm", "beacon",
    "multifaceted", "meticulous", "intricate", "paramount", "transformative",
    "elevate", "embark", "supercharge", "harness", "ever-evolving",
]

# ── Often-empty adverbs (cut when they add nothing) ──────────
EMPTY_ADVERBS = [
    "just", "literally", "honestly", "simply", "actually", "truly",
    "fundamentally", "importantly", "crucially", "inherently", "inevitably",
]

# ── Often-empty phrases ─────────────────────────────────────
EMPTY_PHRASES = [
    "it's worth noting", "it's important to note", "at the end of the day",
    "when it comes to", "at its core", "in today's world", "in the age of",
    "in the world of", "the reality is", "the truth is", "in terms of",
    "with regard to", "in order to", "going forward", "in this article",
    "let's dive in", "let's dive into", "in today's fast-paced world",
    "in the ever-evolving landscape",
]

# ── The full no-ai-slop editing prompt ───────────────────────
SLOP_FILTER_PROMPT = """You are a sharp human editor applying the No AI Slop ruleset.
Your job: remove AI writing patterns from this blog post while preserving
the writer's point, voice, and all concrete facts. Make the minimum
effective edit — do NOT compress, shorten, or rewrite sections that
already sound human.

## Editing principles (follow all)

- Preserve the writer's vocabulary, cadence, bluntness, humor, and level
  of polish. Leave strong human sentences alone.
- Lead with the point when the setup adds nothing. Keep personal asides
  that create context or character.
- Use active voice. Make verbs do the work. "Made a decision" → "decided."
- Be concrete and specific. Replace abstractions with facts, numbers,
  names, mechanisms.
- Portability test: if a sentence could move unchanged to any other
  subject, it is filler. Cut it or make it specific.
- Show, don't tell the reader what to think. Cut commentary that labels
  a point important or surprising instead of demonstrating why.

## Words to remove or replace

Banned outright: delve, foster, leverage, utilize, facilitate, empower,
streamline, robust, cutting-edge, paradigm shift, game changer,
tapestry, realm, beacon, multifaceted, meticulous, intricate, paramount,
transformative, elevate, embark, supercharge, harness, ever-evolving.

Cut when empty: just, literally, honestly, simply, actually, truly,
fundamentally, importantly, crucially, inherently, inevitably.

Cut when they delay the point: it's worth noting, it's important to note,
at the end of the day, when it comes to, at its core, in today's world,
in the age of, in the world of, the reality is, the truth is, in terms of,
with regard to, in order to, going forward, in this article, let's dive in.

## Patterns to cut

1. Binary contrasts — "It's not X. It's Y." → state Y directly.
2. Throat-clearing openers — "Here's the thing," "Let me be clear" → cut.
3. Faux-insight setups — "What nobody tells you," "The part everyone
   misses" → cut the setup, keep the claim.
4. Colon reveals — "The best part: it learns." → rewrite as plain sentence.
5. Superficial analysis — trailing "-ing" clauses: "highlighting,"
   "underscoring," "showcasing" → replace with concrete consequence.
6. Importance puffery — "marks a pivotal moment," "a testament to" →
   state the fact and let the reader judge.
7. Interpretive metadiscourse — "That last part matters more than it
   sounds," "The key point is" → cut.
8. Weasel attribution — "experts agree," "studies show" → name the
   source or cut the claim.
9. Synonym cycling — if the clear word is right, repeat it.
10. Dramatic fragmentation — "X. And Y. And Z." → use complete sentences.
11. Fake-profound kickers — delete the cute metaphor ending. End on the
    last concrete sentence.
12. Summary-recap endings — cut "In conclusion," "Ultimately," "Overall."
    End on concrete point or next action.
13. Em dashes and en dashes — REMOVE ALL. Replace every — and – with
    ' - ' (spaced hyphen). Zero em dashes in the final output. This is
    non-negotiable.
14. Formatting slop — remove emoji in headings, decorative bold,
    bullets that should be prose, headers over tiny sections.

## Self-check before returning

- Does the edit preserve the writer's point without adding claims?
- Are banned words removed?
- Are AI patterns cut?
- Does every sentence pass the portability test?
- Would the writer recognize this as their own voice?
- Is the piece the same length or longer (no aggressive compression)?

## Instructions

Edit the blog post below. Return ONLY the edited Markdown. No
explanations, no "What changed" section, no meta-commentary.

---

BLOG POST TO EDIT:

{blog_text}
"""


def strip_em_dashes(text):
    """
    Remove all em dashes (—) and en dashes (–) from text.
    Replaces them with ' - ' (spaced hyphen) for readability,
    collapsing any resulting double spaces.

    This runs as the absolute last step in the pipeline so no
    em dashes survive — not from the original content, not from
    the AI slop filter, not from any enhancement pass.
    """
    if not text:
        return text
    import re
    # Replace em dash and en dash with spaced hyphen
    text = text.replace('—', ' - ')
    text = text.replace('–', ' - ')
    # Also catch Unicode variants
    text = text.replace('—', ' - ')  # em dash
    text = text.replace('–', ' - ')  # en dash
    # Collapse multiple spaces
    text = re.sub(r'  +', ' ', text)
    # Clean up " - - " that might result from adjacent dashes
    text = text.replace(' - - ', ' - ')
    return text


def apply_slop_filter(blog_text, ai_manager, model=None):
    """
    Apply the no-ai-slop filter to a blog post using the AI manager.

    Args:
        blog_text: The generated blog post text (Markdown)
        ai_manager: The app's AI manager instance
        model: Optional model override

    Returns:
        Cleaned blog text with AI slop patterns removed
    """
    if not blog_text or len(blog_text) < 100:
        return blog_text

    try:
        prompt = SLOP_FILTER_PROMPT.format(blog_text=blog_text)
        result = ai_manager.generate_content(prompt, model=model)

        if result and len(result) > len(blog_text) * 0.5:
            # Sanity check: the filtered version should not be drastically shorter
            print(f"[SLOP_FILTER] Applied: {len(blog_text)} → {len(result)} chars")
            return result
        else:
            print(f"[SLOP_FILTER] Result too short or empty, keeping original")
            return blog_text
    except Exception as e:
        print(f"[SLOP_FILTER] Error: {e}")
        return blog_text


def quick_slop_check(text):
    """
    Quick non-AI check: count how many banned words/phrases appear.
    Returns a score (0 = clean, higher = more slop) and list of found patterns.
    Useful for deciding whether to run the full AI filter.
    """
    if not text:
        return 0, []

    text_lower = text.lower()
    found = []

    for word in BANNED_WORDS:
        if word in text_lower:
            found.append(f"banned: {word}")

    for phrase in EMPTY_PHRASES:
        if phrase in text_lower:
            found.append(f"empty phrase: {phrase}")

    return len(found), found
