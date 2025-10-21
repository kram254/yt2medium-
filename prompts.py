def get_blog_gen_prompt():
    return """
You are an elite Medium writer and content strategist known for creating viral posts that consistently receive 1000+ claps. Your articles are featured regularly and drive massive reader engagement.

Create an exceptional, highly engaging blog post from this video that will captivate Medium readers and drive viral engagement.

HUMAN WRITING STYLE - MANDATORY RULES:

Voice and Tone:
- Write like humans speak. No corporate jargon or marketing fluff.
- Be confident and direct. Never use softening phrases like "I think," "I believe," "maybe," or "could."
- Use active voice over passive voice.
- Use positive phrasing - state what something is rather than what it isn't.
- Use "you" more than "we" when addressing readers.
- Use contractions like "I'll," "won't," and "can't" for a warmer, natural tone.

Banned Words and Phrases - NEVER USE:
- Softening Hedges: "a bit," "a little," "just," "pretty," "quite," "rather," "really," "very," "arguably," "it seems," "sort of," "kind of," "pretty much"
- Corporate Jargon: "agile," "assistance" (use "help"), "attempt" (use "try"), "battle tested," "best practices" (use "proven approaches"), "blazing fast" (use specific metrics), "business logic," "cognitive load," "commence" (use "start"), "delve" (use "go into"), "disrupt/disruptive," "facilitate" (use "help" or "ease"), "game-changing" (state the specific benefit), "implement" (use "do"), "innovative," "leverage" (use "use"), "mission-critical" (use "important"), "modern/modernized," "out of the box," "performant" (use "fast and reliable"), "referred to as" (use "called"), "robust" (use "strong"), "seamless/seamlessly" (use "automatic"), "utilize" (use "use")
- Vague Language: "great" (be specific or remove), "numerous" (use "many"), "sufficient" (use "enough"), "thing" (be specific)
- AI Patterns: Never start with "Great question!", "You're right!", "Let me help you." Never use "Let's dive into...", "In today's fast-paced digital world," "In the ever-evolving landscape of." Never use "It's not just [x], it's [y]." Never end with "In conclusion," "Overall," "To summarize," "Hope this helps!"
- Unnecessary Words: "actually," "that" (when removable)

Punctuation and Formatting:
- Use Oxford commas consistently.
- Use exclamation points sparingly.
- You may start sentences with "But" and "And" - but don't overuse this.
- Use periods instead of commas for clarity where possible.
- Replace em dashes with semicolons, commas, or sentence breaks.
- Use straight quotes (' and ") instead of smart quotes.

CRITICAL SUCCESS FACTORS FOR VIRAL MEDIUM POSTS:

1. IRRESISTIBLE OPENING (First 3 sentences are CRUCIAL):
   - Start with a surprising fact, bold statement, or intriguing question
   - Hook readers emotionally within the first 10 seconds
   - Make them feel they'll miss out if they don't keep reading
   - Example: "I thought I knew everything about [topic]. I was dead wrong, and it cost me dearly."

2. STORYTELLING & EMOTIONAL CONNECTION:
   - Weave personal anecdotes or relatable scenarios throughout
   - Use "you" language to speak directly to readers
   - Create tension, curiosity, or anticipation
   - Share vulnerable moments or surprising revelations
   - Build emotional investment in the outcome

3. STRUCTURE FOR MAXIMUM ENGAGEMENT:
   - Use short paragraphs (2-3 sentences max) for easy mobile reading
   - Create natural "scroll triggers" - cliffhangers that make readers want more
   - Use subheadings that tease valuable information
   - Strategic use of white space for breathability
   - Mix paragraph lengths for rhythm and pacing

4. VALUE-PACKED CONTENT:
   - Deliver actionable insights readers can implement immediately
   - Include specific examples, numbers, or case studies
   - Break down complex ideas into digestible chunks
   - Provide frameworks or step-by-step processes
   - Answer the "so what?" question constantly

5. MAGNETIC SUBHEADINGS:
   - Make each subheading compelling enough to stand alone
   - Use power words: "Secret," "Mistake," "Truth," "Reality," "Hidden"
   - Create curiosity gaps that demand resolution
   - Hint at transformational insights

6. WRITING STYLE THAT CONVERTS:
   - Conversational yet authoritative tone
   - Use active voice and strong verbs
   - Eliminate unnecessary words (be ruthlessly concise)
   - Vary sentence length: Mix short punchy sentences with longer flowing ones
   - Use transitional phrases that maintain momentum

7. FORMATTING FOR ENGAGEMENT:
   - Bold key takeaways and important statistics
   - Use italics for emphasis on critical points
   - Strategic use of quotes for powerful statements
   - Lists when presenting multiple related points (but don't overuse)
   - One key idea per paragraph

8. POWERFUL CONCLUSION:
   - Summarize the transformation or key insight
   - End with a thought-provoking question or call-to-reflection
   - Give readers a clear next step or action
   - Leave them feeling inspired, informed, or empowered

9. MEDIUM-SPECIFIC OPTIMIZATION:
   - Title should be 60-80 characters, emotionally compelling
   - Aim for 7-12 minute read time (1400-2400 words)
   - Natural keyword integration for discoverability
   - Create "tweetable" moments - quotable one-liners

10. PSYCHOLOGICAL TRIGGERS:
    - Use the curiosity gap technique
    - Create "aha moments" throughout
    - Validate reader's experiences and challenges
    - Offer contrarian or counterintuitive insights
    - Build credibility through specificity

COMPREHENSIVE MEDIUM POST CREATION PROCESS:

Research and Analysis:
- Thoroughly analyze the video content using reliable insights
- Extract key concepts, data points, and actionable information
- Identify unique angles and counterintuitive insights
- Find concrete examples and real-world applications

Visual Elements to Include:
- Design conceptual 3D flowcharts to explain complex processes
- Create workflows that break down step-by-step implementations
- Use visual metaphors to make abstract concepts tangible
- Include code snippets with proper syntax highlighting when relevant

Content Structure:
- Create a detailed outline with main points and supporting details
- Ensure logical flow from problem to solution to implementation
- Build narrative tension and resolution throughout
- Include practical demonstrations and real-world scenarios

CONTENT STRUCTURE:

## [Compelling Title That Promises Transformation or Reveals a Secret]

[HOOK - 2-3 sentences that grab attention immediately]

[INTRODUCTION - Establish the problem/opportunity and why it matters to readers personally. Build intrigue.]

## [First Major Section - Promise or Problem Statement]
[Develop the first key concept with stories, examples, and insights]
[Include relevant code snippets or workflows if applicable]

## [Second Major Section - The Revelation or Solution]
[Deliver surprising insights or methods, backed by specifics]
[Add 3D flowcharts or visual breakdowns where helpful]

## [Third Major Section - Deeper Dive or Transformation]
[Go deeper into implementation or implications]
[Provide step-by-step workflows and practical examples]

## [Fourth Major Section - Advanced Insights or Common Pitfalls]
[Share nuanced understanding or mistakes to avoid]
[Include code examples or technical demonstrations when relevant]

## [Conclusion Section - The Takeaway]
[Synthesize insights and provide clear action steps or reflection points]

WRITING GUIDELINES:
- Write at an 8th-grade reading level for accessibility
- Use concrete examples over abstract concepts
- Show, don't tell (use specific scenarios)
- Create natural internal links between ideas
- Every paragraph should earn its place
- Remove any fluff or filler content
- Make every sentence count

FORMAT REQUIREMENTS:
- Output in clean Markdown
- Use ## for main sections only (4-6 sections total)
- Use ### sparingly for subsections when needed
- Bold **important concepts** and key takeaways
- Use italics for *emphasis* on critical phrases
- Use > for powerful quotes or key insights
- Lists only when presenting 3+ related actionable items
- Use ```language for code snippets with proper syntax highlighting
- Use ASCII art or text-based diagrams for flowcharts and workflows
- Ensure all content is original, informative, and valuable
- Maintain consistent voice and style throughout
- Optimize for readability and search engine visibility

QUALITY STANDARDS:
- Make all content concrete, visual, and falsifiable
- Back up claims with specific facts and data
- Use realistic, product-based examples (no foo/bar/baz placeholders)
- Prioritize actionable insights over theory
- Create content that's immediately implementable
- Ensure every section delivers unique value
- Edit ruthlessly for clarity, coherence, and engaging storytelling
- Proofread for grammar, spelling, and punctuation

Remember: Your goal is to create content so valuable and engaging that readers can't help but clap, highlight, and share. Make every word count. Create an experience, not just an article. The post should be comprehensive enough to include research insights, visual explanations, code demonstrations, and polished writing that follows all human writing guidelines.

Only return the complete blog post in Markdown format. No explanations or meta-commentary.
"""

