AVAILABLE_MODELS = {
    'gpt-4o': {
        'name': 'GPT-4o (Primary)',
        'description': 'OpenAI flagship model',
        'best_for': 'All use cases, highest quality',
        'max_tokens': 8192,
        'temperature': 0.9,
        'provider': 'openai'
    },
    'gpt-4o-mini': {
        'name': 'GPT-4o Mini',
        'description': 'Fast and efficient OpenAI model',
        'best_for': 'Quick generation, cost-effective',
        'max_tokens': 8192,
        'temperature': 0.9,
        'provider': 'openai'
    },
    'gemini-2.0-flash-exp': {
        'name': 'Gemini 2.0 Flash (Secondary)',
        'description': 'Latest model, fast and powerful',
        'best_for': 'Most use cases, balanced speed and quality',
        'max_tokens': 8192,
        'temperature': 0.9,
        'provider': 'gemini'
    },
    'gemini-1.5-pro': {
        'name': 'Gemini 1.5 Pro',
        'description': 'Highest quality output',
        'best_for': 'Complex topics, long videos, maximum quality',
        'max_tokens': 8192,
        'temperature': 0.9,
        'provider': 'gemini'
    },
    'gemini-1.5-flash': {
        'name': 'Gemini 1.5 Flash',
        'description': 'Fast generation',
        'best_for': 'Quick generation, shorter videos',
        'max_tokens': 8192,
        'temperature': 0.9,
        'provider': 'gemini'
    },
    'claude-4-sonnet-20250514': {
        'name': 'Claude 4 Sonnet (Extended Thinking)',
        'description': 'Anthropic flagship model with extended thinking',
        'best_for': 'Complex analysis, deep reasoning, high quality content',
        'max_tokens': 16000,
        'temperature': 1.0,
        'provider': 'anthropic',
        'thinking_budget': 10000
    },
    'claude-3-haiku-20240307': {
        'name': 'Claude 3 Haiku',
        'description': 'Fast Anthropic model',
        'best_for': 'Quick generation, backup option',
        'max_tokens': 8192,
        'temperature': 0.9,
        'provider': 'anthropic'
    }
}

IMAGEN_MODELS = {
    'imagen-3.0-generate-001': {
        'name': 'Imagen 3.0',
        'description': 'Latest image generation model',
        'default': True
    },
    'imagen-4.0-generate-001': {
        'name': 'Imagen 4.0',
        'description': 'Newest image generation (if available)',
        'default': False
    }
}

ENGAGEMENT_THRESHOLDS = {
    'excellent': 85,
    'good': 70,
    'fair': 55,
    'needs_improvement': 0
}

OPTIMAL_WORD_COUNT = {
    'min': 800,
    'ideal_min': 1000,
    'ideal_max': 1500,
    'max': 3000
}

READING_SPEED_WPM = 200

DEFAULT_LOCATION = 'us-central1'
DEFAULT_PORT = 8080

VIRAL_POST_CHARACTERISTICS = {
    'min_paragraphs': 8,
    'ideal_paragraph_length': 50,
    'min_subheadings': 4,
    'max_subheadings': 7,
    'bold_usage_target': 10,
    'question_count_target': 5,
    'quote_count_target': 3
}
