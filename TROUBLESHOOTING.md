# Troubleshooting Guide

Comprehensive solutions to common issues with YouTube to Medium.

---

## 🔧 Setup Issues

### Python Version Error

**Symptom:**
```
❌ Python 3.10.5 (Need 3.11+)
```

**Solution:**
1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Restart your terminal
4. Verify: `python --version`

---

### Virtual Environment Issues

**Symptom:**
```
'venv' is not recognized as internal or external command
```

**Solution Windows:**
```powershell
python -m venv venv
```

**Solution Mac/Linux:**
```bash
python3 -m venv venv
```

**Activation Issues:**

**Windows PowerShell:**
```powershell
# If you get execution policy error
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

---

### Dependency Installation Errors

**Symptom:**
```
ERROR: Could not find a version that satisfies the requirement...
```

**Solution 1 - Update pip:**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Solution 2 - Install individually:**
```bash
pip install Flask==3.0.0
pip install google-generativeai
pip install google-genai
pip install google-auth
pip install Markdown
pip install python-dotenv
pip install gunicorn
```

**Solution 3 - Use older versions:**
If specific versions fail, try:
```bash
pip install Flask google-generativeai google-genai google-auth Markdown python-dotenv gunicorn
```

---

## 🔐 Authentication Issues

### "Could not determine the project ID"

**Symptom:**
```
ValueError: Could not determine the project ID.
```

**Solution 1 - Set Environment Variable:**
```bash
# Make sure .env file exists
cp .env.example .env

# Edit .env and add:
PROJECT_ID=your-actual-project-id
```

**Solution 2 - gcloud Authentication:**
```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

**Solution 3 - Verify Project:**
```bash
gcloud config get-value project
```

---

### "default credentials were not found"

**Symptom:**
```
google.auth.exceptions.DefaultCredentialsError
```

**Solution:**
```bash
# Authenticate with gcloud
gcloud auth application-default login

# Follow the browser prompts to login
```

**Alternative - Service Account:**
1. Create service account in Cloud Console
2. Download JSON key
3. Set environment variable:
```bash
# Windows
set GOOGLE_APPLICATION_CREDENTIALS=path\to\key.json

# Mac/Linux
export GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json
```

---

## 🌐 API Issues

### "API [aiplatform.googleapis.com] not enabled"

**Symptom:**
```
Error 403: API not enabled for project
```

**Solution:**
```bash
# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativelanguage.googleapis.com

# Or via Console:
# 1. Go to APIs & Services > Library
# 2. Search for "Vertex AI API" → Enable
# 3. Search for "Generative Language API" → Enable
```

**Verify APIs are enabled:**
```bash
gcloud services list --enabled
```

---

### "Billing not enabled"

**Symptom:**
```
Error: This API method requires billing to be enabled
```

