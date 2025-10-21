# API Reference

Complete API documentation for YouTube to Medium.

---

## Web Application Endpoints

### `GET /`
Landing page with video URL input form.

**Response:** HTML page

---

### `POST /blog`
Generate blog post from YouTube URL (form submission).

**Request:**
```http
POST /blog
Content-Type: application/x-www-form-urlencoded

youtube_link=https://www.youtube.com/watch?v=example
model=gemini-2.0-flash-exp
enhance=on
```

**Parameters:**
- `youtube_link` (required): YouTube video URL
- `model` (required): AI model to use
- `enhance` (optional): Enable enhancement mode

**Response:** HTML page with generated blog post

---

### `POST /generate`
Generate blog post (JSON API).

**Request:**
```json
{
  "youtube_link": "https://www.youtube.com/watch?v=example",
  "model": "gemini-2.0-flash-exp",
  "enhance": false
}
```

**Response:**
```json
{
  "success": true,
  "title": "Blog Post Title",
  "blog_post_html": "<h2>Title</h2><p>Content...</p>",
  "blog_post_markdown": "## Title\n\nContent...",
  "image_data": "base64_encoded_image_data",
  "reading_time": "8 min read",
  "key_quotes": ["Quote 1", "Quote 2"],
  "engagement_score": 85,
  "word_count": 1850
}
```

**Error Response:**
```json
{
  "error": "Error message description"
}
```

---

### `POST /export`
Export blog post content.

**Request:**
```json
{
  "markdown": "## Title\n\nContent..."
}
```

**Response:**
```json
{
  "success": true,
  "content": "## Title\n\nContent..."
}
```

---

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

---

## Python API

### Core Functions

#### `generate_blog_post_text(youtube_link, model)`
Generate blog post text from YouTube video.

**Parameters:**
- `youtube_link` (str): YouTube video URL
- `model` (str): Gemini model name

**Returns:**
- `str`: Generated blog post in Markdown format

**Raises:**
- `Exception`: If generation fails

**Example:**
```python
from app import generate_blog_post_text

blog_text = generate_blog_post_text(
    "https://www.youtube.com/watch?v=example",
    "gemini-2.0-flash-exp"
)
print(blog_text)
```

---

#### `generate_image(blog_title)`
Generate header image for blog post.

**Parameters:**
- `blog_title` (str): Blog post title

**Returns:**
- `str`: Base64 encoded PNG image, or `None` if fails

**Example:**
```python
from app import generate_image

image_data = generate_image("Understanding Machine Learning")
if image_data:
    with open("header.png", "wb") as f:
        f.write(base64.b64decode(image_data))
```

---

#### `enhance_blog_post(blog_text)`
Apply enhancement pass to improve engagement.

**Parameters:**
- `blog_text` (str): Original blog post text

**Returns:**
- `str`: Enhanced blog post text

**Example:**
```python
from app import enhance_blog_post

enhanced = enhance_blog_post(original_text)
```

---

### Utility Functions

#### `validate_youtube_url(url)`
Validate if URL is a valid YouTube link.

**Parameters:**
- `url` (str): URL to validate

**Returns:**
- `bool`: True if valid, False otherwise

**Example:**
```python
from util import validate_youtube_url

if validate_youtube_url("https://www.youtube.com/watch?v=abc"):
    print("Valid!")
```

---

#### `extract_title_from_markdown(markdown_text)`
Extract title from Markdown content.

**Parameters:**
- `markdown_text` (str): Markdown content

**Returns:**
- `str`: Extracted title or default title

**Example:**
```python
from util import extract_title_from_markdown

title = extract_title_from_markdown("## My Great Title\n\nContent...")
# Returns: "My Great Title"
```

---

#### `estimate_reading_time(text)`
Calculate estimated reading time.

**Parameters:**
- `text` (str): Text content

**Returns:**
- `str`: Reading time (e.g., "8 min read")

**Example:**
```python
from util import estimate_reading_time

time = estimate_reading_time("Your blog post content...")
# Returns: "8 min read"
```

---

#### `calculate_engagement_score(text)`
Calculate engagement score (0-100).

**Parameters:**
- `text` (str): Blog post text

