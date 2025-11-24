def get_section_rewrite_prompt(section_content, instruction):
    return f"""Rewrite this section according to the instruction while following human-like writing rules:

Section Content:
{section_content}

Instruction: {instruction}

HUMAN WRITING RULES:
- Eliminate corporate jargon and marketing fluff
- Be confident and direct (no softening phrases like "I think," "maybe," "could")
- Use active voice over passive voice
- Avoid banned words: "leverage," "utilize," "delve," "facilitate," "seamless," "robust," "innovative," "game-changing," "best practices," "blazing fast"
- Replace vague words with specific facts and metrics
- No AI patterns: "Let's dive into," "In today's fast-paced," "Great question," "Hope this helps"
- No essay closers: "In conclusion," "Overall," "To summarize"
- Use contractions for natural tone (I'll, won't, can't)
- Use straight quotes (' and ") instead of smart quotes
- Use Oxford commas consistently

Return ONLY the rewritten section in Markdown format. Maintain the same heading level and structure.
"""

def get_tone_adjustment_prompt(content, target_tone):
    tone_instructions = {
        'funnier': 'Make this more humorous and entertaining while keeping the core information. Add wit, clever observations, or light jokes.',
        'professional': 'Make this more professional and polished. Use formal language, remove casual expressions, focus on credibility.',
        'simpler': 'Simplify this content for easier understanding. Use simpler words, shorter sentences, explain technical terms.',
        'technical': 'Make this more technical and detailed. Add technical depth, specifications, and assume expert audience.',
        'casual': 'Make this more casual and conversational. Use friendly tone, contractions, and relatable language.',
        'academic': 'Make this more academic and scholarly. Use formal structure, cite concepts, maintain rigor.',
        'energetic': 'Make this more energetic and enthusiastic. Use active voice, strong verbs, create excitement.',
        'concise': 'Make this more concise without losing key information. Remove fluff, tighten sentences, be direct.'
    }
    
    instruction = tone_instructions.get(target_tone, f'Adjust the tone to be more {target_tone}')
    
    return f"""Adjust the tone of this content while maintaining human-like writing:

{content}

{instruction}

HUMAN WRITING RULES (apply to all tone adjustments):
- Avoid corporate jargon: no "leverage," "utilize," "robust," "seamless," "innovative," "game-changing"
- Be specific: replace vague words with concrete facts and metrics
- No AI patterns: avoid "Let's dive into," "In today's fast-paced," "Hope this helps"
- Use contractions for natural tone (I'll, won't, can't)
- Eliminate softening phrases ("I think," "maybe," "could," "perhaps," "arguably")
- No essay closers: "In conclusion," "Overall," "To summarize"
- Use active voice over passive voice

Maintain all key information and structure. Return the complete adjusted content in Markdown format.
"""

def get_expand_prompt(section_content, target_words=None):
    target_instruction = f" to approximately {target_words} words" if target_words else ""
    
    return f"""Expand this section with more detail, examples, and insights{target_instruction}:

{section_content}

Add:
- More specific examples with concrete metrics and data
- Deeper explanations without corporate jargon
- Additional context using real-world scenarios
- Supporting details that are falsifiable and verifiable
- Practical insights readers can implement

HUMAN WRITING RULES:
- Use specific facts instead of vague superlatives
- Avoid banned words: "leverage," "utilize," "delve," "robust," "seamless," "innovative"
- No AI patterns like "Let's dive into" or "In today's fast-paced world"
- Be confident and direct (no "I think," "maybe," "perhaps")
- Use contractions for natural tone
- Replace placeholder examples (foo/bar) with realistic ones

Return the expanded section in Markdown format.
"""

def get_compress_prompt(section_content, target_words=None):
    target_instruction = f" to approximately {target_words} words" if target_words else ""
    
    return f"""Compress this section{target_instruction} while keeping the essential information:

{section_content}

Remove:
- Redundant points
- Excessive examples
- Filler words
- Unnecessary details

Keep the core message and key insights. Return the compressed section in Markdown format.
"""

