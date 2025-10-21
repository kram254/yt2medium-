# Quick Reference Guide

One-page reference for YouTube to Medium commands and tips.

---

## 🚀 Quick Start Commands

### First Time Setup
```bash
# Clone/navigate to project
cd d:\yt2medium

# Create environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env: add PROJECT_ID=your-project-id

# Authenticate
gcloud auth application-default login

# Verify
python test_setup.py

# Run
python app.py
```

### Automated Setup (Windows)
```powershell
.\quick_start.ps1
```

---

## 🎯 Common Commands

### Web Application
```bash
python app.py                 # Start web server
python run.py                 # Start with environment check
```
Access at: `http://localhost:8080`

### CLI Generation
```bash
# Basic
python cli.py "YOUTUBE_URL"

# With options
python cli.py "URL" --model gemini-1.5-pro --enhance -o output.md

# Stats only
python cli.py "URL" --stats-only
```

### Batch Processing
```bash
# Basic
python batch_process.py urls.txt

# Custom output directory
python batch_process.py urls.txt output_dir

# Specific model
python batch_process.py urls.txt output gemini-1.5-pro
```

### Testing
```bash
python test_setup.py          # Verify installation
```

### Deployment
```bash
# Windows
.\deploy.ps1

# Mac/Linux
./deploy.sh
```

---

## 📋 Command Options

### CLI Flags

| Flag | Description | Example |
|------|-------------|---------|
| `-m, --model` | Select AI model | `--model gemini-1.5-pro` |
| `-e, --enhance` | Enable enhancement | `--enhance` |
| `-o, --output` | Save to file | `-o post.md` |
| `-s, --stats-only` | Show stats only | `--stats-only` |
| `--no-stats` | Hide statistics | `--no-stats` |

### Model Options

| Model | Best For | Speed |
|-------|----------|-------|
| `gemini-2.0-flash-exp` | Most videos (recommended) | Fast |
| `gemini-1.5-pro` | Complex topics, quality | Medium |
| `gemini-1.5-flash` | Quick generation | Fastest |

---

## 🎨 Input Formats

### Batch Input Files

**Text File (.txt)**
```
https://www.youtube.com/watch?v=video1
https://www.youtube.com/watch?v=video2
```

**CSV File (.csv)**
```csv
url
https://www.youtube.com/watch?v=video1
https://www.youtube.com/watch?v=video2
```

**JSON File (.json)**
```json
["https://www.youtube.com/watch?v=video1"]
```

---

## 📊 Understanding Scores

### Engagement Score

| Range | Quality | Action |
|-------|---------|--------|
| 85-100 | Excellent | Publish now! |
| 70-84 | Good | Minor tweaks |
| 55-69 | Fair | Review & enhance |
| 0-54 | Needs work | Regenerate |

### Reading Time

| Time | Status | Notes |
|------|--------|-------|
| 7-12 min | ✅ Ideal | Perfect for Medium |
| 5-7 min | 🟡 Good | Might lack depth |
| 12-15 min | 🟡 Good | For complex topics |
| 15+ min | ⚠️ Long | May lose readers |

### Word Count

| Count | Status |
|-------|--------|
| 1600-2400 | ✅ Ideal |
| 1400-1600 | 🟡 Good |
| 2400-3000 | 🟡 Good |
| <1400 or >3000 | ⚠️ Outside optimal |

---

## 🔧 Environment Variables

```env
PROJECT_ID=your-gcp-project-id    # Required
LOCATION=us-central1              # Optional (default shown)
PORT=8080                         # Optional (default shown)
FLASK_ENV=development             # Optional
```

---

## 🐛 Quick Troubleshooting

### Common Issues

**"Could not determine project ID"**
```bash
# Solution
echo "PROJECT_ID=your-project-id" > .env
```

**"API not enabled"**
```bash
# Solution
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativelanguage.googleapis.com
```

**"Module not found"**
```bash
# Solution
venv\Scripts\activate  # Activate venv first
pip install -r requirements.txt
```

