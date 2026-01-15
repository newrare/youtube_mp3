import os
import re
import sys
import time
import html
import yt_dlp
import requests
import subprocess

from Tool import convert_name



###METHOD###
def check_ytdlp_version():
    print("🔄 Checking for yt-dlp package updates...")

    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', 'yt-dlp'],
            capture_output=True, text=True, timeout=60
        )

    except subprocess.TimeoutExpired:
        print("⏰ Update check timed out, continuing with current version...")

    except Exception as e:
        print(f"⚠️ Could not check for yt-dlp updates: {e}")



def get_video_title_from_url(video_url: str) -> str:
    try:
        # Set header for simulating a browser visit
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Get request result
        response = requests.get(video_url, headers=headers, timeout=10)

        response.raise_for_status()

        # Extract title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.IGNORECASE)

        if not title_match:
            print("⚠️ Could not extract title from page")
            return False

        title = title_match.group(1)
        title = html.unescape(title)
        title = re.sub(r'\s*-\s*YouTube\s*$', '', title)

        return title.strip()

    except Exception as error:
        print(f"❌ Unexpected error extracting title: {str(error)}")
        return False


def clean_file_temp(file_temp: str) -> bool:
    # Get list of temporary files to remove
    temp_files = [file_temp, f"{file_temp}.mp3", f"{file_temp}.webm", f"{file_temp}.m4a"]

    # Remove temporary files
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    return True



def download_audio_from_video(video_url, playlist_title = None) -> bool:
    # Get (or create) download directory
    user_home_directory = os.path.expanduser('~')
    directory_download  = f"{user_home_directory}/download/"
    file_temp           = os.path.join(directory_download, 'temp')

    # Get and convert title
    title = get_video_title_from_url(video_url)

    if title == False:
        print("❌ Could not determine video title, skipping download!")
        return False

    title_converted = convert_name(title)
    file            = f"{title_converted}.mp3"

    # Create directory and file name
    directory_to_save = directory_download

    if(playlist_title):
        directory_to_save = f"{directory_download}{playlist_title}/"

        if not os.path.exists(directory_to_save):
            os.makedirs(directory_to_save)

    file_to_save = os.path.join(directory_to_save, file)

    # Skip it when file already exists
    if os.path.exists(file_to_save):
        print(f"⏭️  File {file} already exists.")
        return True

    # Create headers and options for yt-dlp
    ydl_headers = {
        'User-Agent'       : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept'           : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language'  : 'en-us,en;q=0.5',
        'Accept-Encoding'  : 'gzip,deflate',
        'Accept-Charset'   : 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
        'Keep-Alive'       : '300',
        'Connection'       : 'keep-alive',
    }

    ydl_opts = {
        'outtmpl'                   : file_temp,
        'http_headers'              : ydl_headers,
        'retry_sleep_functions'     : {'http': lambda x: min(2 ** x, 10)},
        'retries'                   : 3,
        'fragment_retries'          : 3,
        'socket_timeout'            : 30,
        'sleep_interval'            : 1,
        'max_sleep_interval'        : 5,
        'sleep_interval_requests'   : 1,
        'extract_flat'              : False,
        'writethumbnail'            : False,
        'writeinfojson'             : False,
        'ignoreerrors'              : False,
        'logtostderr'               : False,
        'quiet'                     : True,
        'no_warnings'               : True,
        'no_color'                  : True,
        'noprogress'                : True,
        'logger'                    : None,
        'postprocessors'            : [{
            'key'               : 'FFmpegExtractAudio',
            'preferredcodec'    : 'mp3',
            'preferredquality'  : '192',
        }],
    }

    # Download the audio
    print(f"📥 Starting download: {file}")
    ydl = yt_dlp.YoutubeDL(ydl_opts)

    try:
        ydl.download([video_url])

    except Exception as error_result:
        # Wait and clean temporary files when YouTube returns an error
        print(f"❌ Unexpected error: {str(error_result)}")
        time.sleep(5)
        clean_file_temp(file_temp)

        return False

    # Clean temporary file
    temp_mp3_file = f"{file_temp}.mp3"

    if not (os.path.exists(temp_mp3_file) and os.path.getsize(temp_mp3_file) > 0):
        for temp_file in [file_temp, temp_mp3_file]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        print(f"❌ Bad or temporary file empty!")
        return False

    # Move tempory file to final file
    os.rename(temp_mp3_file, file_to_save)
    print(f"✅ {file} Downloaded successfully.")

    return True



###MAIN###
if __name__ == "__main__":
    # Check yt-dlp updates (Youtube compatibility or restrictions)
    check_ytdlp_version()

    # Get URL to use by argument or input
    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"🔗 Using URL from argument: {url}")
    else:
        url = input("Enter a YouTube URL: ")

    # Check if the URL is valid (Youtube)
    if "youtube.com" not in url and "youtu.be" not in url:
        print("❌ Invalid YouTube URL!")
        print("💡 Usage: python main.py <youtube_url>")
        print("💡 Example (argument): python main.py 'https://www.youtube.com/watch?v=xxxxx'")
        print("💡 Example (prompt): python main.py")
        exit()

    # For Playlist
    if "playlist" in url:
        # Options
        ydl_opts = {
            'extract_flat'  : True, # Only extract metadata
            'skip_download' : True, # Not for the moment
            'quiet'         : True, # Suppress most output
            'no_warnings'   : True, # No warnings
            'no_color'      : True, # Remove colors
            'noprogress'    : True, # Remove progress bars
        }

        # Get playlist details and parse it
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_dict   = ydl.extract_info(url, download=False)
            playlist_title  = convert_name(playlist_dict.get('title', ''))

            # Download each video
            for i, entry in enumerate(playlist_dict['entries'], 1):
                video_url = entry['url']

                download_audio_from_video(video_url, playlist_title)

        print("✅ Playlist task terminated!")
        exit()

    # Download a standalone file
    download_audio_from_video(url)
    print("✅ Standalone task terminated!")