**Returns:**
- `int`: Engagement score

**Example:**
```python
from util import calculate_engagement_score

score = calculate_engagement_score(blog_text)
print(f"Engagement Score: {score}/100")
```

---

#### `extract_key_quotes(markdown_text)`
Extract blockquotes from Markdown.

**Parameters:**
- `markdown_text` (str): Markdown content

**Returns:**
- `list`: List of quotes (up to 3)

**Example:**
```python
from util import extract_key_quotes

quotes = extract_key_quotes(blog_text)
for quote in quotes:
    print(f"- {quote}")
```

---

#### `clean_markdown(text)`
Clean and format Markdown text.

**Parameters:**
- `text` (str): Raw Markdown text

**Returns:**
- `str`: Cleaned Markdown

**Example:**
```python
from util import clean_markdown

cleaned = clean_markdown(raw_markdown)
```

---

### Prompt Functions

#### `get_blog_gen_prompt()`
Get the main blog generation prompt.

**Returns:**
- `str`: Prompt text for viral blog post generation

---

#### `get_image_gen_prompt(blog_title)`
Get image generation prompt.

**Parameters:**
- `blog_title` (str): Blog post title

**Returns:**
- `str`: Prompt for image generation

---

## CLI Interface

### Basic Usage
```bash
python cli.py "YOUTUBE_URL"
```

### Options

#### `-m, --model`
Select AI model.

**Choices:**
- `gemini-2.0-flash-exp` (default)
- `gemini-1.5-pro`
- `gemini-1.5-flash`

**Example:**
```bash
python cli.py "URL" --model gemini-1.5-pro
```

---

#### `-e, --enhance`
Enable enhancement mode.

**Example:**
```bash
python cli.py "URL" --enhance
```

---

#### `-o, --output`
Save to file instead of stdout.

**Example:**
```bash
python cli.py "URL" -o output.md
```

---

#### `-s, --stats-only`
Show only statistics.

**Example:**
```bash
python cli.py "URL" --stats-only
```

---

#### `--no-stats`
Skip statistics display.

**Example:**
```bash
python cli.py "URL" --no-stats
```

---

### Full Example
```bash
python cli.py "https://www.youtube.com/watch?v=example" \
  --model gemini-1.5-pro \
  --enhance \
  --output my_post.md
```

---

## Batch Processing

### Usage
```bash
python batch_process.py <input_file> [output_dir] [model]
```

### Input File Formats

#### Text File (.txt)
One URL per line:
```
https://www.youtube.com/watch?v=video1
https://www.youtube.com/watch?v=video2
https://www.youtube.com/watch?v=video3
```

#### CSV File (.csv)
Must have 'url' column:
```csv
url,title
https://www.youtube.com/watch?v=video1,Video 1
https://www.youtube.com/watch?v=video2,Video 2
```

#### JSON File (.json)
Array of URLs:
```json
[
  "https://www.youtube.com/watch?v=video1",
  "https://www.youtube.com/watch?v=video2"
]
```

Or object with urls key:
```json
{
  "urls": [
    "https://www.youtube.com/watch?v=video1",
    "https://www.youtube.com/watch?v=video2"
  ]
}
```

### Output

Creates files in output directory:
```
output/
├── 20251008_143000_001_Blog_Title_1.md
├── 20251008_143100_002_Blog_Title_2.md
└── batch_report_20251008_143000.json
```

Batch report format:
```json
[
  {
    "url": "https://www.youtube.com/watch?v=video1",
    "status": "success",
    "filename": "20251008_143000_001_Blog_Title_1.md",
    "title": "Blog Title 1",
    "word_count": 1850,
    "engagement_score": 85
  },
  {
    "url": "https://www.youtube.com/watch?v=video2",
    "status": "failed",
    "error": "Invalid URL"
  }
]
```

---

## Configuration

### Environment Variables

```env
PROJECT_ID=your-gcp-project-id
LOCATION=us-central1
PORT=8080
FLASK_ENV=development
```

### config.py Constants

#### `AVAILABLE_MODELS`
Dictionary of available AI models with metadata.

#### `IMAGEN_MODELS`
Dictionary of image generation models.

