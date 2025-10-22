# 🎥 AI Content to Medium - Universal Blog Post Generator

Transform **any content** - YouTube videos, web articles, or topic prompts - into viral-worthy Medium blog posts with perfect formatting and AI-powered engagement optimization. Built with OpenAI GPT-4o, Google Gemini, and Anthropic Claude with intelligent fallback support for maximum reliability.

## 🆕 What's New

- ✅ **Universal Input Support** - YouTube, any URL, or direct topics/prompts
- ✅ **Smart Research** - Automatic research for trending topics
- ✅ **Dual Image Generation** - 2 AI images per post (Qwen/DALL-E/Imagen)
- ✅ **Mermaid Diagrams** - Automatic workflow visualizations for technical content
- ✅ **HTML Copy** - One-click copy of formatted content
- ✅ **Flexible Word Count** - 800-2400 words (optimized for Medium)
- ✅ **Web Scraping** - Extract and transform any web article

## ✨ Features

### 🎯 Viral Content Optimization
- **Engagement-Driven Prompts**: Uses proven Medium strategies to create posts designed for 1000+ claps
- **Hook-First Writing**: Compelling openings that grab readers immediately
- **Storytelling Focus**: Emotional connection and narrative flow built-in
- **Curiosity Gaps**: Strategic content structure that keeps readers scrolling

### 📝 Perfect Medium Formatting
- **Auto-Structured Content**: Optimal heading hierarchy and section flow
- **Reading Time Optimization**: Targets the sweet spot of 7-12 minute reads (1400-2400 words)
- **Mobile-Optimized**: Short paragraphs and strategic white space
- **Bold & Italics**: Key concepts emphasized naturally throughout

### 🖼️ AI-Generated Header Images
- **Professional Design**: Stunning, abstract header images using Imagen 3.0
- **Context-Aware**: Images tailored to your blog post title and theme
- **High Quality**: Publication-ready visuals

### 📊 Engagement Analytics
- **Engagement Score**: AI-powered scoring system (0-100) predicts viral potential
- **Reading Time**: Automatic calculation of estimated read time
- **Key Quotes**: Extracts the most impactful statements
- **Word Count**: Tracking to hit optimal length

### 🚀 Advanced Features
- **Multiple AI Models**: Choose from OpenAI GPT-4o, Google Gemini, or Anthropic Claude
- **Intelligent Fallback**: Automatic failover from OpenAI → Gemini → Anthropic for maximum reliability
- **Enhancement Mode**: Optional second pass for even more engaging content
- **Export Ready**: Clean Markdown output for direct Medium publishing
- **One-Click Copy**: Instant clipboard copy for easy publishing

## 🎬 How It Works

1. **Enter Any Content**: YouTube URL, article link, or topic prompt
2. **AI Processes**: Automatic detection, research, or web scraping
3. **Generate**: Creates blog post with 2 AI images and Mermaid diagrams
4. **Review**: Get engagement score, reading time, and key takeaways
5. **Copy & Publish**: One-click HTML copy ready for Medium

### 📥 Input Types Supported

**YouTube Videos**
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://youtu.be/dQw4w9WgXcQ
```

**Web Articles**
```
https://techcrunch.com/article-link
https://medium.com/@author/post
https://blog.example.com/post-title
```

**Trending Topics** (with automatic research)
```
trending AI developments today
latest advances in quantum computing
current state of blockchain
```

**Direct Prompts**
```
create an engaging post about machine learning
write about the future of renewable energy
explain how neural networks work
```

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **AI Models**: OpenAI GPT-4o, Google Gemini 2.0, Anthropic Claude 3.5 Sonnet
- **Image Generation**: Qwen (Hugging Face), DALL-E 3, Imagen 3.0
- **Web Scraping**: BeautifulSoup4
- **Diagram Rendering**: Mermaid.js
- **AI Providers**: OpenAI API, Google Vertex AI, Anthropic API, Hugging Face
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Docker, Cloud Run

## 📋 Prerequisites

1. **AI Provider API Keys** (at least one required):
   - OpenAI API Key (Primary, recommended)
   - Google Cloud Project with Vertex AI (Secondary)
   - Anthropic API Key (Fallback)
2. **Python 3.11+** installed
3. **gcloud CLI** configured (optional, for GCP deployment)

## 🚀 Quick Start

### Local Development

1. **Clone the repository**:
```bash
git clone <your-repo-url>
cd yt2medium
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys (at least ONE required):
```
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
HUGGINGFACE_TOKEN=your-huggingface-token
PROJECT_ID=your-gcp-project-id
LOCATION=us-central1
PORT=5000
```

**Get API Keys:**
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/settings/keys
- Hugging Face: https://huggingface.co/settings/tokens (for Qwen images)

5. **Authenticate with Google Cloud**:
```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

6. **Run the application**:
```bash
python app.py
```

7. **Open your browser**:
Navigate to `http://localhost:8080`

## ☁️ Deploy to Google Cloud Run

### Using gcloud CLI

1. **Build and deploy**:
```bash
gcloud run deploy yt2medium \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=your-project-id,LOCATION=us-central1 \
  --memory 2Gi \
  --timeout 300
```

2. **Access your deployed app**:
The command will output your service URL. Navigate to it in your browser.

### Using Dockerfile

1. **Build the container**:
```bash
docker build -t yt2medium .
```

