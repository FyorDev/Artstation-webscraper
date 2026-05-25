import requests
import time

# Artstation base URL for all requests
BASE_URL = "https://www.artstation.com"

def create_session():
    """Create a requests session with proper headers."""
    session = requests.Session()
    # Full User-Agent required for Cloudflare bot detection
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    })
    return session

class RateLimitedSession:
    """Wrapper for session with rate limiting and retry logic."""
    def __init__(self, session, request_delay=0.05):
        self.session = session
        self.request_delay = request_delay
        self.last_request_time = 0
    
    def get(self, url, max_retries=3, **kwargs):
        """Make a GET request with rate limiting and retry logic."""
        # Enforce request delay to avoid throttling
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        
        retry_delay = 1
        for attempt in range(max_retries):
            try:
                self.last_request_time = time.time()
                response = self.session.get(url, **kwargs)
                
                # Retry on Cloudflare throttling (429) or server issues (503)
                if response.status_code not in (429, 503) or attempt == max_retries - 1:
                    return response
                
                print(f"  [Rate Limited] Got {response.status_code}, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2
            except requests.exceptions.ConnectionError as e:
                if attempt == max_retries - 1:
                    raise
                print(f"  [Connection Error] {e}, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2
        
        return response