#### `ENGAGEMENT_THRESHOLDS`
Engagement score thresholds:
```python
{
    'excellent': 85,
    'good': 70,
    'fair': 55,
    'needs_improvement': 0
}
```

#### `OPTIMAL_WORD_COUNT`
Target word counts:
```python
{
    'min': 1400,
    'ideal_min': 1600,
    'ideal_max': 2400,
    'max': 3000
}
```

#### `VIRAL_POST_CHARACTERISTICS`
Characteristics of viral posts:
```python
{
    'min_paragraphs': 8,
    'ideal_paragraph_length': 50,
    'min_subheadings': 4,
    'max_subheadings': 7,
    'bold_usage_target': 10,
    'question_count_target': 5,
    'quote_count_target': 3
}
```

---

## Error Codes

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid input)
- `500` - Internal Server Error

### Error Messages

#### `"YouTube link is required"`
No URL provided in request.

#### `"Invalid YouTube URL"`
URL format is not recognized as valid YouTube link.

#### `"Failed to generate blog post: [details]"`
Error during blog post generation.

#### `"Could not determine the project ID"`
PROJECT_ID not set or Google Cloud auth failed.

---

## Rate Limits & Quotas

### Gemini API
- **Default**: 60 requests per minute
- **Tokens**: Varies by model
- **Context**: Up to 1M tokens (Gemini 1.5)

### Imagen API
- **Default**: 600 images per minute
- **Size**: Various sizes supported

**Note:** Quotas can be increased via GCP Console.

---

## Best Practices

### API Usage

1. **Error Handling**: Always wrap API calls in try-except
2. **Retry Logic**: Implement exponential backoff
3. **Validation**: Validate inputs before API calls
4. **Caching**: Consider caching results for same URLs

### Performance

1. **Batch Processing**: Use for multiple videos
2. **Async**: Consider async processing for web apps
3. **Timeouts**: Set appropriate timeouts (300s recommended)
4. **Resources**: Allocate 2GB+ memory for Cloud Run

### Security

1. **Environment Variables**: Never hardcode credentials
2. **Input Validation**: Sanitize all user inputs
3. **Rate Limiting**: Implement rate limiting for public APIs
4. **CORS**: Configure CORS if needed for web apps

---

## Examples

### Complete Python Example
```python
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from util import (
    get_project_id,
    validate_youtube_url,
    calculate_engagement_score
)
import prompts

load_dotenv()

def generate_post(youtube_url):
    if not validate_youtube_url(youtube_url):
        raise ValueError("Invalid YouTube URL")
    
    client = genai.Client(
        vertexai=True,
        project=get_project_id(),
        location='us-central1'
    )
    
    contents = [
        types.Part.from_uri(file_uri=youtube_url, mime_type="video/*"),
        types.Part.from_text(text=prompts.get_blog_gen_prompt())
    ]
    
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents=contents,
        config=types.GenerateContentConfig(
            temperature=0.9,
            max_output_tokens=8192
        )
    )
    
    blog_text = response.text
    score = calculate_engagement_score(blog_text)
    
    return {
        'content': blog_text,
        'engagement_score': score
    }

if __name__ == '__main__':
    result = generate_post("https://www.youtube.com/watch?v=example")
    print(f"Score: {result['engagement_score']}/100")
    print(result['content'])
```

### JavaScript Fetch Example
```javascript
async function generateBlogPost(youtubeUrl) {
    const response = await fetch('/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            youtube_link: youtubeUrl,
            model: 'gemini-2.0-flash-exp',
            enhance: false
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error);
    }
    
    return await response.json();
}

// Usage
generateBlogPost('https://www.youtube.com/watch?v=example')
    .then(result => {
        console.log('Title:', result.title);
        console.log('Score:', result.engagement_score);
        console.log('Content:', result.blog_post_markdown);
    })
    .catch(error => {
        console.error('Error:', error);
    });
```

---

## Version History

- **1.0.0** - Initial release with core functionality

---

## Support

For issues or questions:
- GitHub Issues: Report bugs
- Discussions: Ask questions
- Documentation: See README.md

---

*Last Updated: 2025-10-08*