def get_title_alternatives_prompt(original_title, content_excerpt):
    return f"""Generate 10 alternative titles for this blog post.

Original Title: {original_title}

Content Preview:
{content_excerpt[:500]}

Create titles that are:
- 60-80 characters long
- Use power words that drive clicks (avoid corporate jargon)
- Promise value or transformation with specific claims
- Create curiosity without clickbait
- Are specific and concrete (no vague words like "great" or "numerous")
- Use numbers where appropriate
- Make a clear promise so readers know what they'll get
- Tap into relevant, controversial points backed by data

AVOID in titles:
- Corporate jargon: "game-changing," "innovative," "disruptive," "best practices"
- Vague phrases: "The future of," "Modern approaches to"
- Generic promises without specifics

Return as a numbered list (1-10) with just the titles, no explanations.
"""

def get_meta_description_prompt(title, content):
    return f"""Create an SEO-optimized meta description for this blog post.

Title: {title}

Content:
{content[:1000]}

Requirements:
- 150-160 characters
- Include primary keyword naturally
- Create curiosity or promise value
- Make it click-worthy
- Use active voice

Return ONLY the meta description, nothing else.
"""

def get_fact_check_prompt(claim, context=""):
    return f"""Analyze this claim for accuracy:

Claim: {claim}

{f"Context: {context}" if context else ""}

Provide:
1. Verification status (Accurate/Partially Accurate/Inaccurate/Unverifiable)
2. Evidence or corrections
3. Reliable sources to verify
4. Suggested revision if needed

Be objective and cite credible sources.
"""

def get_alternative_angle_prompt(section_content):
    return f"""Rewrite this section from a completely different angle or perspective:

{section_content}

Consider:
- Contrarian viewpoint backed by specific data
- Different industry perspective with concrete examples
- Alternative use case from real-world scenarios
- Counterintuitive approach with verifiable claims
- Fresh metaphor or framing that's immediately understandable

HUMAN WRITING RULES:
- Avoid corporate jargon and marketing fluff
- Be specific with facts and metrics (no vague language)
- No AI patterns or essay closers
- Use active voice and contractions for natural tone
- Make claims concrete, visual, and falsifiable

Return the rewritten section in Markdown format.
"""

def get_code_improvement_prompt(code_snippet, language):
    return f"""Improve this {language} code for production-readiness:

```{language}
{code_snippet}
```

Enhance:
- Error handling
- Edge cases
- Code organization
- Best practices
- Performance
- Comments (only where truly needed)

Return the improved code with brief explanation of changes.
"""

def get_add_examples_prompt(concept, context):
    return f"""Add 2-3 concrete, realistic examples to illustrate this concept:

Concept: {concept}

Context:
{context}

Examples should be:
- Specific and realistic (no foo/bar placeholders)
- From real-world scenarios with verifiable details
- Easy to understand without corporate jargon
- Immediately actionable with clear metrics when possible
- Written in natural, human-like language

HUMAN WRITING RULES:
- Use specific facts and data instead of vague superlatives
- Avoid banned words: "leverage," "utilize," "robust," "seamless," "innovative"
- No AI patterns or softening phrases
- Write with confidence using active voice
- Use contractions for warmth (I'll, won't, can't)

Return the examples with brief explanations in Markdown format.
"""

def get_section_split_prompt(long_section):
    return f"""Split this long section into 2-3 well-organized shorter sections with clear headings:

{long_section}

Each section should:
- Have a descriptive H2 or H3 heading
- Focus on one main idea
- Be 150-250 words
- Flow naturally to the next

Return the split sections in Markdown format.
"""

def get_transition_improvement_prompt(section1, section2):
    return f"""Create a smooth transition sentence between these two sections:

Section 1 ending:
{section1[-200:]}

Section 2 beginning:
{section2[:200]}

Write 1-2 sentences that naturally bridge these sections, creating flow and connection.
Return ONLY the transition sentences.
"""
