"""
viral_engine.py
================
Drop-in module for yt2medium- that loads viral_engine_config.json and
produces ready-to-use prompts for blog generation and title enhancement.

Wired into prompts.py via three integration points:
  1. augment_blog_gen_prompt(base_prompt) — wraps the existing prompt
  2. build_title_prompt(topic_or_transcript) — replaces the 3-variant generator
  3. validate_post(generated_markdown) — runs the self-check rubric after generation

Usage (in prompts.py):
    from viral_engine import ViralEngine
    engine = ViralEngine()  # auto-loads viral_engine_config.json

    # Blog generation:
    def get_blog_gen_prompt():
        base = _existing_blog_gen_prompt()  # rename your current function
        return engine.augment_blog_gen_prompt(base)

    # Title enhancement:
    def get_title_enhancement_prompt(original_title, source_content=""):
        return engine.build_title_prompt(original_title, source_content)

    # Post-generation check (in app.py after LLM returns):
    issues = engine.validate_post(generated_markdown)
    if issues['blocking']:
        # regenerate with corrective prompt
        ...
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class ViralEngine:
    """Loads viral_engine_config.json and exposes prompt-building helpers."""

    DEFAULT_CONFIG_PATH = Path(__file__).parent / "viral_engine_config.json"

    def __init__(self, config_path: Optional[str] = None):
        path = Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        if not path.exists():
            raise FileNotFoundError(
                f"viral_engine_config.json not found at {path}. "
                "Place it next to viral_engine.py or pass config_path."
            )
        with open(path, "r", encoding="utf-8") as f:
            self.config: Dict[str, Any] = json.load(f)

    # ------------------------------------------------------------------
    # Integration point 1: augment blog generation
    # ------------------------------------------------------------------
    def augment_blog_gen_prompt(self, base_prompt: str) -> str:
        """Wrap the existing blog gen prompt with the viral engine overlay."""
        overlay = self._build_viral_overlay()
        return f"{overlay}\n\n{base_prompt}"

    def _build_viral_overlay(self) -> str:
        cfg = self.config
        master = cfg["master_directive"]
        forces = cfg["seven_success_forces"]
        anatomy = cfg["post_anatomy"]
        voice = cfg["voice_specification"]
        length = cfg["length_targets"]
        hooks = cfg["opening_hook_patterns"]["patterns"]
        metaphors = cfg["metaphor_library"]["metaphors"]
        author = cfg["author_profile"]
        rubric = cfg["self_check_rubric"]["required_checks"]
        contract = cfg["output_contract"]

        career_cta = anatomy["career_cta_block"]["template"].format(
            role_targets=author["role_targets"],
            capability_1=author["capability_1"],
            capability_2=author["capability_2"],
            email=author["email"],
            linkedin_url=author["linkedin_url"],
            upwork_url=author["upwork_url"],
            fiverr_url=author["fiverr_url"],
        )

        forces_block = "\n".join(
            f"  - **{f['name']}**: {f['description']}\n    Implementation: {f['implementation']}"
            for key, f in forces.items()
            if key.startswith("force_")
        )

        hook_block = "\n".join(
            f"  - {h['name']}: {h['template']}\n    Example: {h['example']}"
            for h in hooks
        )

        metaphor_block = "\n".join(
            f"  - {m['name']} — fits {m['fits']}; mapping: {m['mapping']}"
            for m in metaphors
        )

        rubric_block = "\n".join(
            f"  - [{c['severity'].upper()}] {c['check']}" for c in rubric
        )

        banned = ", ".join(f'"{p}"' for p in voice["banned_phrases"])
        encouraged = ", ".join(f'"{p}"' for p in voice["encouraged_phrases"])

        return f"""
================================================================================
 VIRAL ENGINE OVERLAY (v{self.config['engine_version']})
 Evidence base: Forensic analysis of the Claude Code 99% Cheaper post by
 {author['name']} — the highest-performing post on {author['medium_url']}.
 These patterns are non-negotiable. They take precedence over any conflicting
 instruction below.
================================================================================

ROLE & DIRECTIVE
{master['role']}

NON-NEGOTIABLES (every post must satisfy all of these):
{chr(10).join(f'  - {n}' for n in master['non_negotiables'])}

THE SEVEN SUCCESS FORCES (stack at least 5 of 7):
{forces_block}

CAREER CTA BLOCK (insert directly after opening hook, before body begins):
---
{career_cta}
---

