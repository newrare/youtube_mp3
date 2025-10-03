import os
import re
import sys
import time
import unicodedata
import yt_dlp
import requests
#from urllib.parse import urlparse



###METHOD###
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
    # Replace special characters
    name_converted = unicodedata.normalize('NFKD', name_to_convert).encode('ASCII', 'ignore').decode('utf-8')
    return re.sub(r'[^0-9a-zA-Z-]+', ' ', name_converted).title().strip()



def clean_file_temp(file_temp: str) -> bool:
    temp_files = [file_temp, f"{file_temp}.mp3", f"{file_temp}.webm", f"{file_temp}.m4a"]

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            print(f"🗑️  Removing temporary file: {os.path.basename(temp_file)}")
            os.remove(temp_file)

    return True



def download_audio_from_video(video_url, playlist_title = None, is_need_sleep = True) -> bool:
    # Get (or create) download directory
    user_home_directory = os.path.expanduser('~')
    directory_download  = f"{user_home_directory}/download/"
    file_temp           = os.path.join(directory_download, 'temp')

    # Format for download
    ydl_opts = {
        'outtmpl'       : file_temp,
        'ignoreerrors'  : False,
        'no_warnings'   : True,
        'extractaudio'  : True,
        'quiet'         : True,
        'no_color'      : True,
        'noprogress'    : True,
        'postprocessors': [{
            'key'               : 'FFmpegExtractAudio',
            'preferredcodec'    : 'mp3',
            'preferredquality'  : '192',
        }],
    }

    # Create the downloader
    ydl = yt_dlp.YoutubeDL(ydl_opts)

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

        try:
            ydl.download([video_url])

            if is_need_sleep:
                print(f"⏳ Pausing 5 seconds before next download...")
                time.sleep(5)

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
                is_need_sleep = True

                # no sleep for last loop
                if i == len(playlist_dict['entries']):
                    is_need_sleep = False

                # Downloading
                video_url   = entry['url']
                download_audio_from_video(video_url, playlist_title, is_need_sleep)

    # Single
    else:
        # Download a standalone file
        download_audio_from_video(url)

    print("All done!")
