import re
import unicodedata



###CONSTANTS###
AUDIO_EXTENSIONS = ['.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg', '.wma', '.opus']



###METHOD###
def convert_name(name_to_convert: str) -> str:
    # Normalize unicode first
    name = unicodedata.normalize('NFKD', name_to_convert)

    # Remove all types of apostrophes (before encoding to ASCII)
    name = re.sub(r"[''\u0027\u2019\u2018`´'']", '', name)

    # Encode to ASCII and convert to lowercase
    name = name.encode('ASCII', 'ignore').decode('utf-8').lower()

    # Replace special characters with spaces
    name = re.sub(r'[^0-9a-zA-Z-]+', ' ', name)

    # No space for contraction (ex: it s -> its, don t -> dont)
    name = re.sub(r'\b(\w+)\s([st])\b', r'\1\2', name)

    # Fix files that already had the 39S encoding error
    name = re.sub(r'\s39s\b', 's', name, flags=re.IGNORECASE)

    # Remove bad space and set Title Case for all words
    name = re.sub(r'\s+', ' ', name).strip().title()

    return name
