"""
Copywriting Enhancer — Headline, CTA, and hook optimization.

Inspired by marketingskills community skill's copywriting frameworks.
Applies proven persuasion and conversion principles to optimize
blog post headlines, opening hooks, and calls-to-action.
"""


# ── Headline formulas ────────────────────────────────────────

HEADLINE_FORMULAS = [
    "How to {benefit} (Without {pain_point})",
    "{Number} {subject} That {outcome}",
    "The {adjective} Guide to {topic}",
    "Why {common_belief} Is Wrong (And What to Do Instead)",
    "{subject}: What {experts} Won't Tell You",
    "I {did_thing} for {time_period}. Here's What Happened.",
    "Stop {bad_habit}. Start {good_habit}.",
    "{outcome} in {time_frame}: A {subject} Breakdown",
]

# ── CTA frameworks ───────────────────────────────────────────

CTA_FRAMEWORKS = {
    "value_first": "Lead with what the reader gets, not what you want them to do. "
                   "'Get the full checklist' beats 'Subscribe to my newsletter'.",
    "curiosity_gap": "Open a loop the reader wants to close. "
                     "'See what 500 developers chose' beats 'Read the survey results'.",
    "social_proof": "Reference the crowd. '12,000 developers already...' "
                    "or 'Join the engineers who...'",
    "urgency_honest": "Time-bound without being sleazy. 'This pricing ends Friday' is fine. "
                      "'Act now before it's too late!!!' is not.",
    "reciprocity": "Give something first, then ask. Share the best insight in the post, "
                   "then offer more depth via the CTA.",
}

# ── Banned words in headlines ────────────────────────────────

HEADLINE_BANNED = [
    "game-changing", "revolutionary", "mind-blowing", "ultimate", "insane",
    "you won't believe", "shocking", "epic", "killer", "ninja", "guru",
    "hack", "secret", "crushing it", "10x", "disruptive",
]


def generate_headline_variants(blog_text, original_title, ai_manager, count=5, model=None):
    """
    Generate optimized headline variants using proven copywriting formulas.

    Args:
        blog_text: The blog post content
        original_title: The current title
        ai_manager: AI manager instance
        count: Number of variants to generate
        model: Optional model override

    Returns:
        dict with:
            - variants: list of {headline, formula_used, estimated_ctr, reasoning}
            - original_score: score of the original headline
            - best_pick: index of the recommended headline
    """
    try:
        banned_str = ", ".join(HEADLINE_BANNED)
        formulas_str = "\n".join(f"  - {f}" for f in HEADLINE_FORMULAS)

        prompt = f"""You are an expert copywriter optimizing blog headlines for Medium.

ORIGINAL HEADLINE: {original_title}
BLOG EXCERPT: {blog_text[:800]}

PROVEN HEADLINE FORMULAS (use as inspiration, not templates):
{formulas_str}

BANNED WORDS (never use): {banned_str}

Generate {count} headline variants. Each must:
1. Be under 60 characters for SEO
2. Communicate a clear benefit or spark curiosity
3. Be specific — name the tool, framework, number, or outcome
4. Sound human, not clickbait
5. Work for a technical audience (developers, ML engineers)

Also score the original headline on a 1-10 scale.

Return ONLY a JSON object (no markdown fences):
{{
    "original_score": 7,
    "original_feedback": "one sentence on what works and what doesn't",
    "variants": [
        {{
            "headline": "the headline text",
            "formula_used": "which copywriting principle it uses",
            "estimated_ctr": "low|medium|high",
            "reasoning": "why this works (one sentence)"
        }}
    ],
    "best_pick": 0
}}"""

        result = ai_manager.generate_content(prompt, model=model)

        import json
        parsed = _parse_json(result)

        if parsed and isinstance(parsed.get("variants"), list):
            return parsed
        return _fallback_headlines(original_title)

    except Exception as e:
        print(f"[COPYWRITING] Headline generation error: {e}")
        return _fallback_headlines(original_title)


