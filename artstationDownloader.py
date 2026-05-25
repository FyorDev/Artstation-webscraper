import os
import sys
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import create_session, RateLimitedSession, BASE_URL

class ArtstationCrawler:
    """Download artwork from Artstation artists."""
    def __init__(self, request_delay=0.05):
        session = create_session()
        self.request = RateLimitedSession(session, request_delay)
    
    def get_projects(self, username, user_id=None):
        """Get all projects for an artist. Paginates until no more pages are returned."""
        projects = []
        page = 1
        
        while True:
            url = f"{BASE_URL}/users/{username}/projects.json"
            params = {'page': page}
            if user_id:
                params['user_id'] = user_id
            
            try:
                print(f"Fetching page {page}...")
                response = self.request.get(url, params=params, timeout=10)
                
                if response.status_code == 403:
                    print("Error: Got 403 Forbidden")
                    print("Request blocked by Cloudflare or access denied.")
                    break
                
                response.raise_for_status()
                data = response.json()
                
                if not data or not data.get('data'):
                    break
                
                projects.extend(data['data'])
                print(f"  Found {len(data.get('data', []))} projects on page {page}")
                
                # continue paginating until server returns no data
                page += 1
            except Exception as e:
                print(f"Error fetching page {page}: {e}")
                break
        
        return projects
    
    def get_project_assets(self, project_id):
        """Get all assets (images) for a project"""
        url = f"{BASE_URL}/projects/{project_id}.json"
        try:
            response = self.request.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('assets', [])
        except Exception as e:
            print(f"Error getting project assets: {e}")
            return []
    
    def download_image(self, image_url, filepath):
        """Download an image from URL"""
        try:
            response = self.request.get(image_url, timeout=10, stream=True)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return True
        except Exception as e:
            print(f"Error downloading {image_url}: {e}")
            return False
    
    def scrape_artist(self, username, output_dir="Downloaded", max_workers=4):
        """Scrape all artwork from an artist using multithreaded downloads."""
        print(f"Scraping artist: {username}")
        artist_dir = os.path.join(output_dir, username)
        artist_path = Path(artist_dir)
        os.makedirs(artist_dir, exist_ok=True)
        
        # Fetch projects
        projects = self.get_projects(username)
        if not projects:
            print("No projects found.")
            if artist_path.exists() and not any(artist_path.iterdir()):
                artist_path.rmdir()
                print(f"[ATYPICAL] Removed empty folder: {artist_dir}")
            return
        
        print(f"Found {len(projects)} projects. Fetching assets...")
        
        # Fetch assets in parallel
        project_assets_map = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(self.get_project_assets, project.get('id')): project for project in projects}
            for idx, future in enumerate(as_completed(futures), 1):
                project = futures[future]
                project_id = project.get('id')
                project_title = re.sub(r'\W+', '_', project.get('title', f"project_{project_id}"))[:50]
                try:
                    project_assets_map[project_id] = (future.result(), project_title)
                    if idx % 10 == 0:
                        print(f"  [{idx}/{len(projects)}] Fetched...")
                except Exception as e:
                    print(f"  [ERROR] {project_title}: {e}")
                    project_assets_map[project_id] = ([], project_title)
        
        print("Asset fetching complete!\n")
        
        # Collect download tasks
        download_tasks = []
        stats = {'videos': 0, 'no_assets': 0, 'existing': 0}
        
        for idx, project in enumerate(projects, 1):
            assets, project_title = project_assets_map.get(project.get('id'), ([], 'unknown'))
            if not assets:
                stats['no_assets'] += 1
                print(f"  [{idx}/{len(projects)}] {project_title}: no assets")
                continue
            
            print(f"  [{idx}/{len(projects)}] {project_title} ({len(assets)} assets)...")
            for asset in assets:
                if asset.get('asset_type') == 'video':
                    stats['videos'] += 1
                    continue
                
                image_url = asset.get('image_url') or asset.get('url')
                if not image_url:
                    continue
                
                filename = os.path.basename(image_url.split('?')[0]) or f"{project_title}_{len(download_tasks)}.jpg"
                filepath = os.path.join(artist_dir, f"{len(download_tasks) + 1}_{filename}")
                
                if not os.path.exists(filepath):
                    download_tasks.append((image_url, filepath, filename))
                else:
                    stats['existing'] += 1
        
        # Download images
        print(f"\nDownloading {len(download_tasks)} images with {max_workers} threads...")
        print(f"  [INFO] Request delay: {self.request.request_delay}s")
        if stats['videos']: print(f"  [INFO] Skipped {stats['videos']} videos")
        if stats['no_assets']: print(f"  [ATYPICAL] {stats['no_assets']} projects had no assets")
        if stats['existing']: print(f"  [INFO] Skipped {stats['existing']} existing files")
        
        downloaded_count, failed_count = 0, 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.download_image, image_url, filepath): filename for image_url, filepath, filename in download_tasks}
            for future in as_completed(futures):
                try:
                    if future.result():
                        downloaded_count += 1
                        print(f"    Downloaded: {futures[future]}")
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    print(f"    [ATYPICAL] Error: {e}")
        
        print(f"\nTotal images downloaded: {downloaded_count}")
        if failed_count: print(f"[ATYPICAL] Failed downloads: {failed_count}")
        
        # Cleanup empty directory
        if artist_path.exists() and not any(artist_path.iterdir()):
            artist_path.rmdir()
            print(f"[ATYPICAL] Removed empty folder: {artist_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        if os.path.exists("links.txt"):
            print("No username provided. Found links.txt - use --batch to process all links.")
        print("Usage: python artstationCrawler.py <username> [--delay SECONDS]")
        print("   or: python artstationCrawler.py --batch [--delay SECONDS]")
        print()
        print("Options:")
        print("  --delay SECONDS    Set request delay (default: 0.05s). Increase for Cloudflare throttling.")
        sys.exit(1)
    
    # Batch mode: download all artists from links.txt
    if sys.argv[1] == "--batch":
        print("Starting batch mode...", flush=True)
        
        if not os.path.exists("links.txt"):
            print("ERROR: links.txt not found! Run: python linkGenerator.py <username>")
            sys.exit(1)
        
        request_delay = 0.05
        if len(sys.argv) >= 4 and sys.argv[2] == "--delay":
            request_delay = float(sys.argv[3])
        
        with open("links.txt") as f:
            links = [line.strip() for line in f if line.strip()]
        
        print(f"\n{'='*60}\nBatch: Processing {len(links)} artists\n{'='*60}\n", flush=True)
        
        crawler = ArtstationCrawler(request_delay=request_delay)
        results = {'successful': 0, 'skipped': 0, 'failed': 0}
        
        for idx, link in enumerate(links, 1):
            username = os.path.basename(link.rstrip('/'))
            artist_dir = os.path.join("Downloaded", username)
            
            if os.path.exists(artist_dir):
                print(f"[{idx}/{len(links)}] Skipping: {username} (done)", flush=True)
                results['skipped'] += 1
            else:
                print(f"[{idx}/{len(links)}] {username}...\n", flush=True)
                try:
                    crawler.scrape_artist(username)
                    results['successful'] += 1
                except Exception as e:
                    print(f"ERROR: {e}\n", flush=True)
                    results['failed'] += 1
        
        print(f"\n{'='*60}\nBatch complete: {results['successful']} successful, "
              f"{results['skipped']} skipped, {results['failed']} failed\n{'='*60}", flush=True)
        sys.exit(0)
    
    # Single artist mode
    username = sys.argv[1]
    request_delay = 0.05  # Default delay
    
    # Parse optional --delay parameter
    if len(sys.argv) >= 4 and sys.argv[2] == "--delay":
        request_delay = float(sys.argv[3])
    
    print(f"Using request delay: {request_delay}s (increase with --delay if throttled by Cloudflare)")
    crawler = ArtstationCrawler(request_delay=request_delay)
    crawler.scrape_artist(username)

