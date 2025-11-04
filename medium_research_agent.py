import re
from typing import Dict, List

MEDIUM_BEST_PRACTICES = {
    "structure": {
        "hook_types": ["Bold claim", "Personal story", "Surprising stat", "Question", "Misconception"],
        "paragraph_max_sentences": 3,
        "heading_frequency_words": 400
    },
    "formatting": {
        "use_bold_for_key_points": True,
        "short_paragraphs": True,
        "single_sentence_impact": True
    },
    "engagement": {
        "conversational_tone": True,
        "use_first_person": True,
        "include_numbers": True,
        "active_voice_min": 80
    },
    "viral_elements": {
        "power_words": ["Secret", "Proven", "Ultimate", "Transform", "Master", "Unleash"],
        "title_formulas": [
            "[Number] Ways to [Benefit]",
            "How I [Achievement] in [Time]",
            "Why [Belief] is Wrong",
            "The Ultimate Guide to [Topic]"
        ]
    }
}

def get_medium_style_enhancement() -> str:
    return """
=== MEDIUM POST EXCELLENCE STANDARDS ===

STRUCTURE:
- Hook: Start with bold claim, surprising fact, or personal story (1-2 sentences)
- Context: Set up the problem (2-3 short paragraphs)
- Main Content: Clear H2 subheadings every 300-500 words
- Conclusion: Actionable takeaway + clear next step

FORMATTING:
- Paragraphs: 2-3 sentences MAX
- Use single-sentence paragraphs for impact
- Bold key insights and important points
- Add H2 every 300-500 words, H3 for subsections
- Strategic whitespace between sections

ENGAGEMENT:
- Write conversationally (use "you", "I", "we")
- Include specific numbers and data
- Use active voice (80%+)
- Simple, powerful language
- Scannable content

HOOKS (choose one):
- "You're missing out on [specific benefit]"
- "Here's what nobody tells you about [topic]"
- "I [achieved X] in [timeframe]. Here's how."
- "Stop [common practice]. Do this instead."
- "The truth about [topic] that [industry] won't tell you"

CREDIBILITY:
- Share personal experience with numbers
- Include data or research
- Show before/after transformation
- Be specific, not generic
- Prove claims with examples

APPLY TO EVERY SECTION OF THE POST.
"""

def apply_medium_practices_to_prompt(base_prompt: str, topic: str) -> str:
    enhancement = get_medium_style_enhancement()
    
    return f"""{base_prompt}

{enhancement}

SPECIFIC FOR THIS POST:
Topic: {topic}

REQUIREMENTS:
1. Start with a hook that stops scrolling
2. Use transformation framework (problem → solution → result)
3. Include 3-5 specific numbers/data points
4. Break into scannable chunks with clear subheadings
5. End with 3 clear action steps
6. MINIMUM 1000 words - TARGET 1200-1800 words
7. Create 6-8 major sections, each 200-350 words minimum
8. Extract and use ALL details from provided context (YouTube transcript, supporting links)

Make this IRRESISTIBLE to Medium readers with 2000+ clap potential.
"""

def get_viral_title_formulas(topic: str) -> List[str]:
    return [
        f"The Ultimate Guide to {topic} (2025 Edition)",
        f"How I Mastered {topic} in 30 Days",
        f"Why Everything You Know About {topic} is Wrong",
        f"7 Proven Strategies to Transform Your {topic}",
        f"Stop Doing {topic} Wrong: The Secret Method That Works",
        f"I Made [Result] with {topic}. Here's My Exact Process.",
        f"{topic}: What the Experts Won't Tell You",
        f"The {topic} Playbook: From Zero to Hero",
        f"{topic} Breakthrough: The Method That Changed Everything",
        f"Unlock {topic}: The Step-by-Step System"
    ]

