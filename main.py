import os
import re
import sys
import time
import unicodedata
import yt_dlp
import requests
import subprocess



###METHOD###
def check_ytdlp_version():
    try:
        print("🔍 Checking yt-dlp version...")
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', 'yt-dlp'],
            capture_output=True, text=True, timeout=60
        )

        if "Requirement already satisfied" in result.stdout:
            print("✅ yt-dlp is already up to date")
        elif "Successfully installed" in result.stdout:
            print("🆙 yt-dlp has been updated!")
        else:
            print("⚠️ Could not verify yt-dlp update status")

    except subprocess.TimeoutExpired:
        print("⏰ Update check timed out, continuing with current version...")

    except Exception as e:
        print(f"⚠️ Could not check for yt-dlp updates: {e}")



def get_video_title_from_url(video_url: str) -> str:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(video_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Extract title from <title> tag
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.IGNORECASE)

        if title_match:
            title = title_match.group(1)
            title = re.sub(r'\s*-\s*YouTube\s*$', '', title)

            return title.strip()
        else:
            print("⚠️ Could not extract title from page")
            return "Unknown_Video"

    except Exception as error:
        print(f"❌ Unexpected error extracting title: {str(error)}")
        return "Unknown_Video"



def convert_name(name_to_convert: str) -> str:
    # Normalize unicode
    name = unicodedata.normalize('NFKD', name_to_convert).encode('ASCII', 'ignore').decode('utf-8').lower()

    # Remove apostrophe
    name = re.sub(r"[’']", '', name)

    # Remove ' 39' (artefact from apostrophe conversion or normalization)
    name = re.sub(r' 39', '', name)

    # Replace special caracters
    name = re.sub(r'[^0-9a-zA-Z-]+', ' ', name)

    # No space for contraction (ex: it s -> its, don t -> dont)
    name = re.sub(r'\b(\w+)\s([st])\b', r'\1\2', name)

    # Remove bad space and set Title Case for all words
    name = re.sub(r'\s+', ' ', name).strip().title()

    return name



def clean_file_temp(file_temp: str) -> bool:
    temp_files = [file_temp, f"{file_temp}.mp3", f"{file_temp}.webm", f"{file_temp}.m4a"]

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            print(f"🗑️  Removing temporary file: {os.path.basename(temp_file)}")
            os.remove(temp_file)

    return True



def download_audio_from_video(video_url, playlist_title = None) -> bool:
    # Get (or create) download directory
    user_home_directory = os.path.expanduser('~')
    directory_download  = f"{user_home_directory}/download/"
    file_temp           = os.path.join(directory_download, 'temp')

    # Get video title file
    title           = get_video_title_from_url(video_url)
    title_converted = convert_name(title)
    file            = f"{title_converted}.mp3"

    if title == "Unknown_Video":
        print("❌ Could not determine video title, skipping download!")
        return False

    # Create directory and file name
    directory_to_save = directory_download

    if(playlist_title):
        directory_to_save = f"{directory_download}{playlist_title}/"

        if not os.path.exists(directory_to_save):
            os.makedirs(directory_to_save)

    file_to_save = os.path.join(directory_to_save, file)

    # Download it
    if not os.path.exists(file_to_save):
        print(f"📥 Starting download: {file}")

        # Create the downloader with headers and options
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

        ydl = yt_dlp.YoutubeDL(ydl_opts)

        try:
            ydl.download([video_url])
        except Exception as error_result:
            print(f"❌ Unexpected error: {str(error_result)}")
            time.sleep(5)
            clean_file_temp(file_temp)

            return False

        # Check that temporary file exists and is not empty
        temp_mp3_file = f"{file_temp}.mp3"

        if os.path.exists(temp_mp3_file) and os.path.getsize(temp_mp3_file) > 0:
            # Move tempory file to final file
            os.rename(temp_mp3_file, file_to_save)
            print(f"✅ {file} Downloaded successfully.")
        else:
            # Clean temporary files
            for temp_file in [file_temp, temp_mp3_file]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

            print(f"❌ Bad or temporary file empty!")
            return False

    else:
        print(f"⏭️  File {file} already exists.")

    return True



###MAIN###
if __name__ == "__main__":
    # Check yt-dlp updates (helps with YouTube compatibility)
    check_ytdlp_version()

    # Check if URL provided as command line argument
    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"🔗 Using URL from argument: {url}")
    else:
        url = input("Enter a YouTube URL: ")

    # Check if the URL is valid (Youtube)
    if "youtube.com" not in url and "youtu.be" not in url:
        print("❌ Invalid YouTube URL!")
        print("💡 Usage: python main.py <youtube_url>")
        print("💡 Example: python main.py https://www.youtube.com/watch?v=xxxxx")
        exit()

    # Playlist
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

    # Single
    else:
        # Download a standalone file
        download_audio_from_video(url)

    print("All done!")
