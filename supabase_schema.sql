CREATE TABLE IF NOT EXISTS blog_posts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    markdown_content TEXT NOT NULL,
    html_content TEXT NOT NULL,
    image_header TEXT,
    image_content TEXT,
    reading_time INTEGER,
    word_count INTEGER,
    engagement_score INTEGER,
    seo_score INTEGER,
    viral_potential INTEGER,
    readability_score INTEGER,
    key_quotes JSONB DEFAULT '[]'::jsonb,
    seo_recommendations JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS generation_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_input TEXT NOT NULL,
    input_type TEXT,
    model_used TEXT,
    template TEXT,
    tone TEXT,
    enhanced BOOLEAN DEFAULT FALSE,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    generation_time NUMERIC,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_blog_posts_created_at ON blog_posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_blog_posts_title ON blog_posts USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_generation_logs_created_at ON generation_logs(created_at DESC);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_blog_posts_updated_at BEFORE UPDATE ON blog_posts
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