def optimize_content_structure(content: str) -> str:
    lines = content.split('\n')
    optimized = []
    current_para = []
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            if current_para:
                para_text = ' '.join(current_para)
                sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', para_text) if s.strip()]
                
                if len(sentences) > 4:
                    optimized.append(' '.join(sentences[:2]))
                    optimized.append('')
                    optimized.append(' '.join(sentences[2:]))
                else:
                    optimized.append(para_text)
                current_para = []
            optimized.append('')
        elif stripped.startswith('#'):
            if current_para:
                optimized.append(' '.join(current_para))
                current_para = []
                optimized.append('')
            optimized.append(stripped)
        else:
            current_para.append(stripped)
    
    if current_para:
        optimized.append(' '.join(current_para))
    
    return '\n'.join(optimized)

def add_strategic_formatting(content: str) -> str:
    lines = content.split('\n')
    formatted = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        if stripped and not stripped.startswith('#'):
            if 'important' in stripped.lower() or 'key' in stripped.lower() or 'critical' in stripped.lower():
                words = stripped.split()
                if len(words) > 10:
                    key_phrase_start = max(0, len(words) // 3)
                    key_phrase_end = min(len(words), key_phrase_start + 5)
                    words[key_phrase_start] = f"**{words[key_phrase_start]}"
                    words[key_phrase_end - 1] = f"{words[key_phrase_end - 1]}**"
                    stripped = ' '.join(words)
        
        formatted.append(stripped if stripped else '')
    
    return '\n'.join(formatted)

def analyze_medium_readiness(content: str) -> Dict:
    words = len(content.split())
    paragraphs = [p for p in content.split('\n\n') if p.strip() and not p.strip().startswith('#')]
    
    sentences_per_para = []
    for para in paragraphs:
        sentences = [s for s in re.split(r'[.!?]+', para) if s.strip()]
        sentences_per_para.append(len(sentences))
    
    avg_sentences = sum(sentences_per_para) / len(sentences_per_para) if sentences_per_para else 0
    
    h2_count = content.count('\n## ')
    h3_count = content.count('\n### ')
    bold_count = content.count('**') // 2
    
    heading_frequency = words / (h2_count + 1) if h2_count > 0 else words
    
    short_paras = len([s for s in sentences_per_para if s <= 3])
    short_para_ratio = short_paras / len(sentences_per_para) if sentences_per_para else 0
    
    score = 0
    if avg_sentences <= 3:
        score += 25
    elif avg_sentences <= 4:
        score += 15
    
    if heading_frequency <= 500:
        score += 25
    elif heading_frequency <= 700:
        score += 15
    
    if short_para_ratio >= 0.6:
        score += 25
    elif short_para_ratio >= 0.4:
        score += 15
    
    if bold_count >= words / 150:
        score += 25
    elif bold_count >= words / 250:
        score += 15
    
    return {
        "medium_readiness_score": score,
        "avg_sentences_per_paragraph": round(avg_sentences, 1),
        "heading_frequency": round(heading_frequency),
        "short_paragraph_ratio": round(short_para_ratio * 100),
        "bold_usage_count": bold_count,
        "recommendations": get_recommendations(score, avg_sentences, heading_frequency, short_para_ratio, bold_count, words)
    }

def get_recommendations(score: int, avg_sent: float, heading_freq: float, short_ratio: float, bold: int, words: int) -> List[str]:
    recs = []
    
    if avg_sent > 3:
        recs.append("Break paragraphs into 2-3 sentences for better readability")
    
    if heading_freq > 500:
        recs.append("Add more H2 subheadings (target: every 300-500 words)")
    
    if short_ratio < 0.5:
        recs.append("Use more short paragraphs for visual appeal")
    
    if bold < words / 200:
        recs.append("Bold more key insights to help readers scan content")
    
    if score >= 75:
        recs.append("Excellent! This post follows Medium best practices")
    elif score >= 50:
        recs.append("Good structure. Minor tweaks will boost engagement")
    else:
        recs.append("Needs improvement. Focus on shorter paragraphs and more subheadings")
    
    return recs
