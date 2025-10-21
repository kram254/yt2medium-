import os
import base64
from dotenv import load_dotenv
import yt_dlp

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
    
    def generate_image(self, prompt):
        errors = []
        
        if self.openai_client:
            try:
                return self._generate_image_openai(prompt)
            except Exception as e:
                errors.append(f"OpenAI DALL-E: {str(e)}")
        
        if self.gemini_client:
            try:
                return self._generate_image_gemini(prompt)
            except Exception as e:
                errors.append(f"Gemini Imagen: {str(e)}")
        
        return None
    
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