**Solution:**
1. Go to [Cloud Console Billing](https://console.cloud.google.com/billing)
2. Select your project
3. Link a billing account
4. Enable billing

**Note:** New users get $300 in free credits!

---

### Rate Limit / Quota Exceeded

**Symptom:**
```
429 Resource has been exhausted
```

**Solution:**
1. Wait a few minutes and retry
2. Check quotas in Cloud Console
3. Request quota increase if needed
4. Use exponential backoff:
```python
import time
retry_count = 0
while retry_count < 3:
    try:
        # Your API call
        break
    except Exception as e:
        retry_count += 1
        time.sleep(2 ** retry_count)
```

---

## 🎬 Video Processing Issues

### "Invalid YouTube URL"

**Symptom:**
```
❌ Invalid YouTube URL
```

**Valid formats:**
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `http://www.youtube.com/watch?v=VIDEO_ID`

**Invalid formats:**
- `youtube.com/VIDEO_ID` (missing protocol)
- `www.youtube.com/shorts/...` (shorts not fully supported)
- Playlist URLs

---

### Video Too Long

**Symptom:**
Slow processing or timeout

**Solution:**
- Keep videos under 20 minutes for best results
- Use Gemini 1.5 Pro for longer videos
- Increase timeout in deployment:
```bash
gcloud run deploy --timeout 600
```

---

### Poor Quality Output

**Symptom:**
Low engagement score, disjointed content

**Possible Causes & Solutions:**

1. **Poor audio quality**
   - Choose videos with clear audio
   - Avoid heavy background music
   - Avoid multiple speakers talking over each other

2. **Wrong video type**
   - Avoid pure entertainment content
   - Use educational/tutorial videos
   - Structured presentations work best

3. **Video too short**
   - Need 5+ minutes of content
   - Shorter videos don't have enough material

4. **Try different model:**
   - Switch to Gemini 1.5 Pro
   - Enable enhancement mode
   - Regenerate 2-3 times if needed

---

## 🖼️ Image Generation Issues

### "Image generation failed"

**Symptom:**
```
Image generation error: ...
```

**Solution 1 - Check API:**
```bash
gcloud services enable aiplatform.googleapis.com
```

**Solution 2 - Region:**
Imagen may not be available in all regions. Use `us-central1`:
```env
LOCATION=us-central1
```

**Solution 3 - Continue without image:**
The app will continue even if image generation fails. You'll just need to add your own header image.

---

## 💻 Runtime Issues

### Port Already in Use

**Symptom:**
```
Address already in use: Port 8080
```

**Solution 1 - Change Port:**
Edit `.env`:
```env
PORT=8081
```

**Solution 2 - Kill Process:**

**Windows:**
```powershell
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

**Mac/Linux:**
```bash
lsof -i :8080
kill -9 <PID>
```

---

### Module Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'flask'
```

**Solution:**
1. Activate virtual environment:
```bash
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

2. Reinstall dependencies:
```bash
pip install -r requirements.txt
```

3. Verify installation:
```bash
pip list
```

---

### Flask Not Starting

**Symptom:**
App starts but you can't access it

**Solution:**
Make sure Flask is binding to correct host:
```python
# In app.py
app.run(debug=True, port=8080, host='0.0.0.0')
```

Access via:
- `http://localhost:8080`
- `http://127.0.0.1:8080`

---

## 🚀 Deployment Issues

### Cloud Run Deployment Fails

**Symptom:**
```
ERROR: build step failed
```

**Solution 1 - Enable Cloud Build:**
```bash
gcloud services enable cloudbuild.googleapis.com
```

**Solution 2 - Check Dockerfile:**
Ensure Dockerfile is correct and all files are present.

**Solution 3 - Manual Build:**
```bash
# Build locally
docker build -t yt2medium .

# Test locally
docker run -p 8080:8080 -e PROJECT_ID=your-project yt2medium

# If works, push to GCR
docker tag yt2medium gcr.io/YOUR_PROJECT/yt2medium
docker push gcr.io/YOUR_PROJECT/yt2medium

# Deploy
gcloud run deploy yt2medium --image gcr.io/YOUR_PROJECT/yt2medium
```

---

### Deployed App Times Out

**Symptom:**
502 or 504 errors on Cloud Run

**Solution:**
Increase timeout and resources:
```bash
gcloud run deploy yt2medium \
  --timeout 300 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10
```

---

## 📊 Performance Issues

### Very Slow Generation

**Expected times:**
- 5-7 min video: 30-45 seconds
- 8-15 min video: 45-75 seconds
- 16-20 min video: 75-120 seconds
- With enhancement: +30-60 seconds

**If slower:**
1. Check internet connection
2. Try different region (us-central1 recommended)
3. Check GCP status page for outages
4. Use Gemini 1.5 Flash for faster generation

---

### High Memory Usage

**Solution:**
```python
# In app.py, limit content length
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
```

For Cloud Run:
```bash
gcloud run deploy --memory 2Gi
```

---

## 🔍 Debugging Tips

### Enable Debug Mode

**Local development:**
```python
# In app.py
app.run(debug=True)
```

**Add logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

### Test API Connection

```python
python test_setup.py
```

This checks:
- ✅ Python version
- ✅ Dependencies installed
- ✅ Environment variables
- ✅ gcloud authentication
- ✅ API connection

---

### Verify Individual Components

**Test Gemini:**
```python
from google import genai
from util import get_project_id

client = genai.Client(vertexai=True, project=get_project_id())
response = client.models.generate_content(
    model='gemini-2.0-flash-exp',
    contents='Hello, test message'
)
print(response.text)
```

**Test Imagen:**
```python
response = client.models.generate_images(
    model='imagen-3.0-generate-001',
    prompt='A beautiful sunset'
)
print("Image generated successfully!")
```

---

## 🆘 Getting Help

### Before Opening an Issue:

1. **Run diagnostics:**
```bash
python test_setup.py
```

2. **Check logs:**
Look for error messages and stack traces

3. **Try minimal example:**
Use CLI with a simple video first

4. **Collect information:**
- OS and Python version
- Error messages (full stack trace)
- Steps to reproduce
- What you've tried already

### Opening an Issue:

Include:
- **Title**: Clear, descriptive summary
- **Environment**: OS, Python version, etc.
- **Steps to Reproduce**: Exact steps to trigger issue
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Error Messages**: Full stack trace
- **Attempts**: What you've tried

---

## 📚 Additional Resources

- **Setup Guide**: `setup_guide.md`
- **Full Documentation**: `README.md`
- **Examples**: `examples.md`
- **Contributing**: `CONTRIBUTING.md`

- **Google Cloud Docs**: [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- **Gemini API**: [Gemini API Guide](https://ai.google.dev/docs)

---

## ✅ Prevention Checklist

Before starting a new project:

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed from requirements.txt
- [ ] .env file configured with PROJECT_ID
- [ ] gcloud authenticated
- [ ] Required APIs enabled
- [ ] Billing enabled on GCP project
- [ ] test_setup.py passes all checks

---

**Still having issues? Open an issue on GitHub with details!**
