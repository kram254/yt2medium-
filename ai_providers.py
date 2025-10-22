import os
import base64
import re
from dotenv import load_dotenv
import yt_dlp
import requests
from bs4 import BeautifulSoup
from datetime import datetime

load_dotenv()

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

def get_youtube_transcript(youtube_url):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            
            title = info.get('title', 'Untitled')
            description = info.get('description', '')
            
            subtitles = info.get('subtitles', {})
            auto_captions = info.get('automatic_captions', {})
            
            transcript_text = ""
            
            if 'en' in subtitles:
                transcript_text = _extract_subtitle_text(subtitles['en'])
            elif 'en' in auto_captions:
                transcript_text = _extract_subtitle_text(auto_captions['en'])
            
            video_context = f"Video Title: {title}\n\nDescription: {description}\n\nTranscript:\n{transcript_text}"
            
            return video_context
    except Exception as e:
        raise Exception(f"Failed to extract video content: {str(e)}")

def _extract_subtitle_text(subtitle_list):
    for sub in subtitle_list:
        if sub.get('ext') in ['vtt', 'srv1', 'srv2', 'srv3']:
            url = sub.get('url')
            if url:
                try:
                    import requests
                    response = requests.get(url)
                    return _clean_vtt_text(response.text)
                except:
                    continue
    return ""

def _clean_vtt_text(vtt_content):
    lines = vtt_content.split('\n')
    text_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('WEBVTT') and not '-->' in line and not line.isdigit():
            text_lines.append(line)
    return ' '.join(text_lines)

def detect_input_type(user_input):
    youtube_patterns = [
        r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+',
    ]
    for pattern in youtube_patterns:
        if re.match(pattern, user_input):
            return 'youtube'
    
    url_pattern = r'https?://[^\s]+'
    if re.match(url_pattern, user_input):
        return 'url'
    
    return 'prompt'

def scrape_web_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        title = soup.find('title')
        title_text = title.get_text() if title else ''
        
        article = soup.find('article') or soup.find('main') or soup.find('body')
        
        paragraphs = article.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']) if article else []
        content_parts = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
        content = '\n\n'.join(content_parts)
        
        return f"Title: {title_text}\n\nURL: {url}\n\nContent:\n{content[:15000]}"
    except Exception as e:
        raise Exception(f"Failed to scrape URL: {str(e)}")

def research_trending_topic(topic_query, ai_manager):
    current_date = datetime.now().strftime("%B %d, %Y")
    
    research_prompt = f"""Today is {current_date}. Research and provide comprehensive information about: {topic_query}

Provide:
1. Latest developments and trending aspects (within the last week if possible)
2. Key facts, statistics, and data points
3. Important companies, people, or projects involved
4. Controversies or debates in the field
5. Future implications and predictions
6. Concrete examples and use cases

Make this research detailed and up-to-date. Focus on what's actually trending and newsworthy right now."""
    
    research_content = ai_manager.generate_content(research_prompt)
    return f"Research Date: {current_date}\n\nTopic: {topic_query}\n\n{research_content}"

class AIProviderManager:
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.gemini_client = None
        
        if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        if ANTHROPIC_AVAILABLE and os.getenv('ANTHROPIC_API_KEY'):
            self.anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        if GEMINI_AVAILABLE:
            try:
                from util import get_project_id
                self.gemini_client = genai.Client(
                    vertexai=True,
                    project=get_project_id(),
                    location=os.getenv('LOCATION', 'us-central1'),
                )
            except:
                self.gemini_client = None
    
    def generate_content(self, prompt, video_context=None):
        errors = []
        
        if self.openai_client:
            try:
                return self._generate_with_openai(prompt, video_context)
            except Exception as e:
                errors.append(f"OpenAI: {str(e)}")
        
        if self.gemini_client:
            try:
                return self._generate_with_gemini(prompt, video_context)
            except Exception as e:
                errors.append(f"Gemini: {str(e)}")
        
        if self.anthropic_client:
            try:
                return self._generate_with_anthropic(prompt, video_context)
            except Exception as e:
                errors.append(f"Anthropic: {str(e)}")
        
        raise Exception(f"All AI providers failed: {'; '.join(errors)}")
    
    def _generate_with_openai(self, prompt, video_context):
        if video_context:
            full_prompt = f"{video_context}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert Medium writer and content strategist."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.9,
            max_tokens=8192
        )
        
        return response.choices[0].message.content
    
    def _generate_with_gemini(self, prompt, video_context):
        if video_context:
            full_prompt = f"{video_context}\n\n{prompt}"
            contents = [types.Part.from_text(text=full_prompt)]
        else:
            contents = [types.Part.from_text(text=prompt)]
        
        response = self.gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.9,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
            )
        )
        
        return response.text
    
    def _generate_with_anthropic(self, prompt, video_context):
        if video_context:
            full_prompt = f"{video_context}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8192,
            temperature=0.9,
            messages=[
                {"role": "user", "content": full_prompt}
            ]
        )
        
        return response.content[0].text
    
    def generate_images(self, prompt1, prompt2):
        errors = []
        images = []
        
        if self.openai_client:
            try:
                img1 = self._generate_image_openai(prompt1)
                images.append(img1)
                try:
                    img2 = self._generate_image_openai(prompt2)
                    images.append(img2)
                except:
                    images.append(None)
                return images
            except Exception as e:
                errors.append(f"OpenAI DALL-E: {str(e)}")
        
        try:
            qwen_images = self._generate_images_qwen(prompt1, prompt2)
            if qwen_images and len(qwen_images) >= 2:
                return qwen_images
        except Exception as e:
            errors.append(f"Qwen: {str(e)}")
        
        if self.gemini_client:
            try:
                img1 = self._generate_image_gemini(prompt1)
                images.append(img1)
                try:
                    img2 = self._generate_image_gemini(prompt2)
                    images.append(img2)
                except:
                    images.append(None)
                return images
            except Exception as e:
                errors.append(f"Gemini Imagen: {str(e)}")
        
        return [None, None]
    
    def _generate_image_openai(self, prompt):
        response = self.openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        
        import requests
        img_response = requests.get(image_url)
        encoded_image = base64.b64encode(img_response.content).decode('utf-8')
        
        return encoded_image
    
    def _generate_image_gemini(self, prompt):
        response = self.gemini_client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type='image/png',
            ),
        )
        image_data = response.generated_images[0].image.image_bytes
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        
        return encoded_image
    
    def _generate_images_qwen(self, prompt1, prompt2):
        API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2-VL-7B-Instruct"
        hf_token = os.getenv('HUGGINGFACE_TOKEN')
        
        if not hf_token:
            raise Exception("HUGGINGFACE_TOKEN not configured")
        
        headers = {"Authorization": f"Bearer {hf_token}"}
        images = []
        
        for prompt in [prompt1, prompt2]:
            try:
                response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=60)
                if response.status_code == 200:
                    encoded_image = base64.b64encode(response.content).decode('utf-8')
                    images.append(encoded_image)
                else:
                    images.append(None)
            except:
                images.append(None)
        
        return images