2. **Test locally**:
```bash
docker run -p 8080:8080 \
  -e PROJECT_ID=your-project-id \
  -e LOCATION=us-central1 \
  yt2medium
```

3. **Push to Google Container Registry**:
```bash
docker tag yt2medium gcr.io/YOUR_PROJECT_ID/yt2medium
docker push gcr.io/YOUR_PROJECT_ID/yt2medium
```

4. **Deploy to Cloud Run**:
```bash
gcloud run deploy yt2medium \
  --image gcr.io/YOUR_PROJECT_ID/yt2medium \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300
```

## 🎨 What Makes This Special?

### Viral Content Strategy

This tool uses advanced prompt engineering based on analysis of 1000+ viral Medium posts to create content that:

- **Hooks readers in the first 10 seconds**
- **Creates emotional investment** through storytelling
- **Uses psychological triggers** like curiosity gaps and "aha moments"
- **Optimizes for mobile reading** with short paragraphs
- **Delivers actionable value** readers can implement immediately
- **Ends with powerful conclusions** that inspire sharing

### The Engagement Score

Our AI-powered engagement scoring system evaluates:
- Paragraph count and length distribution
- Strategic use of bold text and emphasis
- Question frequency (engagement trigger)
- Optimal word count (1400-2400 sweet spot)
- Subheading structure (4-7 is ideal)
- Quote usage for shareability

A score of **80+** indicates high viral potential!

## 📁 Project Structure

```
yt2medium/
├── app.py                 # Main Flask application
├── prompts.py            # AI prompts optimized for viral content
├── util.py               # Utility functions
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
├── .env.example         # Environment variables template
├── static/
│   └── style.css        # Medium-inspired styling
└── templates/
    ├── index.html       # Landing page
    └── blog-post.html   # Blog post preview
```

## 🎯 Best Practices for Maximum Engagement

### Choosing Your Video
- **Educational content** works best (tutorials, explanations, insights)
- **5-20 minute videos** are optimal (enough content, not too long)
- **Clear audio** ensures better transcription and content quality
- **Well-structured talks** translate better to blog format

### Model Selection
- **OpenAI GPT-5 OSS**: Primary choice, latest flagship model (recommended)
- **Google Gemini 2.0 Flash**: Secondary option, fast and powerful
- **Anthropic Claude Sonnet 4.1**: Fallback option, latest flagship model
- System automatically falls back to next provider if primary fails

### Enhancement Mode
- Enable for **more conversational tone**
- Adds **emotional hooks and storytelling elements**
- Takes 30-60 seconds longer but significantly boosts engagement
- Recommended for content targeting 1000+ claps

### Publishing to Medium
1. Copy the generated Markdown
2. Open Medium's story editor
3. Click the "..." menu and select "Import a story"
4. Paste the Markdown
5. Add tags (use the AI-suggested keywords)
6. Add a subtitle/description
7. Publish!

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (Primary) | Optional |
| `PROJECT_ID` | Google Cloud Project ID (Secondary) | Optional |
| `LOCATION` | GCP region for Vertex AI | `us-central1` |
| `ANTHROPIC_API_KEY` | Anthropic API key (Fallback) | Optional |
| `PORT` | Server port | `8080` |
| `FLASK_ENV` | Flask environment | `production` |

### AI Model Options

Available models in the dropdown:
- `gpt-5-oss` - OpenAI latest flagship model (Primary)
- `gemini-2.0-flash-exp` - Google latest experimental model (Secondary)
- `claude-sonnet-4.1` - Anthropic latest flagship model (Fallback)

System automatically falls back: OpenAI → Gemini → Anthropic

## 🐛 Troubleshooting

### "Could not determine project ID"
- Ensure you've set `PROJECT_ID` in your `.env` file
- Run `gcloud auth application-default login`
- Verify with `gcloud config get-value project`

### "API not enabled"
Enable required APIs:
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativelanguage.googleapis.com
```

### "Image generation failed"
- Check if Imagen API is enabled
- Verify your project has billing enabled
- Some regions may not support Imagen (use `us-central1`)

### Slow generation times
- Video processing takes 30-60 seconds typically
- Enhancement mode adds 30-60 seconds
- Longer videos (>20 min) may take 2-3 minutes
- Check your internet connection

## 💡 Tips for 1000+ Claps

1. **Choose trending topics** in your niche
2. **Publish at optimal times** (Tuesday-Thursday, 9am-2pm EST)
3. **Use strong tags** (5 relevant tags max)
4. **Share immediately** on social media and relevant communities
5. **Engage with comments** within the first hour
6. **Submit to publications** for wider reach
7. **Cross-promote** with other Medium writers
8. **Optimize your author bio** to drive follows

## 🤝 Contributing

This project is based on the [Google Cloud DevRel video-to-blog demo](https://github.com/GoogleCloudPlatform/devrel-demos/tree/main/app-dev/video-to-blog) with significant enhancements for Medium-specific optimization.

## 📄 License

This project follows the Apache License 2.0, consistent with the original Google Cloud demo.

## 🙏 Acknowledgments

- Built on Google Cloud Platform's Vertex AI
- Inspired by the Google Cloud DevRel video-to-blog demo
- Prompt engineering based on analysis of viral Medium content
- UI/UX inspired by Medium's design philosophy

## 📞 Support

For issues, questions, or feature requests, please open an issue in the repository.

---

**Ready to create viral content? Start generating your Medium posts now!** 🚀
