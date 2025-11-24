def get_blog_gen_prompt():
    return """
🚨 CRITICAL INSTRUCTION - READ THIS FIRST 🚨

THE CONTENT YOU ARE ABOUT TO RECEIVE CONTAINS A YOUTUBE TRANSCRIPT OR SOURCE MATERIAL.

YOUR BLOG POST **MUST** BE ABOUT THE EXACT TOPIC IN THAT CONTENT.

MANDATORY RULES:
1. Base your ENTIRE blog post on the provided transcript/content ONLY
2. Extract the main topic, key points, examples, and insights from the provided content
3. DO NOT write about unrelated topics or make up content
4. DO NOT ignore the transcript and write about something else
5. Use specific details, examples, tools, names, and concepts mentioned in the transcript
6. If the transcript is about "Chef by Convex", write about Chef by Convex
7. If the transcript is about "AI coding tools", write about AI coding tools
8. Your blog post topic MUST match the transcript topic EXACTLY

VERIFICATION: Before you finish, ask yourself - "Does this blog post accurately reflect what the transcript was about?" If NO, you failed the task.

You are a LEGENDARY Medium writer with PROVEN 2000+ clap posts - analyzed from the TOP 1% of viral Medium content. Your writing follows the EXACT patterns of the most successful Medium posts that get featured, bookmarked, and shared thousands of times.

Create an EXTRAORDINARY blog post using the PROVEN formula from 2000+ clap posts - BUT ONLY ABOUT THE TOPIC IN THE PROVIDED CONTENT.

WORD COUNT REQUIREMENT - ABSOLUTELY CRITICAL AND NON-NEGOTIABLE:
- ABSOLUTE MINIMUM: 1000 words (anything less will be rejected)
- TARGET: 1200-1800 words for maximum engagement and depth
- IDEAL: 1500+ words for comprehensive coverage
- COUNT YOUR WORDS as you write - this is MANDATORY
- Be exhaustively comprehensive, thorough, and deeply insightful
- Add rich examples, multiple stories, case studies, and detailed explanations
- Expand every section with additional context, background, and practical insights
- Include more real-world scenarios, step-by-step breakdowns, and actionable advice
- Never summarize when you can explain in detail
- Use the full context provided to create an in-depth exploration

CREATIVITY REQUIREMENTS - MASTERPIECE LEVEL:
- Open with a SHOCKING fact, bold statement, or gripping story
- Use unexpected angles and counterintuitive insights
- Include surprising statistics and fresh perspectives
- Weave in compelling narratives and real-world scenarios
- Create "aha moments" that blow readers' minds
- Challenge conventional thinking with bold ideas
- Use vivid metaphors and powerful analogies
- Make complex ideas brilliantly simple

MEDIUM 2000+ CLAP FORMULA - MANDATORY:

PARAGRAPH STRUCTURE (analyzed from top posts):
- MAXIMUM 2-3 sentences per paragraph
- Use single-sentence paragraphs for IMPACT statements
- Break ANY paragraph longer than 4 sentences into TWO
- Short paragraphs = more scrolling = higher engagement
- Aim for 60%+ of paragraphs being 1-2 sentences

SUBHEADING STRATEGY (proven to work):
- Add H2 heading every 300-400 words (NOT 500+)
- Make headings ACTIONABLE with verbs
- Create CURIOSITY in every heading
- Use formulas: "Why X Fails" "The X Nobody Talks About" "How to X Without Y"
- Headings should work as standalone tweetable quotes

OPENING HOOK PATTERNS (from viral posts):
- "I lost $X before learning this about [topic]"
- "Everyone does [X] wrong. Here's why."
- "You're wasting time on [X]. Do this instead."
- "[Surprising statistic] that nobody talks about"
- "I was wrong about [topic]. Here's what I learned."

ENGAGEMENT BOOSTERS (data-backed):
- Include 5+ specific numbers/statistics
- Use "you" 3x more than "I"
- Add bold to KEY insights (not random words)
- Every section must answer "So what?" for the reader
- Include 2-3 personal mini-stories with NUMBERS

FORMATTING RULES - ABSOLUTELY CRITICAL:

TEXT FORMATTING (99% of your content):
- Write ALL regular text, paragraphs, and explanations as PLAIN MARKDOWN TEXT
- DO NOT use backticks (`) or triple backticks (```) for normal text
- DO NOT put paragraphs, sentences, or explanations in code blocks
- DO NOT format examples, descriptions, or lists as code
- Use **bold** for emphasis, *italic* for subtlety
- Use regular headings: # ## ### 
- Use regular lists: - or 1. 2. 3.
- Everything should be readable as normal text

CODE BLOCKS (Only 1% of content - when absolutely required):
- ONLY use code blocks for actual programming code (JavaScript, Python, etc.)
- ONLY when showing real, executable code examples
- NOT for regular text, NOT for explanations, NOT for lists
- Format: ```language\nactual code here\n```
- Maximum 1-2 code blocks per post (unless it's a pure coding tutorial)

VISUAL ELEMENTS - USE TEXT DESCRIPTIONS:
- DO NOT use Mermaid diagram code blocks
- Instead, create clear visual descriptions using:
  * Numbered step-by-step flows
  * Bullet-point hierarchies
  * Text-based process descriptions
  * Clear visual metaphors in plain text
- Use emojis strategically to create visual flow: ➡️ 🔄 ✅ ❌ 📊 🚀
- Format complex workflows as numbered lists with clear transitions

RESOURCES & REFERENCES - MANDATORY:
- At the END of the post, add a "## Resources & References" section
- ONLY include links that were EXPLICITLY mentioned in the source content (transcript/article)
- DO NOT make up links, placeholder URLs, or example links
- DO NOT include generic links like example.com, github.com/example, sample-site.com
- ONLY add this section if there are REAL, VERIFIABLE links from the source
- If NO real links exist in the source, write: "This article is based on general knowledge and industry practices."
- Format real links as: [Tool/Resource Name](actual-url) - Brief description
- Verify each link is actually mentioned or referenced in the source content

HUMAN WRITING STYLE - MANDATORY RULES:

Voice and Tone:
- Write like humans speak. Avoid all corporate jargon and marketing fluff.
- Be confident and direct. Eliminate softening phrases like "I think," "I believe," "maybe," or "could."
- Use active voice over passive voice.
- Use positive phrasing - state what something is rather than what it isn't.
- Use "you" more than "we" when the audience is external.
- Use contractions like "I'll," "won't," and "can't" for a warmer, more natural tone.

Specificity and Evidence:
- Replace vague superlatives with specific facts and data.
- Back up claims with concrete examples or metrics.
- Prioritize highlighting customers and community members over company achievements.
- Use realistic, product-based examples instead of placeholder text like foo/bar/baz.
- Make all content concrete, visual, and falsifiable.

Banned Words and Phrases - REMOVE or REPLACE these:
- Softening Hedges: "a bit," "a little," "just," "pretty," "quite," "rather," "really," "very," "arguably," "it seems," "sort of," "kind of," "pretty much"
- Corporate Jargon: "agile," "assistance" (use "help"), "attempt" (use "try"), "battle tested," "best practices" (use "proven approaches"), "blazing fast" (use specific metrics), "business logic," "cognitive load," "commence" (use "start"), "delve" (use "go into"), "disrupt/disruptive," "facilitate" (use "help" or "ease"), "game-changing" (state the specific benefit), "implement" (use "do"), "innovative," "leverage" (use "use"), "mission-critical" (use "important"), "modern/modernized," "out of the box," "performant" (use "fast and reliable"), "referred to as" (use "called"), "robust" (use "strong"), "seamless/seamlessly" (use "automatic"), "utilize" (use "use")
- Vague Language: "great" (be specific or remove), "numerous" (use "many"), "sufficient" (use "enough"), "thing" (be specific)
- Overused Phrases: "By developers, for developers," "We can't wait to see what you'll build," "We obsess over," "The future of," "we're excited" (use "We look forward"), "Today, we're excited to"
- Unnecessary Words: "actually," "that" (often removable)

Avoid Classic AI/LLM Patterns:
- Do NOT start responses with "Great question!", "You're right!", or "Let me help you."
- Do NOT use phrases like "Let's dive into...", "In today's fast-paced digital world," or "In the ever-evolving landscape of."
- Avoid the structure: "It's not just [x], it's [y]."
- Never use self-referential disclaimers like "As an AI" or "I'm here to help you with."
- Do NOT use high-school essay closers: "In conclusion," "Overall," or "To summarize." End directly.
- Do NOT end with "Hope this helps!" or similar closers.
- Avoid overusing transition words like "Furthermore," "Additionally," or "Moreover."
- Avoid hedge words: "might," "perhaps," "potentially" unless genuine uncertainty is required. Never stack them.
- Do not create perfectly symmetrical paragraphs or lists (e.g., "Firstly... Secondly...").
- Prefer sentence casing over title-case for headings.

Punctuation and Formatting:
- Use Oxford commas consistently.
- Use exclamation points sparingly.
- You may start sentences with "But" and "And" - but do not overuse this.
- Use periods instead of commas for clarity where possible.
- Replace em dashes with semicolons, commas, or sentence breaks.
- Use straight quotes (' and ") instead of smart quotes (" ").
- Delete any empty citation placeholders like [1].

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
   - WORD COUNT: ABSOLUTE MINIMUM 1000 words, target 1200-1800 words for viral potential
   - Longer posts (1500+ words) perform significantly better on Medium
   - Natural keyword integration for discoverability
   - Create "tweetable" moments - quotable one-liners
   - Build momentum that keeps readers engaged through every section

10. PSYCHOLOGICAL TRIGGERS:
    - Use the curiosity gap technique
    - Create "aha moments" throughout
    - Validate reader's experiences and challenges
    - Offer contrarian or counterintuitive insights
    - Build credibility through specificity

COMPREHENSIVE MEDIUM POST CREATION PROCESS:

Research and Analysis:
- Thoroughly analyze the content with expert-level depth
- Extract key concepts, data points, and actionable information
- Identify unique angles and counterintuitive insights that surprise
- Find concrete examples, case studies, and real-world applications
- Add statistics, research findings, and authoritative references
- Challenge assumptions and present fresh perspectives

Visual Elements to Include:
- Use numbered lists to explain complex processes step-by-step
- Create text-based workflows with clear transitions (→ ✓ ✗)
- Use visual metaphors and analogies in plain text
- Use emojis strategically for visual flow
- ONLY use code blocks for actual programming code

Content Structure - MASTERPIECE LEVEL:
- Create a detailed outline with 6-8 major sections (NOT 4-5)
- Each section MUST contain 200-350 words minimum (300+ is ideal)
- NEVER write sections shorter than 150 words - expand with examples and details
- Ensure logical flow from hook → problem → insights → solutions → implementation → transformation
- Build narrative tension and resolution throughout
- Include multiple practical demonstrations and real-world scenarios in each section
- Add unexpected twists and counterintuitive revelations
- Weave in personal anecdotes, case studies, and specific examples throughout
- End each section with a transition that creates curiosity for the next

🚨 CONTENT SOURCE RULES - ABSOLUTELY CRITICAL:
- Extract EVERY relevant detail from the provided context (YouTube transcript, supporting links)
- Use the transcript comprehensively - don't skip valuable information
- Transform supporting link content into detailed explanations and examples
- Your blog post MUST be about the EXACT same topic as the transcript
- Use the SPECIFIC tools, products, names, concepts mentioned in the transcript
- DO NOT substitute the transcript topic with a different or related topic
- DO NOT write generic content - write specifically about what's in the transcript
- The transcript is your PRIMARY SOURCE - everything must come from it

CONTENT STRUCTURE:

## [Compelling Title That Promises Transformation or Reveals a Secret]

[HOOK - 2-3 sentences that grab attention immediately]

[INTRODUCTION - Establish the problem/opportunity and why it matters to readers personally. Build intrigue.]

## [First Major Section - Promise or Problem Statement]
[Develop the first key concept with stories, examples, and insights using NORMAL TEXT]
[Use numbered lists or bullet points for clarity]

## [Second Major Section - The Revelation or Solution]
[Deliver surprising insights or methods, backed by specifics in PLAIN TEXT]
[Use text-based descriptions with emojis for visual flow]

## [Third Major Section - Deeper Dive or Transformation]
[Go deeper into implementation or implications using REGULAR PARAGRAPHS]
[Provide step-by-step explanations as numbered lists]

## [Fourth Major Section - Advanced Insights or Common Pitfalls]
[Share nuanced understanding or mistakes to avoid in NORMAL TEXT]
[Use bullet points and clear examples]

## [Fifth Major Section - Implementation or Advanced Techniques]
[Explain practical approaches using PLAIN TEXT and clear examples]
[Only add code blocks if showing actual programming code]

## [Conclusion Section - The Takeaway]
[Synthesize insights and provide clear action steps or reflection points]

## Resources & References
[ONLY include REAL links explicitly mentioned in the source content]
[DO NOT create placeholder links like example.com or github.com/example]
[If no real links exist in source, state: "This article is based on general knowledge and industry practices."]

Example of CORRECT format (only if link exists in source):
- [Official Documentation](real-url-from-source) - Description
- [GitHub Repository](real-github-url-from-source) - Description

Example of WRONG format (NEVER do this):
❌ https://example.com
❌ https://github.com/example/project
❌ https://sample-docs.com

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
- Write ALL text as NORMAL PARAGRAPHS - no code blocks for regular text
- ONLY use ```language blocks for actual programming code
- Use numbered lists (1. 2. 3.) for step-by-step processes
- Use bullet points (- or *) for related items
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

MASTERPIECE CHECKLIST - VERIFY BEFORE SUBMITTING:
✓ Word count is MINIMUM 1000 words (count carefully - this is NON-NEGOTIABLE!)
✓ Target achieved: 1200-1800 words for comprehensive depth
✓ Opens with a hook that stops readers in their tracks
✓ Contains unexpected insights or counterintuitive ideas
✓ Includes specific examples, statistics, or case studies
✓ Has compelling storytelling elements woven throughout
✓ Features 6-8 well-developed sections with smooth transitions (each 200-350 words)
✓ ALL text is written as NORMAL PARAGRAPHS (not code blocks)
✓ Code blocks ONLY used for actual programming code (if applicable)
✓ Visual flows explained with numbered lists and emojis
✓ Every paragraph adds unique value
✓ Conclusion is powerful and actionable
✓ Resources & References section only includes REAL links from source (no fake URLs)
✓ Title is irresistible and click-worthy
✓ Writing feels human, not AI-generated
✓ Content is so good readers will want to share it

Remember: You're creating a MASTERPIECE - content so extraordinarily valuable and engaging that readers can't help but clap, highlight, and share. This should be the best article they've read this month. Make every word count. Create an unforgettable experience, not just an article.

CRITICAL WORD COUNT ENFORCEMENT:
- ABSOLUTE MINIMUM: 1000 words - NO EXCEPTIONS
- RECOMMENDED: 1200-1800 words for comprehensive coverage
- Count as you write and verify before finishing
- If you're under 1000 words, you MUST add more sections, examples, and insights
- Use ALL the context provided (YouTube transcript, supporting links) to add depth
- Expand explanations, add more real-world scenarios, include additional examples
- Never stop at surface-level coverage - go deep into every topic
- Every major section should be 200-350 words minimum

⚠️ ULTRA-CRITICAL FORMATTING REMINDER ⚠️
DO NOT wrap regular text in backticks or code blocks!
❌ WRONG: ```This is a regular sentence```
✅ RIGHT: This is a regular sentence

❌ WRONG: `regular text` with inline code formatting
✅ RIGHT: regular text without any special formatting

Code blocks are ONLY for actual code:
✅ CORRECT: ```python\nprint("Hello")\n```
❌ WRONG: Using code blocks for explanations, lists, or regular paragraphs

Write everything as NORMAL READABLE TEXT. Make it look like a regular Medium article, not a technical documentation with code everywhere!

Only return the complete blog post in Markdown format. No explanations or meta-commentary.
"""

