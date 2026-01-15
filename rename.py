import os
import re

from Tool import convert_name



###METHOD###
def rename():
    # Get arguments
    pattern_remove      = input("Enter a string pattern to remove: ")
    directory_target    = input("Enter an absolute target directory: ")
    directory_target    = os.path.expanduser(directory_target)

    # Check target directory
    if not os.path.isdir(directory_target):
        print(f"❌ The directory {directory_target} does not exist!")
        return

    # Parse files in the target directory
    for file in os.listdir(directory_target):
        origin_file = file
        origin_path = os.path.join(directory_target, file)

        # Skip other files
        if not file.lower().endswith('.mp3'):
            continue

        # Remove pattern from file name
        if pattern_remove and pattern_remove in file:
            file = file.replace(pattern_remove, '').strip()

        # Remove leading numbers from file name
        if re.match(r'^[\d#\s-]+', file):
            file = re.sub(r'^[\d#\s-]+', '', file).strip()

        # Remove .mp3 extension temporarily
        file_without_ext = re.sub(r'\.(mp3|MP3|Mp3|mP3)$', '', file, flags=re.IGNORECASE)

        # Apply convert_name transformation
        file = convert_name(file_without_ext) + '.mp3'

        # Save file
        if file != origin_file:
            file_path = os.path.join(directory_target, file)

            os.rename(origin_path, file_path)
            print(f" -> File renamed: {file_path}")



###MAIN###
if __name__ == "__main__":
    rename()
