import re
from collections import Counter
from textstat import textstat

def analyze_readability(text):
    return {
        'flesch_reading_ease': round(textstat.flesch_reading_ease(text), 1),
        'flesch_kincaid_grade': round(textstat.flesch_kincaid_grade(text), 1),
        'gunning_fog': round(textstat.gunning_fog(text), 1),
        'smog_index': round(textstat.smog_index(text), 1),
        'automated_readability_index': round(textstat.automated_readability_index(text), 1),
        'coleman_liau_index': round(textstat.coleman_liau_index(text), 1),
        'reading_time_seconds': round(textstat.reading_time(text, ms_per_char=14.69)),
        'grade_level': textstat.text_standard(text, float_output=False)
    }

def analyze_keywords(text, top_n=20):
    text_clean = re.sub(r'[^\w\s]', '', text.lower())
    words = text_clean.split()
    
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                  'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
                  'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
    
    filtered_words = [w for w in words if len(w) > 3 and w not in stop_words]
    
    keyword_counts = Counter(filtered_words)
    
    return [{'keyword': word, 'count': count, 'density': round((count / len(filtered_words)) * 100, 2)}
            for word, count in keyword_counts.most_common(top_n)]

def analyze_sentence_structure(text):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    sentence_lengths = [len(s.split()) for s in sentences]
    
    return {
        'total_sentences': len(sentences),
        'avg_sentence_length': round(sum(sentence_lengths) / len(sentence_lengths), 1) if sentence_lengths else 0,
        'max_sentence_length': max(sentence_lengths) if sentence_lengths else 0,
        'min_sentence_length': min(sentence_lengths) if sentence_lengths else 0,
        'short_sentences': len([s for s in sentence_lengths if s < 15]),
        'medium_sentences': len([s for s in sentence_lengths if 15 <= s <= 25]),
        'long_sentences': len([s for s in sentence_lengths if s > 25])
    }

def analyze_tone_sentiment(text):
    positive_words = {'great', 'amazing', 'excellent', 'fantastic', 'wonderful', 'brilliant',
                     'outstanding', 'superb', 'incredible', 'remarkable', 'perfect', 'best',
                     'love', 'enjoy', 'happy', 'excited', 'thrilled', 'delighted', 'powerful'}
    
    negative_words = {'bad', 'terrible', 'awful', 'horrible', 'poor', 'worst', 'fail',
                     'failed', 'problem', 'issue', 'difficult', 'hard', 'struggle', 'hate',
                     'disappointing', 'frustrating', 'annoying', 'ugly', 'wrong'}
    
    professional_words = {'implement', 'develop', 'analyze', 'optimize', 'enhance', 'integrate',
                         'configure', 'deploy', 'architecture', 'framework', 'methodology',
                         'strategy', 'solution', 'approach', 'process', 'system'}
    
    casual_words = {'hey', 'yeah', 'cool', 'awesome', 'totally', 'basically', 'literally',
                   'actually', 'really', 'pretty', 'quite', 'super', 'kinda', 'gonna',
                   'wanna', 'stuff', 'things', 'guys', 'folks'}
    
    words = re.findall(r'\b\w+\b', text.lower())
    
    pos_count = sum(1 for w in words if w in positive_words)
    neg_count = sum(1 for w in words if w in negative_words)
    prof_count = sum(1 for w in words if w in professional_words)
    cas_count = sum(1 for w in words if w in casual_words)
    
    total_words = len(words)
    
    sentiment_score = ((pos_count - neg_count) / total_words * 100) if total_words > 0 else 0
    
    if prof_count > cas_count * 1.5:
        tone = 'professional'
    elif cas_count > prof_count * 1.5:
        tone = 'casual'
    else:
        tone = 'balanced'
    
    return {
        'sentiment_score': round(sentiment_score, 2),
        'positive_word_count': pos_count,
        'negative_word_count': neg_count,
        'tone': tone,
        'tone_confidence': round(max(prof_count, cas_count) / total_words * 100, 1) if total_words > 0 else 0
    }

