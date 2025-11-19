import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
import tweepy
import praw
from dotenv import load_dotenv

load_dotenv()

class SocialAutomation:
    def __init__(self):
        self.twitter_api = self._init_twitter()
        self.reddit_api = self._init_reddit()
        self.facebook_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        self.linkedin_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        self.instagram_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        self.tiktok_token = os.getenv('TIKTOK_ACCESS_TOKEN')
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
        
    def _init_twitter(self):
        try:
            api_key = os.getenv('TWITTER_API_KEY')
            api_secret = os.getenv('TWITTER_API_SECRET')
            access_token = os.getenv('TWITTER_ACCESS_TOKEN')
            access_secret = os.getenv('TWITTER_ACCESS_SECRET')
            
            if all([api_key, api_secret, access_token, access_secret]):
                auth = tweepy.OAuthHandler(api_key, api_secret)
                auth.set_access_token(access_token, access_secret)
                return tweepy.API(auth)
        except Exception as e:
            print(f"Twitter init error: {e}")
        return None
    
    def _init_reddit(self):
        try:
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            username = os.getenv('REDDIT_USERNAME')
            password = os.getenv('REDDIT_PASSWORD')
            user_agent = os.getenv('REDDIT_USER_AGENT', 'Kario Socials Bot v1.0')
            
            if all([client_id, client_secret, username, password]):
                return praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    username=username,
                    password=password,
                    user_agent=user_agent
                )
        except Exception as e:
            print(f"Reddit init error: {e}")
        return None
    
    def generate_platform_content(self, title: str, content: str, platform: str, ai_manager) -> str:
        platform_prompts = {
            'twitter': f"Convert this blog post into an engaging Twitter thread (max 280 chars per tweet). Title: {title}\n\nContent: {content[:1000]}",
            'linkedin': f"Create a professional LinkedIn post from this blog. Title: {title}\n\nContent: {content[:1500]}",
            'facebook': f"Create an engaging Facebook post with emojis from this blog. Title: {title}\n\nContent: {content[:1500]}",
            'reddit': f"Create a Reddit post for r/technology or relevant subreddit. Title: {title}\n\nContent: {content[:2000]}",
            'instagram': f"Create an Instagram caption with hashtags from this blog. Title: {title}\n\nContent: {content[:1000]}",
            'discord': f"Create a Discord announcement message from this blog. Title: {title}\n\nContent: {content[:1500]}",
        }
        
        prompt = platform_prompts.get(platform, f"Create a social media post from: {title}\n\n{content[:1000]}")
        
        try:
            if ai_manager:
                generated = ai_manager.generate_content(
                    "You are a social media expert. Create engaging, platform-optimized content.",
                    prompt,
                    'gpt-4o'
                )
                return generated
        except Exception as e:
            print(f"AI generation error: {e}")
        
        return f"{title}\n\n{content[:500]}..."
    
    def publish_to_twitter(self, content: str) -> Dict:
        if not self.twitter_api:
            return {'success': False, 'error': 'Twitter not configured'}
        
        try:
            if len(content) > 280:
                tweets = self._split_into_tweets(content)
                last_tweet = None
                for tweet in tweets:
                    if last_tweet:
                        last_tweet = self.twitter_api.update_status(
                            status=tweet,
                            in_reply_to_status_id=last_tweet.id,
                            auto_populate_reply_metadata=True
                        )
                    else:
                        last_tweet = self.twitter_api.update_status(status=tweet)
                return {'success': True, 'message': f'Published {len(tweets)} tweets'}
            else:
                result = self.twitter_api.update_status(status=content)
                return {'success': True, 'tweet_id': result.id}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def publish_to_linkedin(self, content: str) -> Dict:
        if not self.linkedin_token:
            return {'success': False, 'error': 'LinkedIn not configured'}
        
        try:
            url = 'https://api.linkedin.com/v2/ugcPosts'
            headers = {
                'Authorization': f'Bearer {self.linkedin_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            person_urn = os.getenv('LINKEDIN_PERSON_URN')
            
            payload = {
                'author': person_urn,
                'lifecycleState': 'PUBLISHED',
                'specificContent': {
                    'com.linkedin.ugc.ShareContent': {
                        'shareCommentary': {
                            'text': content
                        },
                        'shareMediaCategory': 'NONE'
                    }
                },
                'visibility': {
                    'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 201:
                return {'success': True, 'post_id': response.json().get('id')}
            else:
                return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def publish_to_facebook(self, content: str) -> Dict:
        if not self.facebook_token:
            return {'success': False, 'error': 'Facebook not configured'}
        
        try:
            page_id = os.getenv('FACEBOOK_PAGE_ID')
            url = f'https://graph.facebook.com/v18.0/{page_id}/feed'
            
            payload = {
                'message': content,
                'access_token': self.facebook_token
            }
            
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                return {'success': True, 'post_id': response.json().get('id')}
            else:
                return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def publish_to_reddit(self, title: str, content: str, subreddit: str = 'test') -> Dict:
        if not self.reddit_api:
            return {'success': False, 'error': 'Reddit not configured'}
        
        try:
            submission = self.reddit_api.subreddit(subreddit).submit(
                title=title,
                selftext=content
            )
            return {'success': True, 'post_url': submission.url}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def publish_to_discord(self, content: str) -> Dict:
        if not self.discord_webhook:
            return {'success': False, 'error': 'Discord webhook not configured'}
        
        try:
            payload = {
                'content': content,
                'username': 'Kario Socials Bot'
            }
            
            response = requests.post(self.discord_webhook, json=payload)
            if response.status_code == 204:
                return {'success': True}
            else:
                return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def publish_to_instagram(self, content: str, image_url: Optional[str] = None) -> Dict:
        if not self.instagram_token:
            return {'success': False, 'error': 'Instagram not configured'}
        
        return {'success': False, 'error': 'Instagram API requires manual approval - use mobile app'}
    
    def publish_to_tiktok(self, content: str) -> Dict:
        if not self.tiktok_token:
            return {'success': False, 'error': 'TikTok not configured'}
        
        return {'success': False, 'error': 'TikTok requires video content - not supported yet'}
    
    def publish_to_platform(self, platform: str, content: str, title: str = '') -> Dict:
        platform_methods = {
            'twitter': lambda: self.publish_to_twitter(content),
            'linkedin': lambda: self.publish_to_linkedin(content),
            'facebook': lambda: self.publish_to_facebook(content),
            'reddit': lambda: self.publish_to_reddit(title, content),
            'discord': lambda: self.publish_to_discord(content),
            'instagram': lambda: self.publish_to_instagram(content),
            'tiktok': lambda: self.publish_to_tiktok(content),
        }
        
        method = platform_methods.get(platform)
        if method:
            return method()
        else:
            return {'success': False, 'error': f'Platform {platform} not supported'}
    
    def publish_to_multiple_platforms(self, platforms: List[str], content: str, title: str = '') -> Dict:
        results = {}
        for platform in platforms:
            results[platform] = self.publish_to_platform(platform, content, title)
        
        successful = sum(1 for r in results.values() if r.get('success'))
        
        return {
            'success': successful > 0,
            'results': results,
            'successful_count': successful,
            'failed_count': len(platforms) - successful
        }
    
    def schedule_post(self, platform: str, content: str, scheduled_time: datetime) -> Dict:
        scheduled_data = {
            'platform': platform,
            'content': content,
            'scheduled_time': scheduled_time.isoformat(),
            'status': 'scheduled'
        }
        
        schedule_file = 'scheduled_posts.json'
        try:
            if os.path.exists(schedule_file):
                with open(schedule_file, 'r') as f:
                    schedules = json.load(f)
            else:
                schedules = []
            
            schedules.append(scheduled_data)
            
            with open(schedule_file, 'w') as f:
                json.dump(schedules, f, indent=2)
            
            return {'success': True, 'scheduled_id': len(schedules) - 1}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _split_into_tweets(self, content: str) -> List[str]:
        words = content.split()
        tweets = []
        current_tweet = ""
        
        for word in words:
            if len(current_tweet) + len(word) + 1 <= 270:
                current_tweet += (word + " ")
            else:
                if current_tweet:
                    tweets.append(current_tweet.strip())
                current_tweet = word + " "
        
        if current_tweet:
            tweets.append(current_tweet.strip())
        
        return tweets
    
    def get_platform_status(self, platform: str) -> Dict:
        status_map = {
            'twitter': bool(self.twitter_api),
            'linkedin': bool(self.linkedin_token),
            'facebook': bool(self.facebook_token),
            'reddit': bool(self.reddit_api),
            'instagram': bool(self.instagram_token),
            'tiktok': bool(self.tiktok_token),
            'discord': bool(self.discord_webhook),
        }
        
        return {
            'platform': platform,
            'connected': status_map.get(platform, False),
            'available': platform in status_map
        }
    
    def get_all_platforms_status(self) -> Dict:
        platforms = ['twitter', 'linkedin', 'facebook', 'reddit', 'instagram', 'tiktok', 'discord']
        return {platform: self.get_platform_status(platform) for platform in platforms}

def get_social_automation():
    return SocialAutomation()
