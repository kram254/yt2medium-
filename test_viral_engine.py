"""Unit tests for viral_engine.ViralEngine.

Covers each programmatically-enforced blocking check in validate_post,
plus the title-prompt builder and the correction-prompt builder.

Run with:
    python3 -m unittest test_viral_engine -v
"""

import json
import os
import sys
import unittest

# Make the repo root importable when tests are run from a subdir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from viral_engine import ViralEngine  # noqa: E402


# ----------------------------------------------------------------------
# Fixture builder
# ----------------------------------------------------------------------
GOOD_TITLE = (
    "# Claude Code 99% Cheaper Using Ollama and OpenRouter: "
    "How to Run Claude Code for Free (Two Methods That Work)"
)

CTA_BLOCK = """\U0001F680 I'm currently open to AI/ML roles, freelance projects, and software development opportunities. If you're building something interesting from intelligent systems to full-stack apps, I'd love to collaborate.

\U0001F4E9 Email: markorlando45@gmail.com
\U0001F4BC LinkedIn: https://www.linkedin.com/in/emmanuel-ndaliro-501771124/
\U0001F9D1‍\U0001F4BB Upwork: https://www.upwork.com/freelancers/~01ee00096be90b99d3
\U0001F3AF Fiverr: https://www.fiverr.com/users/ndaliro_mark/seller_dashboard"""

OPENING = (
    "I burned through hundreds of dollars in Claude API fees before I realized "
    "the truth. You can get most of what you need for zero dollars. I was "
    "frustrated. You might be, too."
)

MENTAL_MODEL = """## The Mental Model

Forget the idea that Claude Code is the AI. It isn't. Think of it like a car. Claude Code is the chassis. The engine is whatever language model you bolt under the hood. The free alternative is just a different engine in the same chassis.

This metaphor matters because once you see Claude Code as a chassis, swapping the engine becomes obvious. The car still drives. The dashboard still works. The fuel just got free instead of expensive.

Trade-off: the local engine is slower than the cloud engine. The first response takes about six seconds instead of two. After that, queries flow at roughly the pace of human reading.

You can run `ollama pull qwen2.5:7b` to grab the local engine. Visit https://openrouter.ai for the cloud alternative. Configure Claude Code via `~/.config/claude-code/config.json` and point it at the new endpoint."""

METHOD_SECTION = """## Method One: The Local Engine

This section explains the implementation. Each step is concrete. Each command is copy-pasteable.

First, install the runtime with `brew install ollama`. The package manager handles dependencies. Total install time is under thirty seconds on a clean machine.

Second, pull the model with `ollama pull qwen2.5:7b`. This downloads roughly four gigabytes. On a residential connection that takes around ten minutes.

Third, verify the runtime is listening. Run `curl http://localhost:11434/api/tags` and confirm it returns JSON. If the request times out, the runtime isn't running.

Fourth, configure Claude Code to use the new endpoint. The config file lives at `~/.config/claude-code/config.json`. Replace the default model URL with the local Ollama address.

Trade-off: the local engine is slower than the cloud engine on cold start. You also lose the model's training cutoff freshness. For most coding tasks that's a fine swap, but for current-events research the cloud engine still wins."""

REFRAME = """## When the Free Engine Actually Wins

Learning. The first 80% of any task. High-volume grunt work. As your paid model's assistant for cheap parallel calls.

The car analogy holds. You don't drive your Ferrari to the grocery store. You drive the beater. Save the Ferrari for the road trip that matters.

For the rest of your week, the free engine handles the routine traffic without you ever feeling the difference. The pattern shows up everywhere once you start looking. Linting passes, doc generation, name-the-variable suggestions, scaffold-the-test work, regex-rewrites, log-noise cleanup. Tasks that don't reward genius. Tasks that reward a model that just answers and gets out of the way.

The economics make the same case. A free engine running at three queries per second costs nothing. The cloud engine at the same rate costs roughly seven dollars a day, every day, even on the days when half those queries were the model rewriting your `print` statements. The car analogy lands again: a Ferrari sitting in traffic is still burning fuel."""