def analyze_engagement_potential(text, title):
    engagement_score = 50
    
    title_length = len(title.split())
    if 6 <= title_length <= 12:
        engagement_score += 10
    
    power_words = ['secret', 'proven', 'ultimate', 'complete', 'essential', 'critical',
                   'hidden', 'truth', 'reality', 'mistake', 'warning', 'breakthrough']
    if any(word in title.lower() for word in power_words):
        engagement_score += 15
    
    if '?' in title or '!' in title or ':' in title:
        engagement_score += 5
    
    word_count = len(text.split())
    if 800 <= word_count <= 2000:
        engagement_score += 10
    elif word_count > 2000:
        engagement_score += 5
    
    paragraphs = text.split('\n\n')
    short_paragraphs = len([p for p in paragraphs if len(p.split()) < 50])
    if short_paragraphs / len(paragraphs) > 0.6:
        engagement_score += 10
    
    headings = len(re.findall(r'^#{1,3}\s', text, re.MULTILINE))
    if headings >= 5:
        engagement_score += 10
    
    lists = len(re.findall(r'^\*\s|^\d+\.\s', text, re.MULTILINE))
    if lists > 0:
        engagement_score += 5
    
    questions = len(re.findall(r'\?', text))
    if questions >= 3:
        engagement_score += 5
    
    return min(100, max(0, engagement_score))

def calculate_viral_potential(text, title, seo_score):
    viral_score = 40
    
    emotional_triggers = ['shocking', 'unbelievable', 'insane', 'crazy', 'mindblowing',
                         'incredible', 'amazing', 'surprising', 'unexpected', 'revealed']
    if any(trigger in title.lower() for trigger in emotional_triggers):
        viral_score += 15
    
    numbers = len(re.findall(r'\d+', title))
    if numbers > 0:
        viral_score += 10
    
    negative_words = ['never', 'stop', 'avoid', 'mistake', 'wrong', 'fail', 'worst']
    if any(word in title.lower() for word in negative_words):
        viral_score += 10
    
    if seo_score >= 80:
        viral_score += 15
    elif seo_score >= 60:
        viral_score += 10
    
    word_count = len(text.split())
    if 1200 <= word_count <= 1800:
        viral_score += 10
    
    return min(100, max(0, viral_score))

def generate_content_insights(text, title):
    word_count = len(text.split())
    
    readability = analyze_readability(text)
    keywords = analyze_keywords(text)
    sentence_structure = analyze_sentence_structure(text)
    tone_sentiment = analyze_tone_sentiment(text)
    
    insights = []
    
    if readability['flesch_reading_ease'] < 60:
        insights.append({
            'type': 'warning',
            'message': 'Content may be too complex. Consider simplifying sentences.'
        })
    
    if sentence_structure['avg_sentence_length'] > 20:
        insights.append({
            'type': 'warning',
            'message': f"Average sentence length is {sentence_structure['avg_sentence_length']} words. Aim for 15-20 for better readability."
        })
    
    if word_count < 800:
        insights.append({
            'type': 'warning',
            'message': f'Content is only {word_count} words. Aim for 800-1500 words for better engagement.'
        })
    
    if tone_sentiment['sentiment_score'] < -5:
        insights.append({
            'type': 'info',
            'message': 'Content has a negative tone. Consider balancing with positive examples.'
        })
    
    if len(title.split()) > 15:
        insights.append({
            'type': 'warning',
            'message': 'Title is too long. Keep it under 12 words for better click-through rates.'
        })
    
    headings_count = len(re.findall(r'^#{1,3}\s', text, re.MULTILINE))
    if headings_count < 3:
        insights.append({
            'type': 'warning',
            'message': 'Add more subheadings to break up content and improve scannability.'
        })
    
    return insights

def generate_improvement_suggestions(text, title, seo_score, engagement_score):
    suggestions = []
    
    if engagement_score < 70:
        suggestions.append({
            'category': 'engagement',
            'priority': 'high',
            'suggestion': 'Add more questions to engage readers directly'
        })
        suggestions.append({
            'category': 'engagement',
            'priority': 'high',
            'suggestion': 'Include personal anecdotes or real-world examples'
        })
    
    if seo_score < 70:
        suggestions.append({
            'category': 'seo',
            'priority': 'high',
            'suggestion': 'Optimize title with target keywords'
        })
        suggestions.append({
            'category': 'seo',
            'priority': 'medium',
            'suggestion': 'Add more internal and external links'
        })
    
    readability = analyze_readability(text)
    if readability['flesch_reading_ease'] < 60:
        suggestions.append({
            'category': 'readability',
            'priority': 'high',
            'suggestion': 'Break long sentences into shorter ones'
        })
    
    word_count = len(text.split())
    if word_count < 1000:
        suggestions.append({
            'category': 'content',
            'priority': 'medium',
            'suggestion': f'Expand content to reach 1000-1500 words (currently {word_count})'
        })
    
    if '?' not in text[:500]:
        suggestions.append({
            'category': 'engagement',
            'priority': 'medium',
            'suggestion': 'Start with a compelling question in the introduction'
        })
    
    return suggestions
