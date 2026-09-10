"""
Cover Image Generator — Smart cover image prompt generation for blog posts.

Inspired by smart-illustrator, image_gen, and blog-cover-image-cli community skills.
Generates platform-specific cover image prompts with typography guidance,
and in-article diagram/illustration suggestions.
"""


# ── Platform presets ─────────────────────────────────────────

PLATFORM_SPECS = {
    "medium": {
        "width": 1400,
        "height": 788,
        "aspect": "16:9",
        "style": "Clean, editorial, minimal text overlay. Medium readers expect "
                 "professional photography or crisp illustrations — not stock-photo clichés.",
        "text_safe_zone": "center 60% of image for title overlay"
    },
    "linkedin": {
        "width": 1200,
        "height": 627,
        "aspect": "1.91:1",
        "style": "Professional, bold, clean typography. LinkedIn favors high-contrast "
                 "images with clear subject matter. Avoid busy backgrounds.",
        "text_safe_zone": "left-aligned with 20% margin"
    },
    "twitter": {
        "width": 1200,
        "height": 675,
        "aspect": "16:9",
        "style": "Eye-catching, bold colors, minimal text. Must read at thumbnail size. "
                 "High contrast, simple composition.",
        "text_safe_zone": "center, large text only"
    },
    "devto": {
        "width": 1000,
        "height": 420,
        "aspect": "1000:420",
        "style": "Developer-friendly: dark themes, code aesthetics, terminal-inspired, "
                 "or clean flat illustrations. Technical but approachable.",
        "text_safe_zone": "center with generous padding"
    },
    "youtube_thumbnail": {
        "width": 1280,
        "height": 720,
        "aspect": "16:9",
        "style": "High energy, expressive face or bold icon, 3-5 word text overlay in "
                 "thick sans-serif. Must pop at 120x68px thumbnail size.",
        "text_safe_zone": "avoid bottom-right 20% (timestamp overlay)"
    }
}

# ── Visual style presets ─────────────────────────────────────

VISUAL_STYLES = {
    "editorial": "Clean white background, sophisticated typography, muted color palette. "
                 "Think New York Times or The Verge feature art.",
    "technical": "Dark background (#1a1a2e or #0d1117), code-editor inspired, syntax-highlighted "
                 "snippets, terminal green or VS Code blue accents. Circuit patterns optional.",
    "minimal": "Single focal point, generous whitespace, one accent color, "
               "geometric shapes or abstract forms. Less is more.",
    "vibrant": "Bold gradients (purple-to-blue, orange-to-pink), floating 3D elements, "
               "modern tech aesthetic. Energetic but not cluttered.",
    "illustration": "Flat vector illustration style, limited color palette (4-5 colors), "
                    "isometric or 2D characters/objects. Friendly and approachable.",
    "photographic": "High-quality photography style — dramatic lighting, shallow depth of field, "
                    "real-world objects or workspaces. No obvious AI artifacts.",
    "data_viz": "Charts, graphs, dashboards as hero visual. Clean axes, clear labels, "
                "professional color scheme. Data tells the story."
}


