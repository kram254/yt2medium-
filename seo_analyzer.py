import re
from collections import Counter
import math

def calculate_readability_score(text):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = text.split()
    
    if not sentences or not words:
        return 0
    
    total_sentences = len(sentences)
    total_words = len(words)
    syllables = sum(count_syllables(word) for word in words)
    
    if total_sentences == 0 or total_words == 0:
        return 0
    
    flesch_reading_ease = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (syllables / total_words)
    return max(0, min(100, flesch_reading_ease))

def count_syllables(word):
    word = word.lower()
    vowels = 'aeiouy'
    syllable_count = 0
    previous_was_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            syllable_count += 1
        previous_was_vowel = is_vowel
    
    if word.endswith('e'):
        syllable_count -= 1
    if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
        syllable_count += 1
    if syllable_count == 0:
        syllable_count = 1
        
    return syllable_count

def extract_keywords(text, top_n=10):
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    
    stop_words = {
        'this', 'that', 'with', 'from', 'have', 'will', 'your', 'their',
        'which', 'about', 'would', 'there', 'these', 'those', 'when',
        'where', 'what', 'make', 'been', 'more', 'than', 'some', 'could',
        'into', 'time', 'very', 'only', 'just', 'know', 'take', 'people',
        'them', 'then', 'well', 'also', 'back', 'after', 'most', 'even'
    }
    
    filtered_words = [w for w in words if w not in stop_words]
    word_freq = Counter(filtered_words)
    
    return word_freq.most_common(top_n)

def calculate_keyword_density(text):
    words = text.split()
    total_words = len(words)
    
    if total_words == 0:
        return {}
    
    keywords = extract_keywords(text, 5)
    density = {}
    
    for word, count in keywords:
        density[word] = round((count / total_words) * 100, 2)
    
    return density

def analyze_seo(text, title):
    analysis = {
        'readability_score': calculate_readability_score(text),
        'keywords': extract_keywords(text, 10),
        'keyword_density': calculate_keyword_density(text),
        'word_count': len(text.split()),
        'title_length': len(title),
        'title_optimal': 60 <= len(title) <= 80,
        'has_questions': '?' in text,
        'has_lists': bool(re.search(r'^\d+\.|^[-*]', text, re.MULTILINE)),
        'paragraph_count': len(text.split('\n\n')),
        'heading_count': len(re.findall(r'^#{2,3}\s', text, re.MULTILINE)),
        'external_links': len(re.findall(r'https?://', text)),
    }
    
    analysis['seo_score'] = calculate_seo_score(analysis)
    analysis['viral_potential'] = calculate_viral_potential(text, title, analysis)
    
    return analysis

def calculate_seo_score(analysis):
    score = 0
    
    if 60 <= analysis['readability_score'] <= 80:
        score += 20
    elif analysis['readability_score'] > 50:
        score += 15
    
    if analysis['title_optimal']:
        score += 15
    
    if 800 <= analysis['word_count'] <= 2000:
        score += 20
    elif 600 <= analysis['word_count'] <= 2500:
        score += 15
    
    if analysis['heading_count'] >= 4:
        score += 15
    
    if analysis['has_lists']:
        score += 10
    
    if analysis['external_links'] >= 2:
        score += 10
    
    if analysis['keyword_density']:
        densities = list(analysis['keyword_density'].values())
        if any(1 <= d <= 3 for d in densities):
            score += 10
    
    return min(100, score)

def calculate_viral_potential(text, title, analysis):
    score = 0
    
    power_words = [
        'secret', 'truth', 'reality', 'hidden', 'mistake', 'shocking',
        'ultimate', 'essential', 'critical', 'proven', 'revolutionary',
        'game-changing', 'breakthrough', 'transform', 'master', 'unlock'
    ]
    
    title_lower = title.lower()
    for word in power_words:
        if word in title_lower:
            score += 10
            break
    
    if any(title.startswith(p) for p in ['How to', 'Why', 'What', 'The']):
        score += 15
    
    if analysis['readability_score'] > 60:
        score += 15
    
    if analysis['has_questions']:
        score += 10
    
    if 1000 <= analysis['word_count'] <= 1500:
        score += 20
    elif 800 <= analysis['word_count'] <= 2000:
        score += 15
    
    if analysis['heading_count'] >= 5:
        score += 15
    
    if analysis['has_lists']:
        score += 15
    
    return min(100, score)

def generate_seo_recommendations(analysis):
    recommendations = []
    
    if not analysis['title_optimal']:
        recommendations.append('Title should be 60-80 characters for optimal SEO')
    
    if analysis['readability_score'] < 60:
        recommendations.append('Improve readability - use shorter sentences and simpler words')
    
    if analysis['word_count'] < 800:
        recommendations.append('Add more content - aim for 1000-1500 words')
    
    if analysis['heading_count'] < 4:
        recommendations.append('Add more subheadings (H2/H3) to improve structure')
    
    if not analysis['has_lists']:
        recommendations.append('Include bulleted or numbered lists for better scannability')
    
    if analysis['external_links'] < 2:
        recommendations.append('Add 2-3 external links to authoritative sources')
    
    if analysis['keyword_density']:
        high_density = [k for k, v in analysis['keyword_density'].items() if v > 3]
        if high_density:
            recommendations.append(f'Keyword "{high_density[0]}" is overused - reduce density')
    
    return recommendations
