import json
import re
from concurrent.futures import ThreadPoolExecutor

from viral_engine import ViralEngine


class ViralTitleOrchestrator:

    def __init__(self, ai_manager, engine=None, max_workers=5, model=None):
        self.ai = ai_manager
        self.engine = engine or ViralEngine()
        self.max_workers = max_workers
        self.model = model

    def run(self, content, current_title=""):
        plan = self._plan(content, current_title)
        variants = self._execute_variants(plan, content, current_title)
        scored = self._score_variants(variants, content)
        synthesis = self._synthesize(scored, current_title)
        return {
            "plan": plan,
            "variants": scored,
            "recommended": synthesis["recommended"],
            "recommendation_rationale": synthesis["rationale"],
            "passed_threshold": synthesis["passed"],
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

    def _plan(self, content, current_title):
        templates = self.engine.config["title_engine"]["templates"]
        catalogue = "\n".join(
            f"- {t['id']}: {t['name']} (use when: {t['use_when']})"
            for t in templates
        )
        prompt = (
            "You are the PLANNER agent in a viral Medium title pipeline.\n"
            "From the five templates below, pick exactly three IDs whose "
            "use_when conditions best fit the source content. Also surface "
            "the strongest trending product reference and a specific outcome "
            "(percentage, dollar amount, or count) hinted at by the source.\n\n"
            f"TEMPLATES:\n{catalogue}\n\n"
            f"CURRENT TITLE (may be weak): {current_title}\n\n"
            f"SOURCE EXCERPT:\n---\n{content[:2500]}\n---\n\n"
            "Return strict JSON only:\n"
            "{\"chosen_template_ids\": [\"T0X_...\", \"T0Y_...\", \"T0Z_...\"],"
            " \"trending_product\": str, \"specific_outcome\": str,"
            " \"reasoning\": str}"
        )
        raw = self._ai_call(prompt)
        valid_ids = {t["id"] for t in templates}
        try:
            data = self._parse_json(raw)
            ids = [i for i in data.get("chosen_template_ids", [])[:3] if i in valid_ids]
            if len(ids) < 3:
                fallback = [t["id"] for t in templates if t["id"] not in ids]
                ids = (ids + fallback)[:3]
            return {
                "chosen_template_ids": ids,
                "trending_product": str(data.get("trending_product", "")),
                "specific_outcome": str(data.get("specific_outcome", "")),
                "reasoning": str(data.get("reasoning", "")),
            }
        except Exception as exc:
            return {
                "chosen_template_ids": [t["id"] for t in templates[:3]],
                "trending_product": "",
                "specific_outcome": "",
                "reasoning": f"planner_fallback: {exc}",
            }

    def _generate_one_variant(self, template_id, content, current_title, plan):
        templates = self.engine.config["title_engine"]["templates"]
        template = next((t for t in templates if t["id"] == template_id), None)
        if not template:
            return None
        constraints = self.engine.config["title_engine"]["constraints"]
        must_avoid = "; ".join(constraints["must_avoid"])
        formula = self.engine.config["title_engine"]["primary_formula"]["pattern"]
        prompt = (
            f"You are the VARIANT GENERATOR agent for template {template['id']} "
            f"({template['name']}). Produce exactly one viral Medium title that "
            "follows the template pattern and the primary formula.\n\n"
            f"PRIMARY FORMULA:\n{formula}\n\n"
            f"TEMPLATE PATTERN: {template['pattern']}\n"
            f"USE WHEN: {template['use_when']}\n"
            f"EXAMPLE: {template['example']}\n\n"
            "CONSTRAINTS:\n"
            f"- Length: {constraints['min_chars']}-{constraints['max_chars']} chars "
            f"(ideal {constraints['ideal_chars_range'][0]}-{constraints['ideal_chars_range'][1]})\n"
            "- Must include a named brand or product\n"
            "- Must include a specific number (percentage, dollar amount, or count)\n"
            "- Must include a named tool or technology\n"
            "- Must promise a plain-English outcome the reader can picture in two seconds\n"
            f"- Avoid: {must_avoid}\n\n"
            f"PLAN HINTS:\n"
            f"- trending_product: {plan.get('trending_product', '')}\n"
            f"- specific_outcome: {plan.get('specific_outcome', '')}\n\n"
            f"CURRENT TITLE (must be beaten): {current_title}\n\n"
            f"SOURCE EXCERPT:\n---\n{content[:2500]}\n---\n\n"
            "Return strict JSON only:\n"
            "{\"title\": str, \"rationale\": str}"
        )
        raw = self._ai_call(prompt)
        try:
            data = self._parse_json(raw)
            title = (data.get("title") or "").strip().strip('"').strip("'")
            if title:
                return {
                    "template_id": template_id,
                    "template_name": template["name"],
                    "title": title,
                    "rationale": str(data.get("rationale", "")),
                }
        except Exception:
            pass
        return None

    def _execute_variants(self, plan, content, current_title):
        ids = plan["chosen_template_ids"]
        if not ids:
            return []
        results = []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(ids))) as pool:
            futures = [
                pool.submit(self._generate_one_variant, tid, content, current_title, plan)
                for tid in ids
            ]
            for fut in futures:
                try:
                    variant = fut.result()
                except Exception:
                    variant = None
                if variant:
                    results.append(variant)
        return results

    def _score_one(self, variant, content):
        rubric = self.engine.config["title_engine"]["scoring_rubric"]["scale_1_to_5"]
        prompt = (
            "You are the SCORING agent for viral Medium titles. "
            "Rate this title strictly on four 1-5 dimensions. "
            "Be quantitative and conservative, not generous.\n\n"
            f"TITLE: {variant['title']}\n"
            f"TEMPLATE: {variant.get('template_name', variant.get('template_id', ''))}\n\n"
            "RUBRIC:\n"
            f"- search_intent (1-5): {rubric['search_intent']}\n"
            f"- specificity (1-5): {rubric['specificity']}\n"
            f"- outcome_clarity (1-5): {rubric['outcome_clarity']}\n"
            f"- trust_anchor (1-5): {rubric['trust_anchor']}\n\n"
            f"SOURCE CONTEXT:\n---\n{content[:1500]}\n---\n\n"
            "Return strict JSON only:\n"
            "{\"search_intent\": int, \"specificity\": int, "
            "\"outcome_clarity\": int, \"trust_anchor\": int, \"reasoning\": str}"
        )
        raw = self._ai_call(prompt)
        try:
            data = self._parse_json(raw)
            si = max(1, min(5, int(data.get("search_intent", 3))))
            sp = max(1, min(5, int(data.get("specificity", 3))))
            oc = max(1, min(5, int(data.get("outcome_clarity", 3))))
            ta = max(1, min(5, int(data.get("trust_anchor", 3))))
            return {
                "search_intent": si,
                "specificity": sp,
                "outcome_clarity": oc,
                "trust_anchor": ta,
                "total": si + sp + oc + ta,
                "reasoning": str(data.get("reasoning", "")),
            }
        except Exception as exc:
            return {
                "search_intent": 3,
                "specificity": 3,
                "outcome_clarity": 3,
                "trust_anchor": 3,
                "total": 12,
                "reasoning": f"scorer_fallback: {exc}",
            }

    def _score_variants(self, variants, content):
        if not variants:
            return []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(variants))) as pool:
            futures = [pool.submit(self._score_one, v, content) for v in variants]
            for variant, fut in zip(variants, futures):
                try:
                    variant["score"] = fut.result()
                except Exception as exc:
                    variant["score"] = {
                        "search_intent": 1,
                        "specificity": 1,
                        "outcome_clarity": 1,
                        "trust_anchor": 1,
                        "total": 4,
                        "reasoning": f"scorer_exception: {exc}",
                    }
        return variants

    def _synthesize(self, variants, current_title):
        if not variants:
            return {
                "recommended": current_title or "",
                "rationale": "no variants produced",
                "passed": False,
            }
        best = max(variants, key=lambda v: v.get("score", {}).get("total", 0))
        total = best.get("score", {}).get("total", 0)
        passed = total >= 16
        rationale_parts = [
            f"Selected {best.get('template_id', '')} ({best.get('template_name', '')}) "
            f"with total score {total}/20 against the four-dimension rubric.",
        ]
        if best.get("rationale"):
            rationale_parts.append(f"Variant rationale: {best['rationale']}")
        score_reason = best.get("score", {}).get("reasoning", "")
        if score_reason:
            rationale_parts.append(f"Scoring rationale: {score_reason}")
        return {
            "recommended": best["title"],
            "rationale": " ".join(rationale_parts),
            "passed": passed,
        }


def upgrade_post_title(ai_manager, markdown_body, current_title="", model=None):
    if not markdown_body:
        return current_title, markdown_body, None
    orchestrator = ViralTitleOrchestrator(ai_manager, model=model)
    try:
        result = orchestrator.run(markdown_body[:5000], current_title)
    except Exception as exc:
        return current_title, markdown_body, {"error": str(exc)}
    recommended = result.get("recommended", "")
    if not recommended or not result.get("passed_threshold"):
        return current_title, markdown_body, result
    pattern = re.compile(r"^#\s+.+$", re.MULTILINE)
    if pattern.search(markdown_body):
        updated = pattern.sub(f"# {recommended}", markdown_body, count=1)
    else:
        updated = f"# {recommended}\n\n{markdown_body}"
    return recommended, updated, result
