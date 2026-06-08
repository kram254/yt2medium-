import json
import re
from concurrent.futures import ThreadPoolExecutor

from viral_engine import ViralEngine


class ViralBodyOrchestrator:

    SECTION_TYPES = [
        {"id": "S01", "name": "Hook", "desc": "Opening 3 sentences with vulnerability, reader mirror, payoff promise"},
        {"id": "S02", "name": "Career CTA", "desc": "Author's career positioning block with links"},
        {"id": "S03", "name": "Problem", "desc": "The pain point or gap the reader is facing"},
        {"id": "S04", "name": "Solution Overview", "desc": "High-level approach before diving into details"},
        {"id": "S05", "name": "Solution Detail 1", "desc": "First specific technique or step with code/commands"},
        {"id": "S06", "name": "Solution Detail 2", "desc": "Second specific technique or step with code/commands"},
        {"id": "S07", "name": "Solution Detail 3", "desc": "Third specific technique or step with code/commands"},
        {"id": "S08", "name": "Trade-offs", "desc": "Honest discussion of limitations and when not to use"},
        {"id": "S09", "name": "Conclusion CTA", "desc": "Imperative call to action with specific first step"},
    ]

    def __init__(self, ai_manager, engine=None, max_workers=5, model=None):
        self.ai = ai_manager
        self.engine = engine or ViralEngine()
        self.max_workers = max_workers
        self.model = model

    def run(self, content, title=""):
        plan = self._plan(content, title)
        sections = self._draft_sections(plan, content, title)
        scored = self._score_sections(sections, content)
        corrected = self._correct_low_scoring(scored, content, plan)
        final = self._assemble(corrected, title)
        return {
            "plan": plan,
            "sections": corrected,
            "final_markdown": final["markdown"],
            "final_html": final["html"],
            "total_score": final["total_score"],
            "passed_threshold": final["passed"],
        }

    def _ai_call(self, prompt):
        if self.model:
            return self.ai.generate_content(prompt, None, self.model)
        return self.ai.generate_content(prompt)

    def _parse_json(self, raw):
        cleaned = (raw or "").strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[-1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.rstrip("`").strip()
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            cleaned = match.group(0)
        return json.loads(cleaned)

    def _plan(self, content, title):
        cfg = self.engine.config
        forces = cfg["seven_success_forces"]
        hooks = cfg["opening_hook_patterns"]["patterns"]
        metaphors = cfg["metaphor_library"]["metaphors"]

        forces_list = "\n".join(
            f"- {k}: {f['name']} — {f['description']}"
            for k, f in forces.items()
            if k.startswith("force_")
        )
        hooks_list = "\n".join(
            f"- {h['name']}: {h['template']}"
            for h in hooks
        )
        metaphors_list = "\n".join(
            f"- {m['name']}: fits {m['fits']}"
            for m in metaphors
        )

        prompt = (
            "You are the PLANNER agent in a viral Medium blog pipeline.\n"
            "Analyze the source content and create a production plan.\n\n"
            f"SOURCE EXCERPT:\n---\n{content[:3000]}\n---\n\n"
            f"TITLE: {title}\n\n"
            "AVAILABLE SUCCESS FORCES (pick 5+ to stack):\n"
            f"{forces_list}\n\n"
            "HOOK PATTERNS (pick one):\n"
            f"{hooks_list}\n\n"
            "METAPHORS (pick one to sustain across 3+ sections):\n"
            f"{metaphors_list}\n\n"
            "Return strict JSON only:\n"
            '{"chosen_hook": str, "chosen_metaphor": str, "chosen_forces": [list of 5+ force IDs], '
            '"trending_product": str, "key_pain_point": str, "key_solution": str, '
            '"copy_paste_items": [list of 3+ specific commands/URLs/tools to include], '
            '"section_briefs": [{"id": "S01", "focus": str}, ...]}'
        )

        raw = self._ai_call(prompt)
        try:
            data = self._parse_json(raw)
            return {
                "chosen_hook": str(data.get("chosen_hook", "")),
                "chosen_metaphor": str(data.get("chosen_metaphor", "")),
                "chosen_forces": data.get("chosen_forces", [])[:7],
                "trending_product": str(data.get("trending_product", "")),
                "key_pain_point": str(data.get("key_pain_point", "")),
                "key_solution": str(data.get("key_solution", "")),
                "copy_paste_items": data.get("copy_paste_items", [])[:10],
                "section_briefs": data.get("section_briefs", []),
            }
        except Exception as exc:
            return {
                "chosen_hook": "",
                "chosen_metaphor": "",
                "chosen_forces": [],
                "trending_product": "",
                "key_pain_point": "",
                "key_solution": "",
                "copy_paste_items": [],
                "section_briefs": [],
                "error": f"planner_fallback: {exc}",
            }

    def _draft_one_section(self, section_type, plan, content, title):
        cfg = self.engine.config
        voice = cfg["voice_specification"]
        author = cfg["author_profile"]
        length = cfg["length_targets"]

        section_brief = ""
        for sb in plan.get("section_briefs", []):
            if sb.get("id") == section_type["id"]:
                section_brief = sb.get("focus", "")
                break

        career_cta = cfg["post_anatomy"]["career_cta_block"]["template"].format(
            role_targets=author["role_targets"],
            capability_1=author["capability_1"],
            capability_2=author["capability_2"],
            email=author["email"],
            linkedin_url=author["linkedin_url"],
            upwork_url=author["upwork_url"],
            fiverr_url=author["fiverr_url"],
        )

        prompt = (
            f"You are the SECTION DRAFTER agent for section {section_type['id']} ({section_type['name']}).\n"
            f"Write this section for a viral Medium blog post.\n\n"
            f"SECTION TYPE: {section_type['name']}\n"
            f"SECTION DESCRIPTION: {section_type['desc']}\n"
            f"SECTION BRIEF FROM PLANNER: {section_brief}\n\n"
            f"POST TITLE: {title}\n"
            f"CHOSEN METAPHOR (reference in this section if applicable): {plan.get('chosen_metaphor', '')}\n"
            f"TRENDING PRODUCT TO FEATURE: {plan.get('trending_product', '')}\n"
            f"KEY PAIN POINT: {plan.get('key_pain_point', '')}\n"
            f"KEY SOLUTION: {plan.get('key_solution', '')}\n\n"
            "VOICE RULES:\n"
            f"- Person: {voice['person']}\n"
            f"- Tone: {voice['tone']}\n"
            f"- Use contractions: {voice['contractions']}\n"
            f"- Paragraph length: {voice['paragraph_length']}\n"
            f"- Banned phrases: {', '.join(voice['banned_phrases'][:5])}\n\n"
            f"TARGET LENGTH: {length['section_word_count']['ideal_range'][0]}-{length['section_word_count']['ideal_range'][1]} words\n\n"
        )

        if section_type["id"] == "S02":
            prompt += f"USE THIS EXACT CAREER CTA BLOCK:\n---\n{career_cta}\n---\n\n"

        if section_type["id"] in ["S05", "S06", "S07"]:
            items = plan.get("copy_paste_items", [])
            prompt += f"INCLUDE COPY-PASTEABLE ITEMS: {items}\n\n"

        if section_type["id"] == "S01":
            prompt += f"HOOK PATTERN TO USE: {plan.get('chosen_hook', '')}\n\n"

        prompt += (
            f"SOURCE EXCERPT:\n---\n{content[:2000]}\n---\n\n"
            "Return strict JSON only:\n"
            '{"section_markdown": str, "word_count": int, "metaphor_used": bool, '
            '"copy_paste_count": int, "rationale": str}'
        )

        raw = self._ai_call(prompt)
        try:
            data = self._parse_json(raw)
            return {
                "section_id": section_type["id"],
                "section_name": section_type["name"],
                "markdown": str(data.get("section_markdown", "")),
                "word_count": int(data.get("word_count", 0)),
                "metaphor_used": bool(data.get("metaphor_used", False)),
                "copy_paste_count": int(data.get("copy_paste_count", 0)),
                "rationale": str(data.get("rationale", "")),
            }
        except Exception:
            return {
                "section_id": section_type["id"],
                "section_name": section_type["name"],
                "markdown": "",
                "word_count": 0,
                "metaphor_used": False,
                "copy_paste_count": 0,
                "rationale": "draft_fallback",
            }

    def _draft_sections(self, plan, content, title):
        results = []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(self.SECTION_TYPES))) as pool:
            futures = [
                pool.submit(self._draft_one_section, st, plan, content, title)
                for st in self.SECTION_TYPES
            ]
            for fut in futures:
                try:
                    section = fut.result()
                except Exception:
                    section = None
                if section:
                    results.append(section)
        return sorted(results, key=lambda s: s["section_id"])

    def _score_one_section(self, section, content):
        cfg = self.engine.config
        rubric = cfg["self_check_rubric"]["required_checks"]

        relevant_checks = []
        section_id = section["section_id"]

        if section_id == "S01":
            relevant_checks = [c for c in rubric if c["id"] == "C02"]
        elif section_id == "S02":
            relevant_checks = [c for c in rubric if c["id"] == "C03"]
        elif section_id in ["S05", "S06", "S07"]:
            relevant_checks = [c for c in rubric if c["id"] in ["C05", "C06"]]
        elif section_id == "S08":
            relevant_checks = [c for c in rubric if c["id"] == "C06"]
        elif section_id == "S09":
            relevant_checks = [c for c in rubric if c["id"] == "C07"]

        checks_block = "\n".join(
            f"- [{c['severity'].upper()}] {c['id']}: {c['check']}"
            for c in relevant_checks
        ) if relevant_checks else "- General quality and voice consistency"

        prompt = (
            f"You are the SCORING agent for section {section['section_id']} ({section['section_name']}).\n"
            "Rate this section strictly on quality dimensions. Be conservative.\n\n"
            f"SECTION MARKDOWN:\n---\n{section['markdown']}\n---\n\n"
            f"RELEVANT RUBRIC CHECKS:\n{checks_block}\n\n"
            "Rate on 1-5 scale for each dimension:\n"
            "- rubric_compliance: Does it pass the relevant rubric checks?\n"
            "- voice_consistency: Peer-to-peer, uses contractions, no banned phrases?\n"
            "- engagement: Would a reader keep reading?\n"
            "- specificity: Contains concrete details, not vague advice?\n\n"
            "Return strict JSON only:\n"
            '{"rubric_compliance": int, "voice_consistency": int, "engagement": int, '
            '"specificity": int, "blocking_failures": [list of failed check IDs], "reasoning": str}'
        )

        raw = self._ai_call(prompt)
        try:
            data = self._parse_json(raw)
            rc = max(1, min(5, int(data.get("rubric_compliance", 3))))
            vc = max(1, min(5, int(data.get("voice_consistency", 3))))
            en = max(1, min(5, int(data.get("engagement", 3))))
            sp = max(1, min(5, int(data.get("specificity", 3))))
            return {
                "rubric_compliance": rc,
                "voice_consistency": vc,
                "engagement": en,
                "specificity": sp,
                "total": rc + vc + en + sp,
                "blocking_failures": data.get("blocking_failures", []),
                "reasoning": str(data.get("reasoning", "")),
            }
        except Exception as exc:
            return {
                "rubric_compliance": 3,
                "voice_consistency": 3,
                "engagement": 3,
                "specificity": 3,
                "total": 12,
                "blocking_failures": [],
                "reasoning": f"scorer_fallback: {exc}",
            }

    def _score_sections(self, sections, content):
        if not sections:
            return []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(sections))) as pool:
            futures = [pool.submit(self._score_one_section, s, content) for s in sections]
            for section, fut in zip(sections, futures):
                try:
                    section["score"] = fut.result()
                except Exception as exc:
                    section["score"] = {
                        "rubric_compliance": 1,
                        "voice_consistency": 1,
                        "engagement": 1,
                        "specificity": 1,
                        "total": 4,
                        "blocking_failures": [],
                        "reasoning": f"scorer_exception: {exc}",
                    }
        return sections

    def _correct_one_section(self, section, content, plan):
        score = section.get("score", {})
        if score.get("total", 0) >= 14 and not score.get("blocking_failures"):
            return section

        cfg = self.engine.config
        voice = cfg["voice_specification"]
        blocking = score.get("blocking_failures", [])

        prompt = (
            f"You are the CORRECTOR agent for section {section['section_id']} ({section['section_name']}).\n"
            "This section scored below threshold. Fix the issues and return an improved version.\n\n"
            f"ORIGINAL SECTION:\n---\n{section['markdown']}\n---\n\n"
            f"SCORE: {score.get('total', 0)}/20\n"
            f"BLOCKING FAILURES: {blocking}\n"
            f"SCORER REASONING: {score.get('reasoning', '')}\n\n"
            f"CHOSEN METAPHOR (must appear): {plan.get('chosen_metaphor', '')}\n"
            "VOICE RULES:\n"
            f"- Tone: {voice['tone']}\n"
            f"- Use contractions: {voice['contractions']}\n"
            f"- Banned phrases: {', '.join(voice['banned_phrases'][:5])}\n\n"
            "FIX ALL ISSUES. Return strict JSON only:\n"
            '{"corrected_markdown": str, "changes_made": [list of changes], "rationale": str}'
        )

        raw = self._ai_call(prompt)
        try:
            data = self._parse_json(raw)
            corrected_md = str(data.get("corrected_markdown", ""))
            if corrected_md and len(corrected_md) > 50:
                section["markdown"] = corrected_md
                section["corrected"] = True
                section["correction_changes"] = data.get("changes_made", [])
        except Exception:
            pass
        return section

    def _correct_low_scoring(self, sections, content, plan):
        low_scoring = [
            s for s in sections
            if s.get("score", {}).get("total", 0) < 14
            or s.get("score", {}).get("blocking_failures")
        ]
        if not low_scoring:
            return sections

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(low_scoring))) as pool:
            futures = {
                s["section_id"]: pool.submit(self._correct_one_section, s, content, plan)
                for s in low_scoring
            }
            for section_id, fut in futures.items():
                try:
                    corrected = fut.result()
                    for i, s in enumerate(sections):
                        if s["section_id"] == section_id:
                            sections[i] = corrected
                            break
                except Exception:
                    pass
        return sections

    def _assemble(self, sections, title):
        import markdown as md_lib

        sorted_sections = sorted(sections, key=lambda s: s["section_id"])
        parts = []

        if title:
            parts.append(f"# {title}\n")

        for section in sorted_sections:
            if section.get("markdown"):
                parts.append(section["markdown"].strip())

        final_markdown = "\n\n".join(parts)

        total_score = sum(s.get("score", {}).get("total", 0) for s in sorted_sections)
        max_score = len(sorted_sections) * 20
        passed = total_score >= (max_score * 0.7)

        try:
            final_html = md_lib.markdown(
                final_markdown,
                extensions=["fenced_code", "tables", "nl2br"]
            )
        except Exception:
            final_html = f"<pre>{final_markdown}</pre>"

        return {
            "markdown": final_markdown,
            "html": final_html,
            "total_score": total_score,
            "max_score": max_score,
            "passed": passed,
        }


def generate_viral_body(ai_manager, content, title="", model=None):
    if not content:
        return title, "", "", None
    orchestrator = ViralBodyOrchestrator(ai_manager, model=model)
    try:
        result = orchestrator.run(content[:8000], title)
    except Exception as exc:
        return title, "", "", {"error": str(exc)}
    return (
        title,
        result.get("final_markdown", ""),
        result.get("final_html", ""),
        result,
    )