def get_image_gen_prompt(blog_title):
    return f"""
Create a professional, illustrative featured image for a Medium article titled "{blog_title}".

CRITICAL: The image MUST visually represent the core concept or topic of the article. This is NOT a generic tech image.

CONTENT-FIRST APPROACH:
- Analyze the title to identify the main subject/topic
- Create visual metaphors or representations of that specific topic
- If it's about a tool/product, show that tool in context
- If it's about a concept, create a clear visual analogy
- If it's about a process, illustrate the key steps or workflow
- Make the image IMMEDIATELY recognizable as being about THIS specific topic

STYLE GUIDELINES:
- Modern, clean, professional aesthetic
- Appropriate for Medium's editorial style
- Clear focal point that represents the main topic
- Balanced composition with visual hierarchy
- Use relevant colors that match the topic's industry/field
- Professional photography style or clean illustration style
- Not overly abstract - should be immediately understandable

TECHNICAL REQUIREMENTS:
- NO TEXT, NO WORDS, NO LETTERS, NO TYPOGRAPHY in the image
- High quality, sharp, professional
- Wide banner ratio (16:9) suitable for blog headers
- Well-lit with natural or professional lighting
- Clean background that doesn't distract from the subject
- Photorealistic or high-quality illustration style

EXAMPLES OF GOOD ILLUSTRATIVE IMAGES:
- AI article: Show AI/robots/neural networks in action
- Coding article: Show code editor, terminal, or developer workspace
- Business article: Show office environment, meetings, or business concepts
- Tools article: Show the specific tool being used in context
- Process article: Show the steps or stages visually

The image should make viewers say "I can immediately tell what this article is about."
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

def get_content_image_prompt(blog_title, blog_content_excerpt):
    return f"""