def optimize_opening_hook(blog_text, ai_manager, model=None):
    """
    Rewrite the opening paragraph to maximize reader retention.

    The first 2-3 sentences determine if someone keeps reading on Medium.
    This function rewrites the opening using proven hook techniques.

    Returns:
        dict with:
            - original_hook: the current opening
            - optimized_hook: the rewritten opening
            - technique_used: which hook technique was applied
            - retention_estimate: "low" | "medium" | "high"
    """
    try:
        # Extract first paragraph
        paragraphs = [p.strip() for p in blog_text.split("\n\n") if p.strip()]
        # Skip title line if it starts with #
        first_para = ""
        for p in paragraphs:
            if not p.startswith("#"):
                first_para = p
                break
        if not first_para and paragraphs:
            first_para = paragraphs[0]

        prompt = f"""You are a Medium editor optimizing the opening hook of a blog post.

CURRENT OPENING:
{first_para}

REST OF POST (for context):
{blog_text[:1500]}

HOOK TECHNIQUES (pick the best one for this content):
1. **Bold claim**: Open with a counterintuitive statement that makes the reader think "wait, really?"
2. **Specific number**: Lead with a concrete stat or result ("I cut deploy time from 40 minutes to 4")
3. **Pain point**: Start with a frustration the reader recognizes ("You've been debugging this for 3 hours...")
4. **Story**: Begin with a micro-narrative (2-3 sentences) that sets up the topic
5. **Question**: Ask something the reader genuinely wants answered (not rhetorical fluff)
6. **Contrast**: Show the before/after or old-way/new-way in one sentence

RULES:
- Maximum 3 sentences
- No throat-clearing ("In today's world...", "Let me tell you...")
- No AI slop words (delve, leverage, robust, utilize, foster, empower)
- The reader should know what the post is about AND want to keep reading
- Be specific to THIS topic, not generic

Return ONLY JSON (no markdown fences):
{{
    "original_hook": "{first_para[:200]}...",
    "optimized_hook": "the rewritten opening (2-3 sentences)",
    "technique_used": "which hook technique was applied",
    "retention_estimate": "low|medium|high"
}}"""

        result = ai_manager.generate_content(prompt, model=model)
        parsed = _parse_json(result)

        if parsed and parsed.get("optimized_hook"):
            return parsed
        return {
            "original_hook": first_para[:200],
            "optimized_hook": first_para,
            "technique_used": "none (kept original)",
            "retention_estimate": "medium"
        }

    except Exception as e:
        print(f"[COPYWRITING] Hook optimization error: {e}")
        return {
            "original_hook": "",
            "optimized_hook": "",
            "technique_used": "error",
            "retention_estimate": "unknown"
        }


def optimize_cta(blog_text, current_cta=None, ai_manager=None, model=None):
    """
    Generate or optimize the blog post's call-to-action.

    Returns:
        dict with:
            - cta_options: list of 3 CTA variants
            - framework_used: which CTA framework each uses
            - placement_suggestion: where in the post to place the CTA
    """
    try:
        frameworks_str = "\n".join(f"  - {k}: {v}" for k, v in CTA_FRAMEWORKS.items())

        prompt = f"""You are a conversion copywriter optimizing the CTA for a Medium blog post.

BLOG EXCERPT: {blog_text[:1000]}
CURRENT CTA: {current_cta or '(none)'}

CTA FRAMEWORKS:
{frameworks_str}

Generate 3 CTA variants, each using a different framework. Each CTA should:
1. Be 1-2 sentences max
2. Feel natural at the end of the article (not salesy)
3. Give the reader a clear next action
4. Work for a technical audience

Return ONLY JSON (no markdown fences):
{{
    "cta_options": [
        {{
            "cta_text": "the call to action text",
            "framework": "which framework it uses",
            "strength": "low|medium|high"
        }}
    ],
    "placement_suggestion": "end_of_post|after_key_insight|both"
}}"""

        result = ai_manager.generate_content(prompt, model=model)
        parsed = _parse_json(result)

        if parsed and isinstance(parsed.get("cta_options"), list):
            return parsed
        return {"cta_options": [], "placement_suggestion": "end_of_post"}

    except Exception as e:
        print(f"[COPYWRITING] CTA optimization error: {e}")
        return {"cta_options": [], "placement_suggestion": "end_of_post"}


def enhance_post_copywriting(blog_text, title, ai_manager, model=None):
    """
    Full copywriting enhancement: headlines + hook + CTA in one call.

    Returns:
        dict with headlines, hook, and cta results combined.
    """
    results = {}

    try:
        results["headlines"] = generate_headline_variants(
            blog_text, title, ai_manager, count=5, model=model
        )
    except Exception as e:
        print(f"[COPYWRITING] Headlines failed: {e}")
        results["headlines"] = _fallback_headlines(title)

    try:
        results["hook"] = optimize_opening_hook(blog_text, ai_manager, model=model)
    except Exception as e:
        print(f"[COPYWRITING] Hook failed: {e}")
        results["hook"] = {"optimized_hook": "", "technique_used": "error"}

    try:
        results["cta"] = optimize_cta(blog_text, ai_manager=ai_manager, model=model)
    except Exception as e:
        print(f"[COPYWRITING] CTA failed: {e}")
        results["cta"] = {"cta_options": []}

    return results


# ── Helpers ──────────────────────────────────────────────────

def _parse_json(text):
    """Try to parse JSON from AI response, with fallback extraction."""
    import json
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        if isinstance(text, str):
            first = text.find("{")
            last = text.rfind("}")
            if first != -1 and last > first:
                try:
                    return json.loads(text[first:last + 1])
                except Exception:
                    pass
    return None


def _fallback_headlines(title):
    """Return a minimal fallback result."""
    return {
        "original_score": 5,
        "original_feedback": "Could not generate variants",
        "variants": [{"headline": title, "formula_used": "original",
                       "estimated_ctr": "medium", "reasoning": "Kept original"}],
        "best_pick": 0
    }
