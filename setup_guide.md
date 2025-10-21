# Quick Setup Guide for YouTube to Medium

## Step-by-Step Instructions

### 1. Google Cloud Setup (5 minutes)

#### Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "New Project" 
3. Enter a project name (e.g., "yt2medium")
4. Note your Project ID (you'll need this)

#### Enable Required APIs
Run these commands (or enable via Cloud Console):
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativelanguage.googleapis.com
```

#### Set up Billing
1. Go to [Billing](https://console.cloud.google.com/billing)
2. Link a billing account to your project
3. You'll get $300 in free credits if you're a new user

### 2. Local Development Setup (5 minutes)

#### Install Python
Make sure you have Python 3.11 or higher:
```bash
python --version
```

#### Clone/Download the Project
```bash
cd d:/yt2medium
```

#### Create Virtual Environment
```bash
python -m venv venv
```

Activate it:
- **Windows**: `venv\Scripts\activate`
- **Mac/Linux**: `source venv/bin/activate`

#### Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configuration (2 minutes)

#### Set up Environment Variables
Create a `.env` file:
```bash
cp .env.example .env
```

Edit `.env` with your details:
```
PROJECT_ID=your-project-id-here
LOCATION=us-central1
PORT=8080
```

#### Authenticate with Google Cloud
```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 4. Run the Application (1 minute)

#### Start the server
```bash
python run.py
```

Or directly:
```bash
python app.py
```

#### Open in Browser
Navigate to: `http://localhost:8080`

### 5. Test It Out

1. Find a YouTube video (5-15 minutes works best)
2. Copy the URL
3. Paste it into the app
4. Select your AI model
5. Click "Generate Medium Post"
6. Wait 30-60 seconds
7. Review your viral-ready blog post!

## Common Issues & Solutions

### Issue: "Could not determine project ID"
**Solution**: 
- Make sure `.env` file exists with `PROJECT_ID` set
- Run `gcloud auth application-default login`

### Issue: "API not enabled"
**Solution**:
```bash
gcloud services enable aiplatform.googleapis.com
```

### Issue: "Billing not enabled"
**Solution**:
- Go to Cloud Console > Billing
- Enable billing for your project
- You get $300 free credits as a new user

### Issue: "Module not found"
**Solution**:
```bash
pip install -r requirements.txt
```

### Issue: Port already in use
**Solution**:
- Change `PORT` in `.env` to different number (e.g., 8081)
- Or kill the process using port 8080

## Cost Estimates

### Per Blog Post Generation:
- **Video processing (Gemini)**: ~$0.01-0.05
- **Image generation (Imagen)**: ~$0.02
- **Total per post**: ~$0.03-0.07

### Monthly estimates (if generating 100 posts):
- **Cost**: ~$3-7/month
- **Free tier**: $300 credits cover ~4,000-10,000 posts

## Next Steps

### Deploy to Cloud Run (Optional)
Make your app accessible online:
```bash
gcloud run deploy yt2medium \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

### Customize Prompts
Edit `prompts.py` to adjust:
- Writing style
- Content structure
- Engagement optimization
- Image generation style

### Add Features
Consider adding:
- Multiple language support
- Custom brand voice
- SEO optimization
- Direct Medium API publishing
- Batch processing

## Tips for Success

1. **Choose good source videos**:
   - Clear audio quality
   - Well-structured content
   - 5-20 minutes ideal length
   - Educational or insightful topics

2. **Optimize for engagement**:
   - Enable "Enhancement Mode" for best results
   - Use Gemini 2.0 Flash for balance of speed/quality
   - Review and tweak before publishing

3. **Publishing strategy**:
   - Add relevant tags on Medium
   - Write a compelling subtitle
   - Publish during peak times (Tue-Thu, 9am-2pm EST)
   - Share immediately on social media

4. **Track performance**:
   - Monitor which topics get most claps
   - A/B test different writing styles
   - Engage with comments early
   - Submit to Medium publications

## Need Help?

- **Documentation**: See `README.md`
- **Google Cloud Docs**: [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- **Issues**: Open an issue in the repository

---

**You're all set! Start generating viral Medium content now!** 🚀
