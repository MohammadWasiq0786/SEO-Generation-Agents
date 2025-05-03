import re
import requests
from urllib.parse import parse_qs, urlparse
import json

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats."""
    if not url:
        return None
    
    # Clean the URL
    url = url.strip()
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Different YouTube URL patterns
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/e\/|youtube\.com\/watch\?.*v=|youtube\.com\/watch\?.*&v=)([^&?#]+)',
        r'youtube\.com\/shorts\/([^&?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        

    # If all patterns fail, try parsing the URL directly
    parsed_url = urlparse(url)
    if 'youtube.com' in parsed_url.netloc:
        if 'watch' in parsed_url.path:
            query = parse_qs(parsed_url.query)
            if 'v' in query:
                return query['v'][0]
        elif '/shorts/' in parsed_url.path:
            path_parts = parsed_url.path.split('/')
            for i, part in enumerate(path_parts):
                if part == 'shorts' and i+1 < len(path_parts):
                    return path_parts[i+1]
                    
    return None


def get_video_platform(url):
    """Determine the platform from the URL."""
    if not url:
        return "Unknown"
        
    # Normalize the URL
    url = url.strip().lower()
    
    if "youtube.com" in url or "youtu.be" in url:
        return "YouTube"
    elif "instagram.com" in url:
        return "Instagram"
    elif "linkedin.com" in url:
        return "LinkedIn"
    elif "facebook.com" in url or "fb.com" in url:
        return "Facebook"
    elif "tiktok.com" in url:
        return "TikTok"
    elif "twitter.com" in url or "x.com" in url:
        return "Twitter"
    else:
        return "Unknown"
    


def get_youtube_metadata(video_id):
    """Get metadata for a YouTube video with fallback mechanisms."""
    
    # Fallback with basic info that will always work
    basic_metadata = {
        "title": f"YouTube Video ({video_id})",
        "description": "",
        "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
        "duration": 300,  # Default 5 minutes
        "views": 0,
        "author": "YouTube Creator",
        "platform": "YouTube",
        "video_id": video_id
    }

    # Try multiple methods to get the most information
    try:
        # Method 1: Try direct page HTML scraping
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            html_content = response.text
            
            # Extract title
            title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html_content)
            if title_match:
                basic_metadata["title"] = title_match.group(1)
                
            # Extract author/channel
            author_match = re.search(r'<link itemprop="name" content="([^"]+)"', html_content)
            if author_match:
                basic_metadata["author"] = author_match.group(1)
                
            # Try to extract description
            description_match = re.search(r'<meta property="og:description" content="([^"]+)"', html_content)
            if description_match:
                basic_metadata["description"] = description_match.group(1)
            
            # Try to extract duration
            duration_match = re.search(r'"lengthSeconds":"(\d+)"', html_content)
            if duration_match:
                try:
                    basic_metadata["duration"] = int(duration_match.group(1))
                except ValueError:
                    pass  # Use default duration
            
            # Try to extract view count
            views_match = re.search(r'"viewCount":"(\d+)"', html_content)
            if views_match:
                try:
                    basic_metadata["views"] = int(views_match.group(1))
                except ValueError:
                    pass  # Use default views
            
            # Extract higher quality thumbnail if available
            thumbnail_match = re.search(r'<meta property="og:image" content="([^"]+)"', html_content)
            if thumbnail_match:
                basic_metadata["thumbnail_url"] = thumbnail_match.group(1)

        # Method 2: Try to get more info from oEmbed API
        try:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            oembed_response = requests.get(oembed_url)
            
            if oembed_response.status_code == 200:
                oembed_data = oembed_response.json()
                
                # Update metadata with oembed data
                if 'title' in oembed_data and oembed_data['title']:
                    basic_metadata["title"] = oembed_data['title']
                
                if 'author_name' in oembed_data and oembed_data['author_name']:
                    basic_metadata["author"] = oembed_data['author_name']
                
                if 'thumbnail_url' in oembed_data and oembed_data['thumbnail_url']:
                    # Only update if it's higher quality
                    if 'maxresdefault' in oembed_data['thumbnail_url']:
                        basic_metadata["thumbnail_url"] = oembed_data['thumbnail_url']
        except:
            # Ignore any errors with this optional step
            pass
            
    except Exception as e:
        print(f"Error extracting YouTube metadata: {e}")
        # If there's any error, just use the basic metadata
        pass
        
    return basic_metadata


def get_video_metadata(url):
    """Get video metadata based on the platform."""
    if not url:
        raise ValueError("Please enter a video URL")
    
    # Determine platform
    platform = get_video_platform(url)
    
    # Currently we only support full metadata extraction for YouTube
    if platform == "YouTube":
        # Extract video ID from URL
        video_id = extract_video_id(url)
        
        if not video_id:
            raise ValueError("Could not extract video ID from URL. Please use a standard YouTube URL.")
        
        return get_youtube_metadata(video_id)
    else:
        # For other platforms, just return basic info
        return {
            "title": "Video on " + platform,
            "description": "",
            "thumbnail_url": "https://via.placeholder.com/1280x720.png?text=" + platform,
            "duration": 300,  # Default 5 minutes
            "views": 0,
            "author": platform + " Creator",
            "platform": platform,
            "video_id": "unknown"
        }