LENGTH TARGETS:
  - Word count: minimum {length['word_count']['min']}, ideal {length['word_count']['ideal_range'][0]}-{length['word_count']['ideal_range'][1]}, maximum {length['word_count']['max']}
  - Read length: {length['read_length_minutes']['ideal']} minutes (range {length['read_length_minutes']['min']}-{length['read_length_minutes']['max']})
  - Sections: {length['section_count']['ideal_range'][0]}-{length['section_count']['ideal_range'][1]} H2 sections
  - Each section: {length['section_word_count']['ideal_range'][0]}-{length['section_word_count']['ideal_range'][1]} words

OPENING HOOK PATTERNS (pick one that fits the source):
{hook_block}

SUSTAINED METAPHOR (pick exactly one and carry it through the entire post):
{metaphor_block}

VOICE SPECIFICATION:
  - Person: {voice['person']}
  - Tone: {voice['tone']}
  - Register: {voice['register']}
  - Paragraph length: {voice['paragraph_length']}
  - Banned phrases (never use): {banned}
  - Encouraged phrases: {encouraged}
  - Contractions: {voice['contractions']}
  - Hedging: {voice['hedging']}

OUTPUT STRUCTURE (this exact order):
{chr(10).join(f'  {i+1}. {s}' for i, s in enumerate(contract['structure_order']))}

FORBIDDEN IN OUTPUT:
{chr(10).join(f'  - {f}' for f in contract['forbidden_in_output'])}

SELF-CHECK BEFORE OUTPUT:
{rubric_block}

If any blocking check fails, fix it before returning. The output must pass all
blocking checks. This is the bar your own viral post set.

================================================================================
 END VIRAL ENGINE OVERLAY
================================================================================
"""

    # ------------------------------------------------------------------
    # Integration point 2: title generation
    # ------------------------------------------------------------------
    def build_title_prompt(
        self, topic_or_transcript: str, original_title: str = ""
    ) -> str:
        """Build the prompt used by the LLM to generate titles using the formula."""
        cfg = self.config["title_engine"]
        formula = cfg["primary_formula"]
        constraints = cfg["constraints"]
        templates = cfg["templates"]
        rubric = cfg["scoring_rubric"]
        instructions = cfg["generation_instructions"]

        templates_block = "\n".join(
            f"""  - {t['id']} ({t['name']})
    Use when: {t['use_when']}
    Pattern: {t['pattern']}
    Example: {t['example']}
    Search intent: {t['search_intent']}"""
            for t in templates
        )

        must_contain = "\n".join(f"    - {m}" for m in constraints["must_contain"])
        must_avoid = "\n".join(f"    - {m}" for m in constraints["must_avoid"])

        return f"""You are a viral Medium title strategist. Your output follows the proven formula
from the post that broke out on {self.config['author_profile']['medium_url']}.

PRIMARY FORMULA:
{formula['pattern']}

DECOMPOSITION OF THE VIRAL TITLE (so you understand each slot):
  Title: "{formula['example_decomposition']['viral_title']}"
  - Trending product: "{formula['example_decomposition']['components']['trending_product']}"
  - Specific outcome: "{formula['example_decomposition']['components']['specific_outcome']}"
  - Named tools: "{formula['example_decomposition']['components']['named_tools']}"
  - Action goal: "{formula['example_decomposition']['components']['action_goal']}"
  - Numbered proof: "{formula['example_decomposition']['components']['numbered_proof']}"

CONSTRAINTS:
  Length: {constraints['min_chars']}-{constraints['max_chars']} chars (ideal {constraints['ideal_chars_range'][0]}-{constraints['ideal_chars_range'][1]})
  Must contain:
{must_contain}
  Must avoid:
{must_avoid}

FIVE TEMPLATES (pick whichever best fits the source content):
{templates_block}

SCORING RUBRIC (each dimension 1-5, total must be 16+):
  - Search intent: {rubric['scale_1_to_5']['search_intent']}
  - Specificity: {rubric['scale_1_to_5']['specificity']}
  - Outcome clarity: {rubric['scale_1_to_5']['outcome_clarity']}
  - Trust anchor: {rubric['scale_1_to_5']['trust_anchor']}

PROCESS:
{chr(10).join(f'  {s}' for s in instructions['process'])}

SOURCE CONTENT:
---
{topic_or_transcript[:3000]}
---

ORIGINAL TITLE (if any): "{original_title}"

OUTPUT FORMAT (strict JSON):
{instructions['output_format']}

