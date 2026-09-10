"""
Trend Research module — powered by last30days methodology.
Based on https://github.com/mvanhorn/last30days-skill

Replaces the generic AI-guess approach in the Surprise Me endpoint
with a research-backed prompt that instructs the AI to source trends
from real social signals (Reddit upvotes, X engagement, YouTube views,
HN points, GitHub stars) and score them by actual community engagement
rather than editorial guesswork.
"""

from datetime import datetime


def get_last30days_surprise_prompt(topics_of_interest=None, excluded_topics=None):
    """
    Build a Surprise Me prompt using the last30days research methodology.

    Instead of asking the AI to guess what's trending, this prompt instructs
    it to think like the last30days engine: score topics by real community
    engagement signals (upvotes, likes, views, stars) across multiple
    platforms, and surface only topics with verifiable recent activity.

    Args:
        topics_of_interest: Optional list of user preference topics
        excluded_topics: Optional list of topics to skip

    Returns:
        str: The complete prompt for the AI manager
    """
    current_date = datetime.now().strftime("%B %d, %Y")

    prompt = f"""You are a research-driven content strategist using the /last30days methodology.
Today is {current_date}.

Your job: identify the TOP 3 most trending topics in AI, ML, LLMs, developer tools,
and open-source right now by reasoning about REAL community engagement signals -
not by guessing what sounds trendy.

## How to think about this (last30days scoring methodology)

For each topic you suggest, you must be able to point to SPECIFIC verifiable signals:

- Reddit: actual subreddits where this is being discussed, approximate upvote ranges
  you've seen in training (r/MachineLearning, r/LocalLLaMA, r/programming, etc.)
- X/Twitter: notable accounts or threads discussing this
- YouTube: specific channels or videos covering this topic recently
- Hacker News: whether this hit the front page, approximate point ranges
- GitHub: repos with recent star surges, new releases, or trending status

A Reddit thread with 1,500 upvotes is a stronger signal than a blog post nobody read.
A GitHub repo gaining 5K stars in a week tells you more than a press release.
Score by what real people actually engage with - social relevancy, not SEO relevancy.

## Output format

Return ONLY a raw JSON object with no markdown fences, no prose, no explanation.

The JSON must have exactly this structure:
{{"cards": [
  {{
    "rank": 1,
    "rank_badge": "#1 Trending",
    "headline": "punchy 6-10 word title about the SPECIFIC tool/model/release",
    "subtext": "one sentence hook with a concrete fact or number",
    "why_now": "what specific event or release made this blow up this week",
    "evidence": {{
      "reddit": "r/subreddit - approximate engagement",
      "twitter": "key accounts/threads discussing this",
      "youtube": "channels covering this",
      "github": "repo name if applicable, star count",
      "hackernews": "front page status if applicable"
    }},
    "platforms": ["x_twitter", "youtube"],
    "composite_score": 88,
    "estimated_read_time": "9 min read",
    "keywords": ["kw1", "kw2", "kw3"],
    "chat_input_prompt": "Write a complete publish-ready Medium blog post titled [SPECIFIC TITLE about the SPECIFIC tool/model]. Angle: [SPECIFIC ANGLE grounded in the community discussion]. The article must cover: (1) Hook with bold technical claim backed by the community reaction, (2) Background and why this matters now - reference the specific release/event, (3) Technical deep dive with Python code example showing actual usage, (4) Real-world use cases discussed by the community, (5) Critical perspective - what the skeptics on Reddit/HN are saying and whether they have a point, (6) Actionable takeaways the reader can apply this week. Tone: technical but accessible, first-person, no fluff. Write like a developer sharing what they learned, not a marketer. Target reader: senior developer or ML engineer. Length: 1800-2400 words. Medium tags: [TAG1, TAG2, TAG3, TAG4, TAG5]. End with a specific CTA."
  }},
  {{"rank": 2, ...same shape...}},
  {{"rank": 3, ...same shape...}}
]}}

## Rules

- All 3 topics must be DIFFERENT with no overlap.
- composite_score: 60-100, based on cross-platform signal strength.
- Every topic MUST reference a specific tool, model, paper, release, or event -
  not a vague category like "AI agents" or "LLM optimization."
- chat_input_prompt must be at least 350 characters and name the specific subject.
- The "evidence" field must cite real platforms and approximate engagement.
- platforms array: x_twitter, youtube, instagram, reddit, medium only.
- Focus on releases, launches, or discussions from the past 7-14 days as of {current_date}.
- Do NOT hallucinate trends. If you cannot cite a specific signal, pick a different topic.
"""

    if topics_of_interest:
        prompt += "\nUser interests (bias selection toward these): " + ", ".join(str(x) for x in topics_of_interest) + "\n"
    if excluded_topics:
        prompt += "\nExcluded topics (do NOT suggest): " + ", ".join(str(x) for x in excluded_topics) + "\n"

    return prompt