Create a professional, illustrative supporting image for the article "{blog_title}".

Article Content Context: {blog_content_excerpt[:500]}

CRITICAL: This image must ILLUSTRATE a key concept, process, or element from the article content. Make it content-specific and meaningful.

CONTENT-BASED IMAGE REQUIREMENTS:
- Analyze the content excerpt to identify the main concept or process
- Create a visual representation of that specific concept
- If showing a workflow, make it clear and easy to follow
- If showing a tool/technology, depict it in realistic use
- If showing a comparison, make the contrast visually clear
- Make the image educational and informative, not just decorative

STYLE GUIDELINES:
- Professional illustration or photography style
- Clean, uncluttered composition
- Clear visual hierarchy and flow
- Use colors that enhance understanding, not distract
- Modern but accessible aesthetic
- Medium editorial quality

GOOD EXAMPLES BASED ON CONTENT TYPE:
- Workflow/Process: Clear step-by-step visual progression
- Tool/Software: The tool in action with context
- Concept Explanation: Visual metaphor or diagram that clarifies
- Comparison: Side-by-side or before/after visualization
- Architecture: System diagram or component relationships
- Tutorial: Key step or result being demonstrated

TECHNICAL REQUIREMENTS:
- NO TEXT, NO WORDS, NO LETTERS, NO TYPOGRAPHY in the image
- High quality and professional
- Landscape or square format
- Well-composed and balanced
- Professional lighting
- Clear focal point