Return only the JSON. No prose, no explanation outside the JSON.
"""

    # ------------------------------------------------------------------
    # Integration point 3: post-generation validation
    # ------------------------------------------------------------------
    def validate_post(self, markdown: str) -> Dict[str, List[str]]:
        """Run a programmatic check against the self-check rubric.

        Returns: {'blocking': [list of failed check IDs], 'warnings': [...]}
        Empty lists mean the post passed.
        """
        cfg = self.config
        author = cfg["author_profile"]
        voice = cfg["voice_specification"]
        length = cfg["length_targets"]
        forces = cfg["seven_success_forces"]

        blocking: List[str] = []
        warnings: List[str] = []
        words = len(markdown.split())

        # C08: word count
        if words < length["word_count"]["min"] or words > length["word_count"]["max"]:
            blocking.append(
                f"C08 — word count {words} outside range "
                f"{length['word_count']['min']}-{length['word_count']['max']}"
            )

        # C03: career CTA block presence
        if not any(token in markdown for token in [author["email"], author["linkedin_url"]]):
            blocking.append("C03 — career CTA block missing (email/linkedin not found)")

        # C10: banned phrases
        lower = markdown.lower()
        hit_banned = [p for p in voice["banned_phrases"] if p.lower() in lower]
        if hit_banned:
            blocking.append(f"C10 — banned phrases present: {hit_banned}")

        # C07: final paragraph imperative CTA
        tail = markdown.strip().split("\n\n")[-1].strip().lower()
        imperatives = ["open", "type", "run", "go to", "create", "do", "start", "your first", "try"]
        if not any(imp in tail for imp in imperatives):
            blocking.append("C07 — final paragraph lacks imperative CTA")

        # C05: copy-pasteable specifics (code fences, URLs, or backticked tokens)
        url_count = len(re.findall(r"https?://\S+", markdown))
        code_blocks = markdown.count("```")
        inline_code = len(re.findall(r"`[^`\n]+`", markdown))
        specifics = url_count + (code_blocks // 2) + inline_code
        if specifics < 3:
            blocking.append(
                f"C05 — only {specifics} copy-pasteable specifics found (need 3+)"
            )

        # C11: title heuristic — first H1
        m = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
        if m:
            title = m.group(1)
            has_number = bool(re.search(r"\d", title))
            has_brand_or_tool = any(
                kw.lower() in title.lower()
                for kw in cfg["high_intent_keyword_engine"]["category_trending_product"]["high_value_2026"]
            )
            if not has_number:
                blocking.append("C11 — title lacks a specific number")
            if not has_brand_or_tool:
                warnings.append(
                    "C11 — title may lack a trending product/tool keyword "
                    "(check against high_intent_keyword_engine.category_trending_product)"
                )
        else:
            blocking.append("C11 — no H1 title found in post")

        # C09: success forces — heuristic (light)
        force_hits = 0
        if re.search(r"trade[- ]off|warning|critical", markdown, re.IGNORECASE):
            force_hits += 1  # F6 honest tradeoffs
        if re.search(r"\b(I|My|I'm|I've|I was)\b.*\b(burned|wasted|lost|wrong|frustrat)", markdown, re.IGNORECASE):
            force_hits += 1  # F3 confessional hook
        if specifics >= 3:
            force_hits += 1  # F5 specificity
        if re.search(r"(free|cheap|99%|alternative|instead of|vs)", markdown, re.IGNORECASE):
            force_hits += 1  # F2 high-intent search
        if any(
            tool.lower() in markdown.lower()
            for tool in cfg["high_intent_keyword_engine"]["category_trending_product"]["high_value_2026"]
        ):
            force_hits += 1  # F1 topical timing
        # F4 (metaphor) and F7 (imperative CTA) checked separately
        if "your first task" in lower or "do one of them" in lower or "right now" in lower:
            force_hits += 1
        if force_hits < 5:
            blocking.append(f"C09 — only {force_hits}/7 success forces detected (need 5+)")

        return {"blocking": blocking, "warnings": warnings}

    # ------------------------------------------------------------------
    # Helper: build a corrective prompt when validation fails
    # ------------------------------------------------------------------
    def build_correction_prompt(self, markdown: str, issues: Dict[str, List[str]]) -> str:
        """Generate a corrective prompt that asks the LLM to fix specific failures."""
        if not issues["blocking"]:
            return ""
        bullets = "\n".join(f"  - {i}" for i in issues["blocking"])
        return f"""Your previous draft failed these blocking checks from the viral engine:

{bullets}

Revise the draft. Fix each failure. Return only the corrected markdown.
Do not explain — just produce the fixed version.

Previous draft:
---
{markdown}
---
"""


# ----------------------------------------------------------------------
# Quick CLI smoke test:  python viral_engine.py
# ----------------------------------------------------------------------
if __name__ == "__main__":
    engine = ViralEngine()
    print("=== TITLE PROMPT (first 1200 chars) ===")
    print(engine.build_title_prompt("How to deploy LangGraph agents on AWS Lambda")[:1200])
    print("\n=== OVERLAY (first 1500 chars) ===")
    print(engine._build_viral_overlay()[:1500])
    print("\nReady. Drop viral_engine.py + viral_engine_config.json into the repo root next to prompts.py.")