def detect_visual_style(blog_text, title=""):
    """
    Analyze the blog content to suggest the best visual style.

    Returns:
        tuple: (style_key, reasoning)
    """
    text_lower = (blog_text + " " + title).lower()

    # Code-heavy content
    code_markers = ["```", "def ", "import ", "const ", "function ", "class ", "npm ", "pip "]
    code_count = sum(1 for m in code_markers if m in text_lower)
    if code_count >= 3:
        return "technical", "Code-heavy content benefits from a developer-friendly dark aesthetic"

    # Data/analytics content
    data_markers = ["chart", "graph", "metric", "dashboard", "analytics", "benchmark", "performance"]
    if sum(1 for m in data_markers if m in text_lower) >= 2:
        return "data_viz", "Data-focused content works best with visualization-style covers"

    # Tutorial/how-to
    tutorial_markers = ["how to", "step by step", "tutorial", "guide", "getting started", "walkthrough"]
    if any(m in text_lower for m in tutorial_markers):
        return "illustration", "Tutorial content pairs well with friendly illustrations"

    # Opinion/thought leadership
    opinion_markers = ["i think", "i believe", "in my experience", "hot take", "unpopular opinion"]
    if any(m in text_lower for m in opinion_markers):
        return "editorial", "Thought leadership reads best with editorial-style imagery"

    # AI/ML/trending tech
    tech_markers = ["artificial intelligence", "machine learning", "llm", "neural", "gpt", "transformer"]
    if any(m in text_lower for m in tech_markers):
        return "vibrant", "AI/ML topics benefit from modern, energetic visuals"

    return "minimal", "Clean minimal style works well as a safe default"


def generate_cover_image_prompt(blog_text, title, ai_manager, platform="medium",
                                 style=None, model=None):
    """
    Generate an optimized image generation prompt for a blog cover image.

    Args:
        blog_text: The blog post content
        title: The blog post title
        ai_manager: The app's AI manager instance
        platform: Target platform (medium, linkedin, twitter, devto, youtube_thumbnail)
        style: Visual style override (editorial, technical, minimal, vibrant, illustration, photographic, data_viz)
        model: Optional model override

    Returns:
        dict with:
            - prompt: The image generation prompt
            - negative_prompt: What to avoid
            - platform_spec: dimensions and guidelines
            - style_used: which visual style was applied
            - alt_text: accessibility alt text
    """
    try:
        spec = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["medium"])

        if not style:
            style, _reason = detect_visual_style(blog_text, title)
        style_desc = VISUAL_STYLES.get(style, VISUAL_STYLES["minimal"])

        ai_prompt = f"""You are an expert visual designer creating a blog cover image prompt.

BLOG TITLE: {title}
BLOG EXCERPT: {blog_text[:500]}

PLATFORM: {platform} ({spec['width']}x{spec['height']}px, {spec['aspect']} aspect ratio)
PLATFORM STYLE GUIDE: {spec['style']}
TEXT SAFE ZONE: {spec['text_safe_zone']}

VISUAL STYLE: {style_desc}

Generate a detailed image generation prompt that:
1. Captures the essence of the blog topic in a single compelling visual
2. Works at the specified dimensions and aspect ratio
3. Follows the platform style guide
4. Leaves appropriate space for text overlay in the safe zone
5. Uses the specified visual style
6. Avoids: stock photo clichés, clipart, watermarks, text in the image (text will be overlaid separately), hands (AI gets them wrong), faces looking directly at camera

Return ONLY a JSON object (no markdown fences):
{{
    "prompt": "detailed image generation prompt (100-200 words)",
    "negative_prompt": "things to avoid in generation",
    "alt_text": "concise alt text for accessibility (under 125 chars)"
}}"""

        result = ai_manager.generate_content(ai_prompt, model=model)

        import json
        parsed = None
        try:
            parsed = json.loads(result)
        except Exception:
            if isinstance(result, str):
                first = result.find("{")
                last = result.rfind("}")
                if first != -1 and last > first:
                    try:
                        parsed = json.loads(result[first:last + 1])
                    except Exception:
                        parsed = None

        if parsed and isinstance(parsed, dict):
            return {
                "prompt": parsed.get("prompt", f"Professional cover image for: {title}"),
                "negative_prompt": parsed.get("negative_prompt", "text, watermark, blurry, low quality"),
                "platform_spec": spec,
                "style_used": style,
                "alt_text": parsed.get("alt_text", f"Cover image for {title}")
            }
        else:
            return _fallback_prompt(title, spec, style, style_desc)

    except Exception as e:
        print(f"[COVER_IMAGE] Error: {e}")
        return _fallback_prompt(title,
                                PLATFORM_SPECS.get(platform, PLATFORM_SPECS["medium"]),
                                style or "minimal",
                                VISUAL_STYLES.get(style, VISUAL_STYLES["minimal"]))


