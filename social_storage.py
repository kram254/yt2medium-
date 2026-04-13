import os
import json
from datetime import datetime
from pathlib import Path
from social_auth import get_token_encryption
from tenant_context import current_tenant_id, normalize_tenant_id

SOCIAL_DATA_DIR = Path(__file__).parent / 'social_data'
SOCIAL_DATA_DIR.mkdir(exist_ok=True)

class SocialAccountManager:
    def __init__(self):
        self.encryption = get_token_encryption()
        self.data_dir = SOCIAL_DATA_DIR
    
    def _tenant_dir(self, tenant_id=None):
        tenant_id = normalize_tenant_id(tenant_id or current_tenant_id()) or 'legacy'
        tenant_dir = self.data_dir / tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        return tenant_dir

    def _account_path(self, user_id, platform, tenant_id=None):
        return self._tenant_dir(tenant_id) / str(user_id) / f'{platform}_account.json'

    def save_account(self, user_id, platform, account_data, tenant_id=None):
        try:
            user_dir = self._tenant_dir(tenant_id) / str(user_id)
            user_dir.mkdir(parents=True, exist_ok=True)
            
            encrypted_data = {
                'platform': platform,
                'user_info': account_data.get('user_info', {}),
                'access_token': self.encryption.encrypt(account_data.get('access_token', '')),
                'token_type': account_data.get('token_type'),
                'expires_at': account_data.get('expires_at'),
                'created_at': datetime.utcnow().isoformat(),
                'last_used': datetime.utcnow().isoformat(),
                'tenant_id': normalize_tenant_id(tenant_id or current_tenant_id()) or 'legacy'
            }
            
            file_path = user_dir / f'{platform}_account.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(encrypted_data, f, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving {platform} account: {e}")
            return False
    
    def get_account(self, user_id, platform, tenant_id=None):
        try:
            file_path = self._account_path(user_id, platform, tenant_id)
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                encrypted_data = json.load(f)
            if normalize_tenant_id(encrypted_data.get('tenant_id')) not in {normalize_tenant_id(tenant_id or current_tenant_id()), 'legacy', None}:
                return None
            
            access_token = self.encryption.decrypt(encrypted_data.get('access_token', ''))
            if not access_token:
                return None
            
            return {
                'platform': encrypted_data.get('platform'),
                'user_info': encrypted_data.get('user_info'),
                'access_token': access_token,
                'token_type': encrypted_data.get('token_type'),
                'expires_at': encrypted_data.get('expires_at'),
                'created_at': encrypted_data.get('created_at'),
                'last_used': encrypted_data.get('last_used')
            }
        except Exception as e:
            print(f"Error retrieving {platform} account: {e}")
            return None
    
    def delete_account(self, user_id, platform, tenant_id=None):
        try:
            file_path = self._account_path(user_id, platform, tenant_id)
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting {platform} account: {e}")
            return False
    
    def list_accounts(self, user_id, tenant_id=None):
        try:
            user_dir = self._tenant_dir(tenant_id) / str(user_id)
            if not user_dir.exists():
                return []
            
            accounts = []
            for account_file in user_dir.glob('*_account.json'):
                platform = account_file.stem.replace('_account', '')
                account = self.get_account(user_id, platform, tenant_id=tenant_id)
                if account:
                    accounts.append({
                        'platform': platform,
                        'user_info': account.get('user_info'),
                        'connected_at': account.get('created_at'),
                        'last_used': account.get('last_used')
                    })
            
            return accounts
        except Exception as e:
            print(f"Error listing accounts: {e}")
            return []
    
    def update_last_used(self, user_id, platform, tenant_id=None):
        try:
            account = self.get_account(user_id, platform, tenant_id=tenant_id)
            if account:
                account['last_used'] = datetime.utcnow().isoformat()
                self.save_account(user_id, platform, account, tenant_id=tenant_id)
                return True
        except Exception as e:
            print(f"Error updating last_used: {e}")
        return False

def get_social_account_manager():
    return SocialAccountManager()
