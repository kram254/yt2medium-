TEMPLATES = {
    'tutorial': {
        'name': 'Tutorial / How-To Guide',
        'structure': """
Create a comprehensive tutorial-style blog post.

STRUCTURE:
1. Introduction - What readers will learn and why it matters
2. Prerequisites - What readers need before starting
3. Step-by-step implementation with code examples
4. Common pitfalls and troubleshooting
5. Best practices and optimization tips
6. Conclusion with next steps

STYLE: Clear, instructional, beginner-friendly with detailed explanations.
""",
        'tone': 'instructional'
    },
    
    'case_study': {
        'name': 'Case Study / Success Story',
        'structure': """
Create a compelling case study blog post.

STRUCTURE:
1. The Challenge - Set the scene with the problem
2. The Context - Background and constraints
3. The Solution - What was implemented (with technical details)
4. The Results - Measurable outcomes and metrics
5. Key Learnings - What worked and what didn't
6. Actionable Takeaways - How readers can apply this

STYLE: Story-driven, data-focused, results-oriented with real metrics.
""",
        'tone': 'professional'
    },
    
    'opinion': {
        'name': 'Opinion Piece / Hot Take',
        'structure': """
Create a thought-provoking opinion piece.

STRUCTURE:
1. Bold Statement - Controversial or counterintuitive claim
2. Why This Matters - Context and implications
3. Supporting Arguments - Evidence and reasoning (3-4 points)
4. Counterarguments - Address opposing views
5. Real-World Examples - Concrete scenarios
6. Call to Action - What readers should do/think differently

STYLE: Confident, provocative, conversation-starting with strong voice.
""",
        'tone': 'conversational'
    },
    
    'listicle': {
        'name': 'Listicle / Top N',
        'structure': """
Create an engaging listicle blog post.

STRUCTURE:
1. Introduction - Promise and hook
2. Item 1-N - Each with:
   - Clear heading
   - Explanation (100-150 words)
   - Example or code snippet
   - Pro tip or insight
3. Bonus items (if relevant)
4. Conclusion - Summary and action

STYLE: Scannable, punchy, high-value with clear takeaways per item.
""",
        'tone': 'energetic'
    },
    
    'deep_dive': {
        'name': 'Deep Dive / Technical Analysis',
        'structure': """
Create an in-depth technical analysis.

STRUCTURE:
1. Executive Summary - Key findings upfront
2. Background and Context - Why this matters
3. Technical Deep Dive - Detailed analysis (3-4 sections)
4. Architecture and Implementation - With diagrams
5. Performance Analysis - Benchmarks and metrics
6. Best Practices - Production-ready recommendations
7. Conclusion and Future Considerations

STYLE: Authoritative, detailed, technical with depth and nuance.
""",
        'tone': 'technical'
    },
    
    'story': {
        'name': 'Personal Story / Journey',
        'structure': """
Create a compelling personal narrative.

STRUCTURE:
1. The Hook - Captivating opening scene
2. The Setup - Background and context
3. The Journey - Challenges, decisions, turning points
4. The Transformation - What changed
5. The Lessons - Insights gained
6. The Application - How readers can benefit

STYLE: Authentic, vulnerable, relatable with emotional connection.
""",
        'tone': 'personal'
    },
    
    'comparison': {
        'name': 'Comparison / A vs B',
        'structure': """
Create a comprehensive comparison post.

STRUCTURE:
1. Introduction - What's being compared and why
2. Overview - Brief intro of each option
3. Comparison Criteria (4-6 key factors):
   - Feature comparison
   - Performance benchmarks
   - Use cases
   - Pricing/cost analysis
4. Pros and Cons - Side by side
5. Recommendation - When to use which
6. Conclusion - Clear guidance

STYLE: Objective, balanced, data-driven with clear comparisons.
""",
        'tone': 'analytical'
    },
    
    'guide': {
        'name': 'Complete Guide / Ultimate Resource',
        'structure': """
Create a comprehensive, definitive guide.

STRUCTURE:
1. Introduction - Scope and what makes this complete
2. Fundamentals - Core concepts explained
3. Getting Started - First steps
4. Intermediate Topics - Deeper exploration (3-4 sections)
5. Advanced Techniques - Expert-level content
6. Best Practices and Patterns
7. Resources and Tools
8. Conclusion - Mastery roadmap

STYLE: Comprehensive, authoritative, reference-quality with 1500+ words.
""",
        'tone': 'authoritative'
    }
}

TONE_PRESETS = {
    'professional': """
Tone: Professional and polished
- Use industry-standard terminology
- Formal but not stuffy
- Data-driven and evidence-based
- Objective and balanced perspective
- Corporate-friendly language
""",
    
    'conversational': """
Tone: Conversational and friendly
- Write like talking to a colleague over coffee
- Use "you" and "I" frequently
- Include rhetorical questions
- Casual but intelligent
- Relatable examples and analogies
""",
    
    'technical': """
Tone: Technical and precise
- Use accurate technical terminology
- Include specifications and metrics
- Reference documentation and standards
- Code-focused with implementation details
- Assume technical audience
""",
    
    'humorous': """
Tone: Humorous and entertaining
- Include witty observations
- Use pop culture references where appropriate
- Self-deprecating humor occasionally
- Keep it light but valuable
- Don't force jokes - be naturally funny
""",
    
    'academic': """
Tone: Academic and research-focused
- Cite sources and studies
- Use formal structure
- Evidence-based arguments
- Logical progression of ideas
- Reference methodology and research
""",
    
    'instructional': """
Tone: Clear and instructional
- Step-by-step clarity
- Avoid jargon or explain when used
- Anticipate questions
- Patient and thorough
- Beginner-friendly approach
""",
    
    'personal': """
Tone: Personal and authentic
- Share vulnerabilities and failures
- Use first-person narrative
- Emotional honesty
- Personal anecdotes
- Relatable human experiences
""",
    
    'energetic': """
Tone: Energetic and enthusiastic
- Exclamation points (but not excessive)
- Active voice and strong verbs
- Short, punchy sentences
- Create excitement
- Motivational and inspiring
""",
    
    'analytical': """
Tone: Analytical and objective
- Examine multiple perspectives
- Data-driven comparisons
- Logical evaluation
- Pros and cons format
- Unbiased recommendations
""",
    
    'authoritative': """
Tone: Authoritative and expert
- Demonstrate deep knowledge
- Reference industry experience
- Confident assertions
- Share insider insights
- Position as thought leader
"""
}

INDUSTRY_STYLES = {
    'tech': 'Focus on innovation, scalability, and developer experience. Use technical terms confidently.',
    'business': 'Focus on ROI, strategy, and growth. Use business metrics and KPIs.',
    'startup': 'Focus on speed, iteration, and problem-solving. Embrace failure and learning.',
    'creative': 'Focus on inspiration, aesthetics, and storytelling. Use vivid imagery.',
    'science': 'Focus on research, methodology, and evidence. Reference studies and data.',
    'personal_development': 'Focus on transformation, mindset, and action. Use motivational language.'
}

def get_template_prompt(template_key, tone_key=None, industry=None):
    if template_key not in TEMPLATES:
        template_key = 'tutorial'
    
    template = TEMPLATES[template_key]
    prompt_parts = [template['structure']]
    
    tone = tone_key if tone_key and tone_key in TONE_PRESETS else template['tone']
    prompt_parts.append(TONE_PRESETS[tone])
    
    if industry and industry in INDUSTRY_STYLES:
        prompt_parts.append(f"\nIndustry Focus: {INDUSTRY_STYLES[industry]}")
    
    return '\n\n'.join(prompt_parts)
