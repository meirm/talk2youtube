import requests
from bs4 import BeautifulSoup
import json
import sys
import re

def fetch_youtube_metadata(url):
    headers = {
        'Accept-Language': 'en-US,en;q=0.9',  # This header asks for US English content where available
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    data_json = None
    for script in soup.find_all('script'):
        if 'var ytInitialData =' in script.text:
            data_str = script.text.split('var ytInitialData =')[1].split(';')[0].strip()
            data_json = json.loads(data_str)
            break

    if data_json is None:
        return {}

    contents_path = data_json['contents']['twoColumnWatchNextResults']['results']['results']['contents']
    
    video_info = contents_path[0]['videoPrimaryInfoRenderer']
    video_title = video_info['title']['runs'][0]['text']
    view_count_text = video_info['viewCount']['videoViewCountRenderer']['viewCount']['simpleText']
    
    channel_info = contents_path[1]['videoSecondaryInfoRenderer']
    channel_name = channel_info['owner']['videoOwnerRenderer']['title']['runs'][0]['text']
    channel_url = "https://www.youtube.com" + channel_info['owner']['videoOwnerRenderer']['navigationEndpoint']['commandMetadata']['webCommandMetadata']['url']
    subscriber_count = channel_info['owner']['videoOwnerRenderer'].get('subscriberCountText', {}).get('simpleText', 'N/A')
    
    # Handle the possibility of 'description' not being directly available
    video_description = "N/A"
    if 'attributedDescription' in channel_info and 'content' in channel_info['attributedDescription']:
        video_description = channel_info['attributedDescription']['content']

    metadata = {
        'title': video_title,
        'view_count': view_count_text,
        'channel_name': channel_name,
        'channel_url': channel_url,
        'subscriber_count': subscriber_count,
        'video_description': video_description,
    }

    return metadata


def main(url):
    metadata = fetch_youtube_metadata(url)
    print(json.dumps(metadata, indent=2))

# Example usage
if __name__ == "__main__":
    url = sys.argv[1]  # Accepts URL as a command-line argument
    main(url)
