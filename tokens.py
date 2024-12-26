import json
import os
from datetime import datetime

class TokenManager:
    def __init__(self, filename='tokens.json'):
        self.filename = filename
        self.tokens = self._load_tokens()
    
    def _load_tokens(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_tokens(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.tokens, f, ensure_ascii=False, indent=2)
    
    def add_token(self, token, bot_username, creator_id, creator_username):
        token_info = {
            'token': token,
            'bot_username': bot_username,
            'creator_id': creator_id,
            'creator_username': creator_username,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.tokens.append(token_info)
        self._save_tokens()
    
    def get_all_tokens(self):
        return self.tokens
    
    def get_user_tokens(self, creator_id):
        return [t for t in self.tokens if t['creator_id'] == creator_id]
    
    def format_token_info(self, token_info):
        return (f"🤖 Бот: @{token_info['bot_username']}\n"
                f"👤 Создатель: @{token_info['creator_username']}\n"
                f"📅 Дата создания: {token_info['created_at']}") 