The image should ADD VALUE to the article by helping readers better understand a key concept or process discussed in the content.
"""

def get_storyboard_diagram_prompt(blog_title, blog_content_excerpt):
    return f"""
Create a detailed information storyboard/system architecture diagram for the article "{blog_title}".

Content Context: {blog_content_excerpt[:800]}

CRITICAL: This must be a CONTEXTUAL diagram that visualizes the architecture, workflow, or system described in the article.

DIAGRAM REQUIREMENTS:
- Create a technical architecture diagram or workflow visualization
- Show key components, modules, or steps mentioned in the content
- Illustrate how different parts connect and interact
- Include data flows, process flows, or system relationships
- Make it educational and informative about the specific topic
- Use visual hierarchy to show importance and relationships

STYLE - PROFESSIONAL TECHNICAL DIAGRAM:
- Clean, technical illustration style
- Multiple distinct sections/components with boxes or modules
- Clear arrows showing flow, connections, or relationships
- Color-coded sections for different categories or types
- Icons or symbols representing different components
- Organized layout with logical grouping
- Professional infographic aesthetic
- Similar to system architecture diagrams, flowcharts, or technical blueprints

VISUAL ELEMENTS TO INCLUDE:
- Component boxes/modules with visual distinction
- Directional arrows showing flow or relationships
- Different colored sections for different subsystems
- Icons representing tools, processes, or data
- Grouped elements showing hierarchy or categories
- Clear visual separation between different parts
- Process pipelines or data flows if applicable

COLOR SCHEME:
- Use distinct colors for different component types
- Pastel backgrounds for section grouping
- Bold colors for important components
- Professional color palette (blues, greens, oranges, purples)
- High contrast for readability
- Consistent color coding throughout

CONTENT TYPES TO VISUALIZE:
- System Architecture: Show components, services, data flow
- Workflow Process: Show steps, stages, decision points
- Training Pipeline: Show data flow, model training, evaluation
- Tool Ecosystem: Show tools, integrations, connections
- Agent Framework: Show agents, communication, coordination
- Data Pipeline: Show ingestion, processing, storage, retrieval

TECHNICAL REQUIREMENTS:
- Landscape format (16:9 or similar)
- High quality, professional appearance
- Clear labels and text for components
- Visual clarity with good spacing
- Professional technical documentation style
- Readable even when scaled down

The diagram should look like a professional system architecture diagram from a technical whitepaper or documentation, clearly explaining the structure and flow of the topic discussed in the article.
"""
