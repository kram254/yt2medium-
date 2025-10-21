# Getting Started with YouTube to Medium

## 🎯 Your First Blog Post in 5 Minutes

This guide walks you through creating your first viral-worthy Medium post from a YouTube video.

---

## Step 1: Prerequisites Check (2 minutes)

### What You Need:
- ✅ Python 3.11 or higher
- ✅ Google Cloud account (with free $300 credits for new users)
- ✅ A YouTube video URL (5-15 minutes recommended)

### Quick Check:
```bash
python --version
```
Should show 3.11 or higher.

---

## Step 2: Google Cloud Setup (3 minutes)

### Create Project:
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "New Project"
3. Name it (e.g., "yt2medium")
4. **Copy your Project ID** (you'll need this!)

### Enable APIs:
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativelanguage.googleapis.com
```

Or via Console:
1. Go to "APIs & Services" > "Library"
2. Search for "Vertex AI API" → Enable
3. Search for "Generative Language API" → Enable

### Set Billing:
1. Go to "Billing" in Cloud Console
2. Link a billing account
3. New users get $300 free credits! 🎉

---

## Step 3: Project Setup (3 minutes)

### Windows (Automated):
```powershell
cd d:\yt2medium
.\quick_start.ps1
```
This script does everything for you!

### Manual Setup (All Platforms):

#### 3.1 Create Virtual Environment:
```bash
cd d:\yt2medium
python -m venv venv
```

#### 3.2 Activate It:
**Windows:**
```powershell
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

#### 3.3 Install Dependencies:
```bash
pip install -r requirements.txt
```

#### 3.4 Configure Environment:
```bash
cp .env.example .env
```

Edit `.env`:
```env
PROJECT_ID=your-project-id-here
LOCATION=us-central1
PORT=8080
```

#### 3.5 Authenticate:
```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

#### 3.6 Verify Setup:
```bash
python test_setup.py
```

You should see all ✅ checks pass!

---

## Step 4: Generate Your First Post (2 minutes)

### Option A: Web Interface (Recommended for First Time)

1. **Start the server:**
```bash
python app.py
```

2. **Open browser:**
Navigate to `http://localhost:8080`

3. **Paste YouTube URL:**
Find a good video (try this one):
```
https://www.youtube.com/watch?v=VnvRFRk_51k
```

4. **Select model:**
Choose "Gemini 2.0 Flash" (recommended)

5. **Optional:**
Check "Apply Advanced Enhancement" for more engaging content

6. **Click "Generate Medium Post"**
Wait 30-60 seconds...

7. **Review your post!**
You'll see:
- Beautiful header image
- Formatted blog post
- Engagement score
- Reading time
- Word count

8. **Copy or Download:**
Click "Copy Markdown" to get the content ready for Medium!

### Option B: Command Line (Quick & Powerful)

```bash
python cli.py "https://www.youtube.com/watch?v=VnvRFRk_51k"
```

Add options:
```bash
python cli.py "VIDEO_URL" --model gemini-1.5-pro --enhance -o my_post.md
```

---

## Step 5: Publish to Medium (5 minutes)

### 5.1 Copy Your Content:
From the web interface, click "📋 Copy Markdown"

### 5.2 Go to Medium:
1. Log in to [Medium.com](https://medium.com)
2. Click "Write" (top right)
3. You'll see a blank story editor

### 5.3 Import Markdown:
1. Click the "..." menu (three dots, top right)
2. Select "Import a story"
3. Paste your Markdown
4. Medium will format it automatically!

### 5.4 Add Finishing Touches:
- **Header Image**: Download the generated image and upload it
- **Title**: The title is already there, but you can tweak it
- **Subtitle**: Add a compelling subtitle (1-2 sentences)
- **Tags**: Add 5 relevant tags (use your video's topic)

### 5.5 Preview & Publish:
1. Click "Preview" to see how it looks
2. Make any final adjustments
3. Click "Publish"
4. Choose distribution (Public, Unlisted, etc.)
5. Click "Publish now"

🎉 **Congratulations! Your first AI-generated Medium post is live!**

---

## Understanding Your Results

### Engagement Score Explained:

| Score | Meaning | What to Do |
|-------|---------|------------|
| 85-100 | Excellent! Viral potential | Publish as-is |
| 70-84 | Good engagement | Minor tweaks, then publish |
| 55-69 | Fair | Review and enhance |
| 0-54 | Needs work | Try different video or re-generate |

### Score is Based On:
- ✅ Optimal word count (1400-2400)
- ✅ Short, readable paragraphs
- ✅ Strategic use of bold text
- ✅ Questions to engage readers
- ✅ Proper heading structure
- ✅ Quotable moments

### Reading Time:
- **7-12 minutes = Ideal** 🎯
- 5-7 minutes = Good (but might lack depth)
- 12-15 minutes = Still good (for complex topics)
- 15+ minutes = May lose readers

---

## Tips for Best Results

### 1. Choose the Right Video

**✅ Great Videos:**
- Educational tutorials
- Technology explanations
- Business insights
- Personal development
- Case studies
- How-to guides

**❌ Avoid:**
- Music videos
- Pure entertainment
- Videos with poor audio
- Very short clips (<3 min)
- Very long videos (>30 min)

### 2. Model Selection Guide

**Gemini 2.0 Flash Exp** (Recommended)
- Best balance of speed and quality
- Great for most videos
- Fast generation (30-45 sec)

**Gemini 1.5 Pro**
- Highest quality output
- Best for complex topics
- Longer videos (15-20 min)
- Slightly slower

**Gemini 1.5 Flash**
- Fastest generation
- Good for short videos
- Quick iterations

### 3. When to Use Enhancement

**Enable Enhancement (✓) When:**
- You want maximum engagement
- Story-driven content
- Personal development topics
- Targeting viral potential

**Skip Enhancement When:**
- Technical documentation
- Speed is priority
- Content is already well-structured

### 4. Boost Your Engagement Score

**Quick Wins:**
- Add questions throughout (reader engagement)
- Use bold for key concepts
- Keep paragraphs short (2-4 sentences)
- Include actionable takeaways
- Add quotes or key insights
- Use subheadings effectively

---

## Common Issues & Solutions

### "Could not determine project ID"
**Fix:**
```bash
# Make sure .env exists with PROJECT_ID
echo "PROJECT_ID=your-project-id" > .env

# Or authenticate again
gcloud auth application-default login
```

### "API not enabled"
**Fix:**
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativelanguage.googleapis.com
```

### "Permission denied"
**Fix:**
```bash
# Make sure you're authenticated
gcloud auth application-default login

# Verify your project
gcloud config get-value project
```

### "Module not found"
**Fix:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Generation is Slow
**Normal behavior:**
- 30-60 seconds for most videos
- 60-120 seconds for long videos or with enhancement
- First generation might be slower (API warmup)

### Low Engagement Score
**Try:**
1. Use enhancement mode
2. Choose a different source video
3. Try Gemini 1.5 Pro model
4. Manually review and add questions/bold text

---

## Next Steps

### Explore More Features:

#### 1. Batch Processing
Generate multiple posts at once:
```bash
python batch_process.py sample_urls.txt
```

#### 2. CLI Power User
```bash
# Show just stats
python cli.py "VIDEO_URL" --stats-only

# Save to file
python cli.py "VIDEO_URL" -o output/my_post.md

# Use best model with enhancement
python cli.py "VIDEO_URL" --model gemini-1.5-pro --enhance
```

#### 3. Deploy to Cloud
Make it accessible online:
```bash
.\deploy.ps1  # Windows
./deploy.sh   # Mac/Linux
```

### Learn More:

- **README.md** - Complete documentation
- **examples.md** - Curated video recommendations
- **setup_guide.md** - Detailed setup instructions
- **CONTRIBUTING.md** - Help improve the project

---

## Your First Week Plan

### Day 1: Setup & First Post
- ✅ Complete setup
- ✅ Generate first post from tutorial video
- ✅ Publish to Medium

### Day 2-3: Experiment
- Try 3-5 different videos
- Test different models
- Compare with/without enhancement
- Learn what works for your niche

### Day 4-5: Optimize
- Review engagement scores
- Tweak titles and intros
- Add personal insights
- Build your style guide

### Day 6-7: Scale
- Set up batch processing
- Create content calendar
- Plan 10 posts
- Track Medium analytics

---

## Success Metrics to Track

### Week 1 Goals:
- [ ] 3-5 posts published
- [ ] Average engagement score 70+
- [ ] 100+ total claps across posts
- [ ] 1-2 comments per post

### Month 1 Goals:
- [ ] 15-20 posts published
- [ ] Average engagement score 80+
- [ ] 1000+ total claps
- [ ] 50+ Medium followers
- [ ] 1-2 viral posts (500+ claps each)

---

## Need Help?

### Quick Resources:
- 🐛 **Bug or Issue**: Open GitHub issue
- 💡 **Feature Idea**: Open discussion
- 📖 **Documentation**: Check README.md
- 🎥 **Examples**: See examples.md

### Community:
- Share your success stories
- Ask questions in discussions
- Contribute improvements
- Help other users

---

## 🎉 You're Ready!

You now have everything you need to create amazing Medium content from YouTube videos.

**Remember:**
1. Choose quality source videos
2. Use appropriate model for content type
3. Review and add personal touches
4. Publish consistently
5. Engage with your readers

**Happy content creation! 🚀**

---

*Questions? Check the [README.md](README.md) or open an issue!*
