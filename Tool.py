import re
import unicodedata



###CONSTANTS###
AUDIO_EXTENSIONS = ['.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg', '.wma', '.opus']



###METHOD###
def convert_name(name_to_convert: str) -> str:
    # Remove all types of apostrophes first (before any encoding)
    name = re.sub(r"[''\u0027\u2019\u2018`´'']", '', name_to_convert)

    # Normalize unicode
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower()

    # Replace special characters with spaces
    name = re.sub(r'[^0-9a-zA-Z-]+', ' ', name)

    # No space for contraction (ex: it s -> its, don t -> dont)
    name = re.sub(r'\b(\w+)\s([st])\b', r'\1\2', name)

    # Remove bad space and set Title Case for all words
    name = re.sub(r'\s+', ' ', name).strip().title()

    return name
