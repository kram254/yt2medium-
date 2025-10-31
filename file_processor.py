import os
import tempfile
from pathlib import Path
import mimetypes

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

import json

def extract_text_from_pdf(file_path):
    if not PdfReader:
        return None
    
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def extract_text_from_docx(file_path):
    if not Document:
        return None
    
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return None

def extract_text_from_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading TXT: {e}")
        return None

def extract_text_from_image(file_path):
    if not Image or not pytesseract:
        return None
    
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        print(f"Error reading image: {e}")
        return None

def extract_text_from_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return json.dumps(data, indent=2)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return None

def extract_text_from_markdown(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading Markdown: {e}")
        return None

def process_uploaded_file(file_path, filename):
    mime_type, _ = mimetypes.guess_type(filename)
    extension = Path(filename).suffix.lower()
    
    text_content = None
    file_type = "unknown"
    
    if extension == '.pdf' or (mime_type and 'pdf' in mime_type):
        text_content = extract_text_from_pdf(file_path)
        file_type = "pdf"
    elif extension in ['.docx', '.doc'] or (mime_type and 'word' in mime_type):
        text_content = extract_text_from_docx(file_path)
        file_type = "document"
    elif extension == '.txt' or (mime_type and mime_type.startswith('text/')):
        text_content = extract_text_from_txt(file_path)
        file_type = "text"
    elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'] or (mime_type and mime_type.startswith('image/')):
        text_content = extract_text_from_image(file_path)
        file_type = "image"
    elif extension == '.json':
        text_content = extract_text_from_json(file_path)
        file_type = "json"
    elif extension in ['.md', '.markdown']:
        text_content = extract_text_from_markdown(file_path)
        file_type = "markdown"
    
    if not text_content:
        with open(file_path, 'rb') as f:
            content = f.read()
            try:
                text_content = content.decode('utf-8', errors='ignore')
                file_type = "raw_text"
            except:
                return None, file_type
    
    return text_content, file_type

def get_supported_extensions():
    extensions = ['.txt', '.md', '.json']
    
    if PdfReader:
        extensions.extend(['.pdf'])
    
    if Document:
        extensions.extend(['.docx', '.doc'])
    
    if Image and pytesseract:
        extensions.extend(['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'])
    
    return extensions

def is_file_supported(filename):
    extension = Path(filename).suffix.lower()
    return extension in get_supported_extensions() or extension == ''
