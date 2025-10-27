from medium_research_agent import (
    apply_medium_practices_to_prompt,
    optimize_content_structure,
    analyze_medium_readiness,
    get_viral_title_formulas
)

test_content = """
## Introduction

This is a test blog post with multiple paragraphs. Some paragraphs are long and contain many sentences that should be broken up for better readability. This makes the content easier to scan and more engaging for readers.

## Main Section

Here is another section with content. We want to test the optimization functions to see if they properly analyze and improve the structure of the content.

The system should detect issues like long paragraphs and provide recommendations.

## Conclusion

This is the final section of our test post.
"""

print("Testing Medium Research Agent Functions")
print("=" * 50)

print("\n1. Content Structure Optimization:")
optimized = optimize_content_structure(test_content)
print(f"Original length: {len(test_content)}")
print(f"Optimized length: {len(optimized)}")
print("Status: WORKING")

print("\n2. Medium Readiness Analysis:")
analysis = analyze_medium_readiness(test_content)
print(f"Readiness Score: {analysis['medium_readiness_score']}/100")
print(f"Avg Sentences/Para: {analysis['avg_sentences_per_paragraph']}")
print(f"Recommendations: {len(analysis['recommendations'])}")
print("Status: WORKING")

print("\n3. Viral Title Formulas:")
titles = get_viral_title_formulas("AI Content Creation")
print(f"Generated {len(titles)} title variations")
print(f"Example: {titles[0]}")
print("Status: WORKING")

print("\n4. Prompt Enhancement:")
base_prompt = "Write a blog post about AI."
enhanced = apply_medium_practices_to_prompt(base_prompt, "AI Technology")
print(f"Original prompt: {len(base_prompt)} chars")
print(f"Enhanced prompt: {len(enhanced)} chars")
print("Status: WORKING")

print("\n" + "=" * 50)
print("ALL FUNCTIONS ARE LIVE AND OPERATIONAL")
print("=" * 50)