**"Port already in use"**
```env
# Solution: Change port in .env
PORT=8081
```

---

## 💡 Best Practices

### Video Selection
- ✅ 5-20 minutes long
- ✅ Clear audio
- ✅ Educational content
- ✅ Well-structured
- ❌ Avoid music videos
- ❌ Avoid poor audio
- ❌ Avoid entertainment only

### Model Selection
- **Most cases**: `gemini-2.0-flash-exp`
- **Complex topics**: `gemini-1.5-pro`
- **Speed priority**: `gemini-1.5-flash`

### Enhancement Mode
- **Enable**: Story-driven, viral potential
- **Skip**: Technical docs, speed priority

---

## 📁 File Locations

```
d:/yt2medium/
├── app.py              # Main application
├── cli.py              # CLI tool
├── batch_process.py    # Batch processing
├── prompts.py          # AI prompts
├── util.py             # Utilities
├── config.py           # Configuration
├── .env                # Your settings (create this)
├── requirements.txt    # Dependencies
└── templates/          # HTML templates
    └── static/         # CSS files
```

---

## 🌐 Useful URLs

- **Local App**: `http://localhost:8080`
- **Health Check**: `http://localhost:8080/health`
- **GCP Console**: `https://console.cloud.google.com`
- **Medium**: `https://medium.com`

---

## 📖 Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Complete guide |
| `GETTING_STARTED.md` | Step-by-step tutorial |
| `setup_guide.md` | Setup instructions |
| `TROUBLESHOOTING.md` | Problem solutions |
| `API_REFERENCE.md` | API documentation |
| `examples.md` | Video recommendations |
| `CONTRIBUTING.md` | How to contribute |

---

## 🎯 Workflow Cheat Sheet

### Generate Single Post
```bash
1. python cli.py "VIDEO_URL" --enhance -o post.md
2. Review post.md
3. Copy to Medium
4. Add tags and publish
```

### Generate Multiple Posts
```bash
1. Create urls.txt with video links
2. python batch_process.py urls.txt output
3. Review output/*.md files
4. Publish best scoring posts
```

### Optimize Engagement
```bash
1. Generate with enhancement: --enhance
2. Check score: Look for 80+
3. Use Gemini 1.5 Pro if needed
4. Review key quotes
5. Add personal insights
```

---

## ⚡ Keyboard Shortcuts

### In Web UI
- **Ctrl+C**: Copy from textarea
- **F5**: Refresh page
- **Ctrl+Click**: Open in new tab

### In Terminal
- **Ctrl+C**: Stop server
- **Ctrl+Z**: Background process (Linux/Mac)
- **↑/↓**: Command history

---

## 📈 Publishing Checklist

- [ ] Engagement score 70+
- [ ] Reading time 7-12 min
- [ ] Title is compelling
- [ ] Header image included
- [ ] Key quotes stand out
- [ ] Personal insights added
- [ ] Tags selected (5 max)
- [ ] Subtitle written
- [ ] Preview checked
- [ ] Published at optimal time

---

## 🔑 Key Metrics to Track

**Week 1**
- Posts published: Target 3-5
- Average engagement score: Target 70+
- Total claps: Target 100+

**Month 1**
- Posts published: Target 15-20
- Average engagement score: Target 80+
- Total claps: Target 1000+
- Followers gained: Target 50+

---

## 💾 Backup Important Files

```bash
# Backup your configuration
cp .env .env.backup

# Backup generated posts
cp -r output output_backup
```

---

## 🆘 Emergency Commands

**Reset everything**
```bash
rm -rf venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Clear cache**
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
```

**Check what's running**
```bash
# Windows
netstat -ano | findstr :8080

# Mac/Linux
lsof -i :8080
```

---

## 📞 Quick Help

- **Bug**: Open GitHub issue
- **Question**: Check TROUBLESHOOTING.md
- **Setup**: See GETTING_STARTED.md
- **API**: See API_REFERENCE.md

---

**Print this page for quick reference!**

*Updated: 2025-10-08*