PRODUCTION_SETUP = """## The Production-Ready Configuration

Once the toy setup works, harden it. The runtime needs a supervisor. The model needs a warm pool. The chassis needs a fallback.

Start with the supervisor. On a Mac, the right tool is launchd. Drop a plist at `~/Library/LaunchAgents/com.user.ollama.plist` that boots the runtime on login and restarts it on crash. On Linux, the equivalent is a systemd user unit at `~/.config/systemd/user/ollama.service`. Either one prevents the most boring failure mode in the world: the runtime died, you didn't notice, every Claude Code request hangs for thirty seconds before timing out.

Next, the warm pool. Cold-starting a 7B model takes around five seconds the first time after the runtime starts. That's tolerable once a day. It's not tolerable in the middle of a flow. The fix is `OLLAMA_KEEP_ALIVE=24h` in the supervisor's environment. The runtime keeps the model resident for a full day. The chassis sees consistent latency.

Then the fallback. Pin both engines in the Claude Code config. The local engine is the default. The cloud engine is the fallback on any 5XX response. The config block looks roughly like:

```json
{
  "primary": "http://localhost:11434",
  "fallback": "https://openrouter.ai/api/v1",
  "fallback_model": "openrouter/qwen/qwen-3.6-free",
  "fallback_token_env": "OPENROUTER_API_KEY"
}
```

Trade-off: maintaining two engines doubles your config surface. You will eventually mis-configure one. The mitigation is a thirty-second smoke test you run at the start of every coding session: `curl localhost:11434/api/tags` and `curl https://openrouter.ai/api/v1/models -H "Authorization: Bearer $OPENROUTER_API_KEY"`. Both 200 means you're safe. Either 4XX means fix it before you start work, not after."""

COST_COMPARISON = """## The Cost Math Nobody Shows You

Let's actually do the math. The paid Claude API bills at roughly three dollars per million input tokens and fifteen dollars per million output tokens for the mid-tier model. A coding day with Claude Code easily burns through two million tokens of context and four hundred thousand tokens of output. That's around twelve dollars a day. Across a five-day work week, sixty dollars. Across a year, three thousand.

Now run the same workload through Ollama on the machine you already paid for. Electricity for the GPU draws around 250 watts under load. At $0.15 per kilowatt-hour, a full coding day costs maybe forty cents. Across a year, under one hundred and fifty dollars. That's the ninety-nine percent figure in the title: roughly $3,000 versus roughly $150.

The OpenRouter free tier sits in between. You pay nothing in dollars but you spend rate-limit headroom and you accept the third-party hop. For most weeks of work, that trade is fine. For the week you ship the production release, route to the paid engine. The chassis lets you switch lanes mid-trip.

Critical warning: don't trust this math blindly for your own workload. Run `ollama serve --verbose` for one full coding day and capture the actual token counts. Multiply by your paid-engine rate card. Your number won't match mine. The exercise is what matters."""

PITFALLS = """## Five Pitfalls You Will Hit Anyway

The first pitfall is letting the runtime go to sleep. Ollama on a laptop suspends itself after the lid closes. The next morning Claude Code times out on a healthy-looking config because the runtime is napping. Fix: a launchd plist or a systemd timer that pings `http://localhost:11434/api/tags` every five minutes. The model stays warm. The chassis never notices.

The second pitfall is mis-matching context windows. The local engine ships with an 8K window by default. Claude Code happily packs 30K tokens of context into a single request. The runtime silently truncates the tail. The model responds confidently to half a prompt. Fix: set `OLLAMA_NUM_CTX=32768` in the launch environment. The runtime expands the window. The chassis stops handing it half-finished sentences.

The third pitfall is assuming the free engine is identical to the paid engine on subtle reasoning tasks. It isn't. The free engine wins on routine work and loses on multi-step synthesis. The simplest defense is a router: when the prompt mentions a hard-reasoning verb (`design`, `plan`, `architect`), route to the cloud engine. Trade-off: the router itself takes a few milliseconds and you have to maintain its keyword list. The simplest version is a six-line shell script.

The fourth pitfall is privacy regression. If you switch to OpenRouter without thinking, every prompt your team sends now passes through a third party. For most code that's fine. For client work under an NDA, it is not. Fix: keep the local engine as the default and the cloud engine as the opt-in. The chassis can hold both at once.

The fifth pitfall is staleness. The model you pull today is the model you have until you pull again. The cloud engine retrains. The local one doesn't. Set a calendar reminder: every quarter, run `ollama pull qwen2.5:7b` again to refresh to the latest checkpoint. The chassis stays the same. The engine quietly improves."""

