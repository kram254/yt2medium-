LINKEDIN_BEST_PRACTICES = {
    "post_types": {
        "thought_leadership": {
            "opening": "Start with a bold insight or contrarian take",
            "structure": "Problem → Insight → Action → CTA",
            "tone": "Professional, confident, authoritative"
        },
        "skill_share": {
            "opening": "Lead with value: 'Here's what I learned...'",
            "structure": "Hook → 3-5 actionable tips → Reflection → CTA",
            "tone": "Helpful, experienced, mentor-like"
        },
        "career_milestone": {
            "opening": "Celebrate achievement authentically",
            "structure": "Journey → Lessons → Gratitude → Forward look",
            "tone": "Humble, grateful, inspiring"
        }
    },
    "engagement_tactics": {
        "hooks": [
            "After [X years/months], I learned...",
            "Nobody talks about [insight], but...",
            "Here's what changed my [career/perspective]...",
            "If you're [struggling with X], try this...",
            "The best [advice/lesson] I ever got was..."
        ],
        "cta_patterns": [
            "What's your experience with [topic]?",
            "How would you approach this?",
            "Drop a comment if you agree/disagree",
            "Who else has dealt with this?",
            "What would you add to this list?"
        ]
    },
    "formatting": {
        "line_breaks": "Use line breaks generously for readability",
        "emojis": "1-2 strategic emojis max",
        "hashtags": "3-5 relevant hashtags",
        "length": "150-500 words optimal",
        "lists": "Use bullet points for clarity"
    },
    "content_pillars": [
        "Industry insights and trends",
        "Actionable tips and frameworks",
        "Career lessons and growth",
        "Problem-solving approaches",
        "Thought leadership takes"
    ]
}

def generate_linkedin_post_prompt(medium_title, medium_content):
    return f"""
You are a LinkedIn content expert specializing in professional, high-engagement posts that drive meaningful interactions.

Create a LinkedIn post based on this Medium article:
Title: {medium_title}

Content excerpt: {medium_content[:500]}...

LINKEDIN POST REQUIREMENTS:

STRUCTURE:
1. Hook (1-2 sentences): Grab attention with a bold insight or relatable problem
2. Value (3-5 key points): Share actionable insights or lessons
3. CTA (1-2 sentences): Ask a question or invite engagement

TONE & STYLE:
- Professional yet conversational
- Confident but not arrogant
- Helpful and generous with knowledge
- Authentic and personal touch

FORMATTING:
- Use line breaks between sections
- Keep paragraphs short (1-3 sentences max)
- Add 1-2 strategic emojis
- End with 3-5 relevant hashtags
- Mention skills or expertise demonstrated

ENGAGEMENT TACTICS:
- Start with a question or bold statement
- Include a relatable challenge or insight
- Provide specific, actionable value
- End with a question that invites comments
- Reference the Medium article subtly

LINKEDIN BEST PRACTICES:
- Avoid excessive self-promotion
- Focus on value and learning
- Use "I" and "you" language
- Include specific examples or numbers
- Make it easy to read and scan
- Encourage comments and discussion

Generate a LinkedIn post that:
1. Complements the Medium article
2. Drives engagement and comments
3. Showcases professional expertise
4. Invites meaningful conversation
5. Follows LinkedIn algorithm best practices

Output ONLY the LinkedIn post, ready to copy-paste.
"""

def generate_linkedin_post(medium_title, medium_content, ai_manager):
    try:
        prompt = generate_linkedin_post_prompt(medium_title, medium_content)
        linkedin_post = ai_manager.generate_content(
            prompt,
            medium_content[:1000],
            'gpt-4o'
        )
        return linkedin_post.strip()
    except Exception as e:
        print(f"LinkedIn post generation error: {e}")
        return None
