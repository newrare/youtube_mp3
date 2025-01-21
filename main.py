import os
import re
import time
import yt_dlp
import unicodedata



###METHOD###
def convert_name(name_to_convert: str) -> str:
    # replace special characters
    name_converted = unicodedata.normalize('NFKD', name_to_convert).encode('ASCII', 'ignore').decode('utf-8')
    return re.sub(r'[^0-9a-zA-Z-]+', ' ', name_converted).title().strip()



def download_audio_from_video(video_url, playlist_title = None):
    # Get (or create) download directory
    user_home_directory = os.path.expanduser('~')
    directory_download  = f"{user_home_directory}/download/"
    file_temp           = os.path.join(directory_download, 'temp')

    # Format for download
    ydl_opts = {
        'format'    : 'bestaudio/best',
        'outtmpl'   : file_temp,
        'postprocessors': [{
            'key'               : 'FFmpegExtractAudio',
            'preferredcodec'    : 'mp3',
            'preferredquality'  : '192',
        }],
    }

    # Download and get file name converted
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        video           = ydl.extract_info(video_url, download = True) # Download the video to directory_file_origin and get Object video
        title           = video.get('title', '')
        title_converted = convert_name(title)
        file            = f"{title_converted}.mp3"

    # After Download, rename origin file to name convertedw
    if(playlist_title):
        directory_to_save = f"{directory_download}{playlist_title}/"

        if not os.path.exists(directory_to_save):
            os.makedirs(directory_to_save)

    file_temp = f"{file_temp}.mp3"
    os.rename(file_temp, os.path.join(directory_to_save, file))



def youtube_audio():
    url = input("Enter a YouTube URL: ")

    # Check if the URL is valid (Youtube)
    if "youtube.com" not in url and "youtu.be" not in url:
        print("Invalid YouTube URL")
        return

    if "playlist" in url:
        # download a playlist files
        ydl_opts = {
            'extract_flat'  : True,
            'skip_download' : True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_dict   = ydl.extract_info(url, download=False)
            playlist_title  = convert_name(playlist_dict.get('title', ''))

            #parse the playlist and download each video
            for entry in playlist_dict['entries']:
                video_url = entry['url']

                download_audio_from_video(video_url, playlist_title)

                #time.sleep(2) # Wait for 2 seconds between each download
    else:
        # download a standalone file
        download_audio_from_video(url)



###MAIN###
if __name__ == "__main__":
    youtube_audio()