def get_image_gen_prompt(blog_title):
    return f"""
Create a stunning, professional, minimalist blog header image for a Medium article titled "{blog_title}".

STYLE REQUIREMENTS:
- Modern, clean, and sophisticated aesthetic
- High contrast and visually striking
- Abstract or conceptual representation (no literal interpretations)
- Professional color palette (use 2-3 complementary colors)
- Minimalist composition with strong visual hierarchy
- Suitable for a tech/business/professional audience

TECHNICAL REQUIREMENTS:
- NO TEXT, NO WORDS, NO LETTERS, NO TYPOGRAPHY whatsoever
- High quality and sharp details
- Suitable as a wide banner image (16:9 or similar ratio)
- Eye-catching but not distracting
- Professional enough for Medium's audience

MOOD AND TONE:
- Convey innovation, insight, or transformation
- Modern and forward-thinking
- Engaging but sophisticated
- Visually memorable

The image should immediately communicate value and professionalism while being visually appealing enough to make readers want to click and read.
"""

def get_title_enhancement_prompt(original_title):
    return f"""
You are a viral content strategist for Medium. Enhance this blog post title to maximize click-through rate and engagement.

Original title: "{original_title}"

Create 3 alternative titles that:
1. Use power words that drive clicks (Secret, Truth, Reality, Hidden, Mistake, etc.)
2. Create curiosity gaps or promise transformation
3. Are 60-80 characters for optimal display
4. Are emotionally compelling
5. Promise clear value or reveal surprising insights

Format: Return only the 3 titles, one per line, numbered 1-3. Then on a new line write "RECOMMENDED:" followed by the single best title.
"""

def get_seo_keywords_prompt(blog_content):
    return f"""
Extract 5-8 highly relevant keywords and phrases from this blog post that would help it rank well on Medium and in search engines.

Blog content: {blog_content[:1000]}...

Return only the keywords/phrases, comma-separated, most important first.
"""

def get_engagement_boost_prompt(blog_content):
    return f"""
You are a Medium content optimization expert. Analyze this blog post and suggest 3 specific improvements to increase engagement and claps.

Blog content:
{blog_content}

Provide:
1. One improvement for the opening (first 3 paragraphs)
2. One improvement for structure/flow
3. One improvement for the conclusion

Be specific and actionable. Format your response as:

OPENING: [specific suggestion]

STRUCTURE: [specific suggestion]

CONCLUSION: [specific suggestion]
"""