METHOD_TWO = """## Method Two: The Cloud Alternative

OpenRouter is the second engine option. It routes traffic to a free tier of models hosted across multiple providers. The interface stays identical to the cloud Claude API, so Claude Code doesn't know the difference.

First, create an account at https://openrouter.ai. The free tier requires no credit card. You get a key in roughly thirty seconds.

Second, copy the key into your environment as `OPENROUTER_API_KEY`. The Claude Code shim reads this on startup and routes outbound calls through OpenRouter instead of the Anthropic endpoint.

Third, pick the model. The free roster shifts week to week. `openrouter/qwen/qwen-3.6-free` is a safe default for coding tasks. `openrouter/meta/llama-3.1-70b-free` is the better default for prose.

Fourth, sanity-check. Send a trivial query through `curl https://openrouter.ai/api/v1/chat/completions` with the key in the header and confirm a 200 response. If you get a 429 it means the free tier rate-limited you. Wait a minute and try again.

Trade-off: OpenRouter routes through a third party. Your prompts pass through their infrastructure before reaching the model. If your work involves IP-sensitive code, the local engine wins on privacy. For everything else, OpenRouter wins on raw response speed because the models live on dedicated GPUs."""

CLOSING = """## Your First Task

The chassis is in your hands already. The engine is the only thing you've been paying for. Swap it.

Open a new terminal window right now. Type `ollama pull qwen2.5:7b` or go to https://openrouter.ai and create an account. Do one of them right now. Don't bookmark this post and forget. Start the download. Then come back."""


def make_good_post(
    title=GOOD_TITLE,
    include_cta=True,
    closing=CLOSING,
    extra_tail="",
):
    """Build a post that passes every blocking check.

    Each keyword argument flips exactly one rubric check off so a test
    can verify the validator catches that specific failure.
    """
    parts = [title]
    if include_cta:
        parts.append(CTA_BLOCK)
    parts.append(OPENING)
    parts.append(MENTAL_MODEL)
    parts.append(METHOD_SECTION)
    parts.append(METHOD_TWO)
    parts.append(PRODUCTION_SETUP)
    parts.append(COST_COMPARISON)
    parts.append(PITFALLS)
    parts.append(REFRAME)
    parts.append(closing)
    if extra_tail:
        parts.append(extra_tail)
    return "\n\n".join(parts)


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------
class TestFixture(unittest.TestCase):
    """Sanity check the fixture itself before relying on it."""

    @classmethod
    def setUpClass(cls):
        cls.engine = ViralEngine()

    def test_good_post_passes_all_blocking_checks(self):
        post = make_good_post()
        word_count = len(post.split())
        self.assertGreaterEqual(word_count, 1600, f"fixture too short: {word_count}")
        self.assertLessEqual(word_count, 2400, f"fixture too long: {word_count}")
        result = self.engine.validate_post(post)
        self.assertEqual(
            result["blocking"],
            [],
            f"known-good fixture failed: {result['blocking']}",
        )


class TestValidatePostBlockingChecks(unittest.TestCase):
    """One test per blocking check the validator implements."""

    @classmethod
    def setUpClass(cls):
        cls.engine = ViralEngine()

    def _has(self, result, check_id):
        return any(check_id in issue for issue in result["blocking"])

    # C03: career CTA block presence (email or LinkedIn URL must appear)
    def test_c03_missing_career_cta_block_is_blocking(self):
        post = make_good_post(include_cta=False)
        result = self.engine.validate_post(post)
        self.assertTrue(self._has(result, "C03"), result["blocking"])

    # C05: at least 3 copy-pasteable specifics
    def test_c05_insufficient_specifics_is_blocking(self):
        bare = (
            "# Title with Claude Code 99 percent\n\n"
            "I was wrong about Claude Code. "
            "It is cheaper to use free alternatives. "
            "Trade-off applies. Your first task is to act. "
            "Open the door. Do one of them right now. "
        )
        # Pad to land inside the 1600-2400 word window without adding URLs or code
        bare = bare + ("Plain prose sentence. " * 400)
        result = self.engine.validate_post(bare)
        self.assertTrue(self._has(result, "C05"), result["blocking"])

    # C07: final paragraph must contain an imperative
    def test_c07_no_imperative_cta_at_end_is_blocking(self):
        post = make_good_post(
            closing=(
                "## Wrap-up\n\nThe situation was interesting. "
                "Many lessons emerged from the experience. "
                "Reflection is the natural next step for any practitioner."
            )
        )
        result = self.engine.validate_post(post)
        self.assertTrue(self._has(result, "C07"), result["blocking"])

    # C08: word count out of range (too low)
    def test_c08_word_count_too_low_is_blocking(self):
        post = "# Title with Claude Code 99 percent\n\n" + ("Word " * 50)
        result = self.engine.validate_post(post)
        self.assertTrue(self._has(result, "C08"), result["blocking"])

    # C08: word count out of range (too high)
    def test_c08_word_count_too_high_is_blocking(self):
        post = make_good_post() + "\n\n" + ("Word " * 3000)
        result = self.engine.validate_post(post)
        self.assertTrue(self._has(result, "C08"), result["blocking"])

    # C09: fewer than 5 of the 7 success forces detected
    def test_c09_too_few_success_forces_is_blocking(self):
        # No confession, no trade-off, no specifics, no high-intent terms,
        # no trending product, no imperative anchor — bland prose only.
        post = "# An Article About Generic Topics\n\n" + (
            "This is a sentence about ideas. " * 400
        )
        result = self.engine.validate_post(post)
        self.assertTrue(self._has(result, "C09"), result["blocking"])

    # C10: banned phrase present
    def test_c10_banned_phrase_present_is_blocking(self):
        post = make_good_post(
            extra_tail="Hope this helps anyone who reads it.",
        )
        result = self.engine.validate_post(post)
        self.assertTrue(self._has(result, "C10"), result["blocking"])

    # C11: title missing a number
    def test_c11_title_lacks_number_is_blocking(self):
        post = make_good_post(
            title="# Claude Code Made Free Using Ollama and OpenRouter"
        )
        result = self.engine.validate_post(post)
        self.assertTrue(self._has(result, "C11"), result["blocking"])

    # C11: no H1 title at all
    def test_c11_no_h1_title_is_blocking(self):
        post = make_good_post()
        # Strip every line that starts with a single "# "
        post = "\n".join(
            line
            for line in post.split("\n")
            if not (line.startswith("# ") and not line.startswith("## "))
        )
        result = self.engine.validate_post(post)
        self.assertTrue(self._has(result, "C11"), result["blocking"])


class TestTitlePromptBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ViralEngine()

    def test_title_prompt_contains_formula_and_templates(self):
        prompt = self.engine.build_title_prompt(
            "Deploying LangGraph agents on AWS Lambda with cold-start tricks",
            "LangGraph on Lambda",
        )
        self.assertIn("PRIMARY FORMULA", prompt)
        self.assertIn("T01_cost_killer", prompt)
        self.assertIn("T05_anti_pattern", prompt)
        self.assertIn("SCORING RUBRIC", prompt)
        self.assertIn("strict json", prompt.lower())

    def test_title_prompt_includes_source_excerpt(self):
        marker = "UNIQUEMARKER42"
        prompt = self.engine.build_title_prompt(f"Some content {marker} here", "")
        self.assertIn(marker, prompt)


class TestCorrectionPromptBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ViralEngine()

    def test_no_blocking_returns_empty_correction(self):
        empty = self.engine.build_correction_prompt(
            "irrelevant", {"blocking": [], "warnings": []}
        )
        self.assertEqual(empty, "")

    def test_blocking_issues_appear_in_correction(self):
        issues = {
            "blocking": [
                "C08 - word count 100 outside range",
                "C03 - career CTA block missing",
            ],
            "warnings": [],
        }
        prompt = self.engine.build_correction_prompt("draft markdown", issues)
        self.assertIn("C08", prompt)
        self.assertIn("C03", prompt)
        self.assertIn("draft markdown", prompt)
        self.assertIn("Revise the draft", prompt)


class TestConfigLoaded(unittest.TestCase):
    """Smoke checks against the loaded config so a corrupt JSON file
    fails CI instead of silently degrading at runtime."""

    @classmethod
    def setUpClass(cls):
        cls.engine = ViralEngine()

    def test_engine_version_present(self):
        self.assertIn("engine_version", self.engine.config)

    def test_seven_success_forces_all_present(self):
        forces = self.engine.config["seven_success_forces"]
        named = [k for k in forces if k.startswith("force_")]
        self.assertEqual(len(named), 7, named)

    def test_five_title_templates_all_present(self):
        templates = self.engine.config["title_engine"]["templates"]
        self.assertEqual(len(templates), 5)
        ids = {t["id"] for t in templates}
        self.assertEqual(
            ids,
            {
                "T01_cost_killer",
                "T02_hidden_capability",
                "T03_comparison_stack",
                "T04_builders_playbook",
                "T05_anti_pattern",
            },
        )

    def test_author_profile_has_real_urls(self):
        author = self.engine.config["author_profile"]
        self.assertIn("@", author["email"])
        self.assertTrue(author["linkedin_url"].startswith("https://"))
        self.assertTrue(author["upwork_url"].startswith("https://"))
        self.assertTrue(author["fiverr_url"].startswith("https://"))

    def test_self_check_rubric_has_twelve_items(self):
        checks = self.engine.config["self_check_rubric"]["required_checks"]
        self.assertEqual(len(checks), 12)


if __name__ == "__main__":
    unittest.main(verbosity=2)