def _fallback_prompt(title, spec, style, style_desc):
    """Generate a sensible fallback prompt without AI."""
    return {
        "prompt": (
            f"Professional blog cover image, {style} style. "
            f"Topic: {title}. {style_desc} "
            f"Aspect ratio {spec['aspect']}, high resolution, clean composition. "
            f"Leave center space clear for text overlay."
        ),
        "negative_prompt": "text, watermark, blurry, low quality, hands, clipart",
        "platform_spec": spec,
        "style_used": style,
        "alt_text": f"Cover image for {title}"
    }


def generate_article_illustrations(blog_text, ai_manager, max_illustrations=3, model=None):
    """
    Suggest in-article illustrations/diagrams for key sections.

    Args:
        blog_text: The blog post content
        ai_manager: The app's AI manager instance
        max_illustrations: Maximum number of illustration suggestions
        model: Optional model override

    Returns:
        list of dicts with:
            - section: which part of the article
            - type: "diagram" | "illustration" | "screenshot" | "chart"
            - prompt: image generation prompt
            - placement: "before_section" | "after_section" | "inline"
            - caption: suggested caption text
    """
    try:
        ai_prompt = f"""Analyze this blog post and suggest {max_illustrations} strategic in-article illustrations.

BLOG POST:
{blog_text[:3000]}

For each illustration, determine the best type:
- "diagram": for explaining architecture, workflows, or relationships (Mermaid/flowchart style)
- "illustration": for conceptual explanations (flat vector style)
- "screenshot": for UI/tool demonstrations (suggest what to show)
- "chart": for data comparisons or trends

Return ONLY a JSON array (no markdown fences):
[
    {{
        "section": "heading or description of the section this belongs near",
        "type": "diagram|illustration|screenshot|chart",
        "prompt": "detailed image generation prompt",
        "placement": "before_section|after_section|inline",
        "caption": "suggested caption text"
    }}
]

Rules:
- Only suggest illustrations that genuinely help understanding
- Each illustration should serve a different purpose
- Prompts should be specific enough to generate useful images
- Prefer diagrams for technical concepts, illustrations for abstract ideas"""

        result = ai_manager.generate_content(ai_prompt, model=model)

        import json
        parsed = None
        try:
            parsed = json.loads(result)
        except Exception:
            if isinstance(result, str):
                first = result.find("[")
                last = result.rfind("]")
                if first != -1 and last > first:
                    try:
                        parsed = json.loads(result[first:last + 1])
                    except Exception:
                        parsed = None

        if isinstance(parsed, list):
            return parsed[:max_illustrations]
        return []

    except Exception as e:
        print(f"[COVER_IMAGE] Illustration suggestions error: {e}")
        return []


def generate_multi_platform_covers(blog_text, title, ai_manager, platforms=None, model=None):
    """
    Generate cover image prompts for multiple platforms at once.

    Args:
        blog_text: The blog post content
        title: The blog post title
        ai_manager: The app's AI manager instance
        platforms: List of platform keys (defaults to medium, linkedin, twitter)
        model: Optional model override

    Returns:
        dict mapping platform name to cover image prompt result
    """
    if platforms is None:
        platforms = ["medium", "linkedin", "twitter"]

    style, _reason = detect_visual_style(blog_text, title)
    results = {}

    for platform in platforms:
        try:
            results[platform] = generate_cover_image_prompt(
                blog_text, title, ai_manager,
                platform=platform, style=style, model=model
            )
        except Exception as e:
            print(f"[COVER_IMAGE] Error for {platform}: {e}")
            spec = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["medium"])
            results[platform] = _fallback_prompt(title, spec, style,
                                                  VISUAL_STYLES.get(style, VISUAL_STYLES["minimal"]))

    return results
