import os
import requests
import base64
from urllib.parse import urlparse

class GitHubHandler:
    def __init__(self, token=None):
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.base_url = 'https://api.github.com'
        self.headers = {
            'Accept': 'application/vnd.github.v3.raw',
            'User-Agent': 'YT2Medium'
        }
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
    
    def parse_github_url(self, url):
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            return None
        
        owner = path_parts[0]
        repo = path_parts[1].replace('.git', '')
        
        file_path = None
        if len(path_parts) > 4 and path_parts[2] in ['blob', 'tree']:
            branch = path_parts[3]
            file_path = '/'.join(path_parts[4:])
        
        return {
            'owner': owner,
            'repo': repo,
            'branch': 'main',
            'file_path': file_path
        }
    
    def get_file_content(self, url):
        try:
            repo_info = self.parse_github_url(url)
            if not repo_info:
                return None
            
            owner = repo_info['owner']
            repo = repo_info['repo']
            file_path = repo_info['file_path']
            branch = repo_info['branch']
            
            if not file_path:
                return None
            
            api_url = f'{self.base_url}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}'
            
            response = requests.get(api_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                if response.headers.get('content-type') == 'application/json':
                    data = response.json()
                    if 'content' in data:
                        return base64.b64decode(data['content']).decode('utf-8')
                else:
                    return response.text
            elif response.status_code == 404:
                return None
            else:
                return None
                
        except Exception as e:
            print(f"GitHub fetch error: {e}")
            return None
    
    def get_readme(self, url):
        try:
            repo_info = self.parse_github_url(url)
            if not repo_info:
                return None
            
            owner = repo_info['owner']
            repo = repo_info['repo']
            
            for readme_name in ['README.md', 'readme.md', 'README.txt', 'readme.txt']:
                api_url = f'{self.base_url}/repos/{owner}/{repo}/contents/{readme_name}'
                response = requests.get(api_url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    if response.headers.get('content-type') == 'application/json':
                        data = response.json()
                        if 'content' in data:
                            return base64.b64decode(data['content']).decode('utf-8')
                    else:
                        return response.text
            
            return None
            
        except Exception as e:
            print(f"GitHub README fetch error: {e}")
            return None
    
    def list_files(self, url, path=''):
        try:
            repo_info = self.parse_github_url(url)
            if not repo_info:
                return None
            
            owner = repo_info['owner']
            repo = repo_info['repo']
            
            api_url = f'{self.base_url}/repos/{owner}/{repo}/contents/{path}'
            response = requests.get(api_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return [
                        {
                            'name': item['name'],
                            'type': item['type'],
                            'path': item['path'],
                            'size': item.get('size', 0)
                        }
                        for item in data
                    ]
            
            return None
            
        except Exception as e:
            print(f"GitHub list files error: {e}")
            return None
    
    def get_repo_info(self, url):
        try:
            repo_info = self.parse_github_url(url)
            if not repo_info:
                return None
            
            owner = repo_info['owner']
            repo = repo_info['repo']
            
            api_url = f'{self.base_url}/repos/{owner}/{repo}'
            response = requests.get(api_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'name': data.get('name'),
                    'description': data.get('description'),
                    'url': data.get('html_url'),
                    'stars': data.get('stargazers_count'),
                    'language': data.get('language'),
                    'topics': data.get('topics', []),
                    'readme_url': data.get('readme_url')
                }
            
            return None
            
        except Exception as e:
            print(f"GitHub repo info error: {e}")
            return None

def get_github_handler():
    return GitHubHandler()
