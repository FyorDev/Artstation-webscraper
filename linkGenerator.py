import sys
import os
import time
from utils import create_session, BASE_URL

def get_following_list(username):
    """Fetch all artists that a user follows."""
    session = create_session()
    following_list = []
    page = 1
    
    while True:
        url = f"{BASE_URL}/users/{username}/following.json"
        params = {'page': page}
        
        try:
            print(f"Fetching page {page}...")
            response = session.get(url, params=params, timeout=10)
            
            if response.status_code == 403:
                print("Error: Got 403 Forbidden.")
                return following_list
            
            response.raise_for_status()
            data = response.json()
            
            if not data or not data.get('data'):
                print(f"Fetched {page - 1} pages total")
                break
            
            users = data['data']
            following_list.extend(users)
            print(f"  Found {len(users)} users on page {page}")
            
            page += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break
    
    return following_list

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python linkGenerator.py <username>")
        print("\nGenerates a links.txt file with all artists you follow.")
        sys.exit(1)
    
    username = sys.argv[1]
    print(f"Fetching following list for: {username}")
    
    following_users = get_following_list(username)
    if not following_users:
        print("No users found. Check your username.")
        sys.exit(1)
    
    # Build URLs from usernames
    links = [f"{BASE_URL}/{user['username']}" for user in following_users if user.get('username')]
    
    # Write to file
    output_file = os.path.join(os.getcwd(), "links.txt")
    with open(output_file, "w") as f:
        f.write('\n'.join(links) + '\n')
    
    print(f"\nTotal users followed: {len(following_users)}")
    print(f"Wrote {len(links)} links to {output_file}")
    print("Download with: python artstationCrawler.py --batch")
