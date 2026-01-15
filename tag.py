import os
import sys

from collections        import Counter

from mutagen.easyid3    import EasyID3
from mutagen.id3        import ID3NoHeaderError, ID3
from mutagen.flac       import FLAC
from mutagen.mp4        import MP4
from mutagen.oggvorbis  import OggVorbis
from mutagen.wave       import WAVE

from Tool               import convert_name, AUDIO_EXTENSIONS



###CONSTANTS###
VALID_GENRES = ["Book", "Game", "Kid", "Movie", "Other", "Pop", "Rap", "Rock", "Tango", "Web"]



###METHOD###
def get_audio_tags(file_path: str) -> dict:
    tags = {
        'artist': None,
        'album': None,
        'genre': None
    }

    try:
        ext = os.path.splitext(file_path)[1].lower()
        audio = None

        if ext == '.mp3':
            audio = EasyID3(file_path)
        elif ext == '.flac':
            audio = FLAC(file_path)
        elif ext in ['.m4a', '.mp4']:
            audio = MP4(file_path)
            # MP4 uses different tag names
            tags['artist'] = audio.get('\xa9ART', [None])[0]
            tags['album'] = audio.get('\xa9alb', [None])[0]
            tags['genre'] = audio.get('\xa9gen', [None])[0]
            return tags
        elif ext == '.ogg':
            audio = OggVorbis(file_path)
        elif ext == '.wav':
            audio = WAVE(file_path)

        if audio:
            tags['artist'] = audio.get('artist', [None])[0]
            tags['album'] = audio.get('album', [None])[0]
            tags['genre'] = audio.get('genre', [None])[0]

    except Exception as e:
        print(f"⚠️ Could not read tags from {os.path.basename(file_path)}: {e}")

    return tags



