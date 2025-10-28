import os
import json
import requests
import ssl
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import urllib3

load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TokenEncryption:
    def __init__(self):
        self.key = os.environ.get('ENCRYPTION_KEY')
        if not self.key:
            self.key = Fernet.generate_key().decode()
            print(f"Generate ENCRYPTION_KEY: {self.key}")
        self.cipher = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
    
    def encrypt(self, token):
        return self.cipher.encrypt(token.encode()).decode()
    
    def decrypt(self, encrypted_token):
        try:
            return self.cipher.decrypt(encrypted_token.encode()).decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            return None

class MediumAuth:
    def __init__(self):
        self.client_id = os.environ.get('MEDIUM_CLIENT_ID')
        self.client_secret = os.environ.get('MEDIUM_CLIENT_SECRET')
        self.redirect_uri = os.environ.get('MEDIUM_REDIRECT_URI', 'http://localhost:8000/auth/medium/callback')
        self.auth_url = 'https://medium.com/m/oauth/authorize'
        self.token_url = 'https://api.medium.com/v1/tokens'
        self.api_base = 'https://api.medium.com/v1'
        self.encryption = TokenEncryption()
    
    def get_auth_url(self, state):
        params = {
            'client_id': self.client_id,
            'scope': 'basicProfile,publishPost',
            'state': state,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri
        }
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"{self.auth_url}?{query_string}"
    
    def exchange_code_for_token(self, code):
        try:
            if not code or len(code) < 10:
                return None
            
            data = {
                'code': code,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            response = requests.post(
                self.token_url,
                json=data,
                timeout=15,
                verify=True
            )
            response.raise_for_status()
            result = response.json()
            
            if not result.get('access_token'):
                return None
            
            return {
                'access_token': result.get('access_token'),
                'token_type': result.get('token_type', 'Bearer'),
                'expires_at': (datetime.utcnow() + timedelta(seconds=result.get('expires_in', 3600))).isoformat()
            }
        except Exception as e:
            print(f"Medium token exchange error: {e}")
            return None
    
    def get_user_info(self, access_token):
        try:
            if not access_token:
                return None
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
            response = requests.get(
                f'{self.api_base}/me',
                headers=headers,
                timeout=15,
                verify=True
            )
            response.raise_for_status()
            data = response.json()
            
            user_data = data.get('data', {})
            if not user_data.get('id'):
                return None
            
            return {
                'id': user_data.get('id'),
                'username': user_data.get('username'),
                'name': user_data.get('name'),
                'url': user_data.get('url'),
                'image_url': user_data.get('imageUrl')
            }
        except Exception as e:
            print(f"Medium user info error: {e}")
            return None
    
    def publish_post(self, access_token, title, content, tags=None, image_url=None):
        try:
            if not access_token or not title or not content:
                return {'success': False, 'error': 'Missing required fields'}
            
            user_info = self.get_user_info(access_token)
            if not user_info:
                return {'success': False, 'error': 'Failed to get user info'}
            
            if len(title) > 500:
                return {'success': False, 'error': 'Title too long'}
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            post_data = {
                'title': title[:500],
                'contentFormat': 'html',
                'content': content,
                'publishStatus': 'draft',
                'tags': tags[:5] if tags else []
            }
            
            response = requests.post(
                f"{self.api_base}/users/{user_info['id']}/posts",
                json=post_data,
                headers=headers,
                timeout=20,
                verify=True
            )
            response.raise_for_status()
            result = response.json()
            
            post_data_result = result.get('data', {})
            if not post_data_result.get('id'):
                return {'success': False, 'error': 'No post ID returned'}
            
            return {
                'success': True,
                'post_id': post_data_result.get('id'),
                'url': post_data_result.get('url'),
                'status': post_data_result.get('publishStatus')
            }
        except Exception as e:
            print(f"Medium publish error: {e}")
            return {'success': False, 'error': 'Publishing failed'}

class LinkedInAuth:
    def __init__(self):
        self.client_id = os.environ.get('LINKEDIN_CLIENT_ID')
        self.client_secret = os.environ.get('LINKEDIN_CLIENT_SECRET')
        self.redirect_uri = os.environ.get('LINKEDIN_REDIRECT_URI', 'http://localhost:8000/auth/linkedin/callback')
        self.auth_url = 'https://www.linkedin.com/oauth/v2/authorization'
        self.token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
        self.api_base = 'https://api.linkedin.com/v2'
        self.encryption = TokenEncryption()
    
    def get_auth_url(self, state):
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': state,
            'scope': 'w_member_social,r_liteprofile,r_emailaddress'
        }
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"{self.auth_url}?{query_string}"
    
    def exchange_code_for_token(self, code):
        try:
            if not code or len(code) < 10:
                return None
            
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.redirect_uri,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            response = requests.post(
                self.token_url,
                data=data,
                timeout=15,
                verify=True
            )
            response.raise_for_status()
            result = response.json()
            
            if not result.get('access_token'):
                return None
            
            return {
                'access_token': result.get('access_token'),
                'token_type': result.get('token_type', 'Bearer'),
                'expires_in': result.get('expires_in'),
                'expires_at': (datetime.utcnow() + timedelta(seconds=result.get('expires_in', 3600))).isoformat()
            }
        except Exception as e:
            print(f"LinkedIn token exchange error: {e}")
            return None
    
    def get_user_info(self, access_token):
        try:
            if not access_token:
                return None
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
            response = requests.get(
                f'{self.api_base}/me',
                headers=headers,
                timeout=15,
                verify=True
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('id'):
                return None
            
            return {
                'id': data.get('id'),
                'first_name': data.get('localizedFirstName'),
                'last_name': data.get('localizedLastName'),
                'profile_url': data.get('profileUrl')
            }
        except Exception as e:
            print(f"LinkedIn user info error: {e}")
            return None
    
    def share_post(self, access_token, text, image_url=None):
        try:
            if not access_token or not text:
                return {'success': False, 'error': 'Missing required fields'}
            
            user_info = self.get_user_info(access_token)
            if not user_info:
                return {'success': False, 'error': 'Failed to get user info'}
            
            if len(text) > 3000:
                text = text[:3000]
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            post_data = {
                'actor': f"urn:li:person:{user_info['id']}",
                'object': 'urn:li:share:0',
                'lifecycleState': 'PUBLISHED',
                'specificContent': {
                    'com.linkedin.ugc.ShareContent': {
                        'shareCommentary': {
                            'text': text
                        },
                        'shareMediaCategory': 'ARTICLE'
                    }
                },
                'visibility': {
                    'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
                }
            }
            
            if image_url and isinstance(image_url, str) and len(image_url) > 10:
                post_data['specificContent']['com.linkedin.ugc.ShareContent']['media'] = [{
                    'status': 'READY',
                    'description': {
                        'text': 'Blog Post Image'
                    },
                    'media': image_url,
                    'title': {
                        'text': 'Blog Post'
                    }
                }]
            
            response = requests.post(
                f'{self.api_base}/ugcPosts',
                json=post_data,
                headers=headers,
                timeout=20,
                verify=True
            )
            response.raise_for_status()
            result = response.json()
            
            if not result.get('id'):
                return {'success': False, 'error': 'No post ID returned'}
            
            return {
                'success': True,
                'post_id': result.get('id'),
                'status': 'published'
            }
        except Exception as e:
            print(f"LinkedIn share error: {e}")
            return {'success': False, 'error': 'Sharing failed'}

def get_medium_auth():
    return MediumAuth()

def get_linkedin_auth():
    return LinkedInAuth()

def get_token_encryption():
    return TokenEncryption()
