# Human-Like Writing Style Enforcement Guide

This document defines the mandatory writing rules to ensure all generated content sounds natural, confident, and human-written rather than AI-generated or filled with corporate jargon.

## Voice and Tone

- Write like humans speak. Avoid all corporate jargon and marketing fluff.
- Be confident and direct. Eliminate softening phrases like "I think," "I believe," "maybe," or "could."
- Use active voice over passive voice.
- Use positive phrasing - state what something **is** rather than what it **isn't**.
- Use "you" more than "we" when the audience is external.
- Use contractions like "I'll," "won't," and "can't" for a warmer, more natural tone.

## Specificity and Evidence

- Replace vague superlatives with specific facts and data.
- Back up claims with concrete examples or metrics.
- Prioritize highlighting customers and community members over company achievements.
- Use realistic, product-based examples instead of placeholder text like `foo/bar/baz`.
- Make all content concrete, visual, and falsifiable.

## Banned Words and Phrases

### Softening Hedges (REMOVE or REPLACE)

- a bit
- a little
- just
- pretty
- quite
- rather
- really
- very
- arguably
- it seems
- sort of / kind of
- pretty much

### Corporate Jargon (REMOVE or REPLACE)

| Banned Word | Replacement |
|-------------|-------------|
| agile | (be specific about what you mean) |
| assistance | help |
| attempt | try |
| battle tested | (use specific metrics) |
| best practices | proven approaches |
| blazing fast | (use specific speed metrics) |
| business logic | (be specific) |
| cognitive load | (describe the actual challenge) |
| commence | start |
| delve | go into |
| disrupt/disruptive | (state the specific benefit) |
| facilitate | help or ease |
| game-changing | (state the specific benefit) |
| implement | do |
| innovative | (show what's new specifically) |
| leverage | use |
| mission-critical | important |
| modern/modernized | (be specific about what makes it current) |
| out of the box | (describe the actual feature) |
| performant | fast and reliable |
| referred to as | called |
| robust | strong |
| seamless/seamlessly | automatic |
| utilize | use |

### Vague Language (REMOVE or REPLACE)

| Banned Word | Replacement |
|-------------|-------------|
| great | (be specific or remove) |
| numerous | many |
| sufficient | enough |
| thing | (be specific) |

### Overused Marketing Phrases (NEVER USE)

- By developers, for developers
- We can't wait to see what you'll build
- We obsess over
- The future of
- we're excited (use "We look forward")
- Today, we're excited to

### Unnecessary Words

- actually (usually removable)
- that (often removable)

## Avoid Classic AI/LLM Patterns

### Opening Phrases (NEVER USE)

- Great question!
- You're right!
- Let me help you
- I'm here to help you with
- As an AI

### Transition Clichés (AVOID)

- Let's dive into...
- In today's fast-paced digital world
- In the ever-evolving landscape of
- Furthermore
- Additionally
- Moreover (use sparingly)

### Structural Patterns (AVOID)

- "It's not just [x], it's [y]" structure
- Perfectly symmetrical lists (e.g., "Firstly... Secondly... Thirdly...")
- Starting every paragraph with transition words

### Closing Phrases (NEVER USE)

- In conclusion
- Overall
- To summarize
- Hope this helps!
- Thanks for reading!

### Hedge Word Stacking (NEVER DO)

- "This might perhaps potentially..." (never stack uncertainty words)
- Use "might," "perhaps," "potentially" only when genuine uncertainty is required

## Title Creation Rules

- Make a clear promise so readers know what they'll get
- Tap into relevant, controversial points backed by data (avoid clickbait)
- Share something uniquely helpful
- Avoid vague titles like "My Thoughts On XYZ"
- Titles must be opinions or shareable facts
- Prefer sentence casing over title-case for headings

## Punctuation and Formatting

- Use Oxford commas consistently
- Use exclamation points sparingly
- You may start sentences with "But" and "And" - but do not overuse this
- Use periods instead of commas for clarity where possible
- Replace em dashes (—) with semicolons, commas, or sentence breaks
- Use straight quotes (`'` and `"`) instead of smart quotes (`"` and `"`)
- Delete any empty citation placeholders like `[1]`

## Content Quality Standards

### Make Content Verifiable

- All claims should be concrete, visual, and falsifiable
- Back up statements with specific facts and data
- Use realistic, product-based examples (no placeholder examples)
- Prioritize actionable insights over theory
- Create content that's immediately implementable

### Examples of Good vs Bad Writing

#### ❌ BAD (AI-like, corporate jargon)

"In today's fast-paced digital landscape, we're excited to leverage our innovative, game-changing platform to facilitate seamless collaboration. Our robust, battle-tested solution utilizes best practices to implement a performant architecture that will delve into your business logic and modernize your workflows. It's not just a tool, it's a revolution."

#### ✅ GOOD (Human-like, specific)

"This platform cuts meeting prep time by 67%. Instead of spending 2 hours gathering context, you'll spend 15 minutes. Here's how it works: connect your calendar, and the system pulls relevant docs, past decisions, and team updates into one brief. You read it on your commute, and you're ready."

## Validation Checklist

Before publishing, verify:

- ✓ No corporate jargon from the banned list
- ✓ No AI opening/closing patterns
- ✓ No softening hedges or excessive qualifiers
- ✓ All claims backed by specific facts or metrics
- ✓ Examples are realistic and product-based (no foo/bar)
- ✓ Contractions used for natural tone
- ✓ Active voice used throughout
- ✓ Straight quotes used instead of smart quotes
- ✓ Oxford commas used consistently
- ✓ Content is concrete, visual, and falsifiable
- ✓ Writing sounds like confident human speech

## Implementation Notes

These rules are enforced in:

- `prompts.py` - Blog generation prompts (lines 116-159)
- `ai_editor.py` - All content editing and refinement functions
- All AI-generated content should pass through these filters

When writing or editing content, ask: "Would a confident human expert write it this way?" If the answer is no, revise.