def set_audio_tags(file_path: str, artist: str = None, album: str = None, genre: str = None) -> bool:
    try:
        ext     = os.path.splitext(file_path)[1].lower()
        audio   = None

        if ext == '.mp3':
            try:
                audio = EasyID3(file_path)
            except ID3NoHeaderError:
                # Add ID3 header first
                audio_file = ID3()
                audio_file.save(file_path)
                print(f"      → ID3 header saved, loading EasyID3...")
                # Then load with EasyID3
                audio = EasyID3(file_path)
                print(f"      ✓ New ID3 tags created, audio type: {type(audio)}, audio is None: {audio is None}")
            except Exception as mp3_err:
                print(f"      ⚠️ MP3 error: {type(mp3_err).__name__}: {mp3_err}")
                import traceback
                traceback.print_exc()
                return False

        elif ext == '.flac':
            audio = FLAC(file_path)
        elif ext in ['.m4a', '.mp4']:
            audio = MP4(file_path)
            # MP4 uses different tag names
            if artist:
                audio['\xa9ART'] = [artist]
            if album:
                audio['\xa9alb'] = [album]
            if genre:
                audio['\xa9gen'] = [genre]
            audio.save()
            return True
        elif ext == '.ogg':
            audio = OggVorbis(file_path)
        elif ext == '.wav':
            audio = WAVE(file_path)

        if audio is not None:
            if artist:
                audio['artist'] = artist
            if album:
                audio['album'] = album
            if genre:
                audio['genre'] = genre
            audio.save()
            return True
        else:
            print(f"   ⚠️ Audio object is None for {os.path.basename(file_path)}, ext={ext}")
            return False

    except Exception as e:
        print(f"❌ Error updating tags for {os.path.basename(file_path)}: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

    return False



def find_most_common_tag(files_tags: list, tag_name: str) -> str:
    values = [tags[tag_name] for tags in files_tags if tags.get(tag_name)]

    if not values:
        return None

    # Count occurrences
    counter     = Counter(values)
    most_common = counter.most_common(1)

    return most_common[0][0] if most_common else None



def normalize_genre(genre: str) -> str:
    if not genre:
        return None

    genre_converted = convert_name(genre)

    # Check if it matches any valid genre
    for valid_genre in VALID_GENRES:
        if genre_converted.lower() == valid_genre.lower():
            return valid_genre

    # Try partial match
    for valid_genre in VALID_GENRES:
        if valid_genre.lower() in genre_converted.lower() or genre_converted.lower() in valid_genre.lower():
            return valid_genre

    return None



def process_audio_tags(target_path: str) -> None:
    if not os.path.exists(target_path):
        print(f"❌ Path does not exist: {target_path}")
        return

    if not os.path.isdir(target_path):
        print(f"❌ Path is not a directory: {target_path}")
        return

    # Ask if user wants to force tag updates
    force_update = input("🔄 Do you want to force/redo tags even if tags are already set? (yes/no) [no]: ").strip().lower()
    force_update = force_update in ['yes', 'y']

    # Get all audio files
    audio_files = []

    for item in os.listdir(target_path):
        file_path = os.path.join(target_path, item)

        if os.path.isfile(file_path):
            ext = os.path.splitext(item)[1].lower()

            if ext in AUDIO_EXTENSIONS:
                audio_files.append(file_path)

    if not audio_files:
        print(f"⚠️ No audio files found in: {target_path}")
        return

    print(f"📁 Found {len(audio_files)} audio file(s)")

    # Extract tags from all files
    files_tags = []
    files_to_process = []

    for file_path in audio_files:
        tags = get_audio_tags(file_path)
        files_tags.append(tags)

        # Check if file already has all tags
        has_all_tags = tags['artist'] and tags['album'] and tags['genre']

        if not force_update and has_all_tags:
            print(f"⏭️  {os.path.basename(file_path)}: Already tagged (Artist={tags['artist']}, Album={tags['album']}, Genre={tags['genre']}) - Skipping")
        else:
            files_to_process.append(file_path)
            if not force_update:
                status = "Already tagged" if has_all_tags else "Missing tags"
                print(f"📄 {os.path.basename(file_path)}: Artist={tags['artist']}, Album={tags['album']}, Genre={tags['genre']} [{status}]")
            else:
                print(f"📄 {os.path.basename(file_path)}: Will be retagged")

    # If no files need processing, exit
    if not files_to_process:
        print(f"\n✨ All files already have complete tags. Nothing to do!")
        return

    print(f"\n🔧 {len(files_to_process)} file(s) will be processed")

    # If force update, ask user for tags directly, otherwise find most common tags
    if force_update:
        # Force mode: ask user for all tags
        common_artist = input("🎤 Enter artist name: ").strip()
        common_album = input("💿 Enter album name: ").strip()
        print(f"🎵 Valid genres: {', '.join(VALID_GENRES)}")
        common_genre = input("Enter genre: ").strip()
    else:
        # Normal mode: find most common tags
        common_artist = find_most_common_tag(files_tags, 'artist')
        common_album = find_most_common_tag(files_tags, 'album')
        common_genre = find_most_common_tag(files_tags, 'genre')

        # Prompt user if tags are missing
        if not common_artist:
            common_artist = input("🎤 Artist name not found. Enter artist name: ").strip()

        if not common_album:
            common_album = input("💿 Album name not found. Enter album name: ").strip()

        if not common_genre:
            print(f"🎵 Genre not found. Valid genres: {', '.join(VALID_GENRES)}")
            common_genre = input("Enter genre: ").strip()

    # Normalize tags
    artist_normalized   = convert_name(common_artist) if common_artist else None
    album_normalized    = convert_name(common_album) if common_album else None
    genre_normalized    = normalize_genre(common_genre)

    # Genre is not valid, prompt again
    while common_genre and not genre_normalized:
        print(f"⚠️ Invalid genre '{common_genre}'. Valid genres: {', '.join(VALID_GENRES)}")
        common_genre = input("Enter genre: ").strip()
        genre_normalized = normalize_genre(common_genre)

    # Display what will be applied
    print(f"\n📋 Tags to apply:")
    print(f"   Artist: {artist_normalized}")
    print(f"   Album: {album_normalized}")
    print(f"   Genre: {genre_normalized}")
    print()

    # Update files that need processing
    for file_path in files_to_process:
        filename = os.path.basename(file_path)
        success = set_audio_tags(file_path, artist_normalized, album_normalized, genre_normalized)

        if success:
            print(f"✅ Updated: {filename}")
        else:
            print(f"❌ Failed: {filename}")



###MAIN###
if __name__ == "__main__":
    # Check if path provided as command line argument
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
        print(f"📂 Using path from argument: {target_path}")
    else:
        target_path = input("Enter target directory path: ")

    # Expand user path (handle ~)
    target_path = os.path.expanduser(target_path)

    # Convert to absolute path
    target_path = os.path.abspath(target_path)

    # Process audio tags
    process_audio_tags(target_path)

    print("✨ All done!")
