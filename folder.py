import os
import re
import sys

from collections import Counter

from Tool import convert_name, AUDIO_EXTENSIONS



###METHOD###
def detect_common_patterns(items: list, target_path: str) -> list:
    audio_extensions = AUDIO_EXTENSIONS
    filenames = []

    # Collect all audio filenames
    for item in items:
        item_path = os.path.join(target_path, item)
        if os.path.isfile(item_path):
            name, ext = os.path.splitext(item)
            if ext.lower() in audio_extensions:
                filenames.append(name)

    if len(filenames) < 2:
        return []

    patterns = []
    found_prefixes = set()

    # Try to find common prefixes at the start of filenames
    # Check different separator patterns
    separators = [' - ', ' – ', ' — ', ' _ ', ' | ']

    for separator in separators:
        # Collect all potential prefixes (everything before first, second, third occurrence of separator)
        prefix_candidates = []

        for fname in filenames:
            if separator in fname:
                parts = fname.split(separator)
                # Try different prefix lengths
                for i in range(1, len(parts)):
                    prefix = separator.join(parts[:i]) + separator
                    prefix_candidates.append(prefix)

        # Find ALL common prefixes (not just the most common)
        if prefix_candidates:
            prefix_counts = Counter(prefix_candidates)

            # Check each prefix candidate
            for prefix, count in prefix_counts.most_common():
                # Skip if this prefix was already added or is contained in an already added prefix
                if prefix in found_prefixes:
                    continue

                # If at least 3 files start with this prefix (minimum threshold)
                files_starting_with_prefix = sum(1 for f in filenames if f.startswith(prefix))

                if files_starting_with_prefix >= min(3, len(filenames) * 0.3):
                    patterns.append((prefix, 'prefix'))
                    found_prefixes.add(prefix)

    # Sort patterns by length (longest first) to remove longer prefixes first
    patterns.sort(key=lambda x: len(x[0]), reverse=True)

    return patterns



def remove_common_patterns(filename: str, patterns: list) -> str:
    """Remove all common patterns (prefixes) from filename recursively"""
    name, ext = os.path.splitext(filename)

    # Apply all patterns recursively until no more changes
    changed = True
    while changed:
        changed = False
        for pattern, pattern_type in patterns:
            # Remove prefix if it starts with this pattern
            if pattern_type == 'prefix' and name.startswith(pattern):
                name = name[len(pattern):].strip()
                changed = True

    return name + ext



def should_remove_track_numbers(items: list, target_path: str) -> bool:
    audio_files         = []
    files_with_numbers  = 0

    for item in items:
        item_path = os.path.join(target_path, item)

        if os.path.isfile(item_path):
            name, ext = os.path.splitext(item)

            if ext.lower() in AUDIO_EXTENSIONS:
                audio_files.append(name)

                # Check if filename starts with a number followed by separator
                if re.match(r'^\d+[\s\.\-_]+', name):
                    files_with_numbers += 1

    # If no audio files, return False
    if len(audio_files) == 0:
        return False

    # If 70% or more of audio files start with numbers, consider them track numbers
    percentage = (files_with_numbers / len(audio_files)) * 100

    return percentage >= 70



def remove_track_number(filename: str, should_remove: bool) -> str:
    name, ext = os.path.splitext(filename)

    if ext.lower() in AUDIO_EXTENSIONS and should_remove:
        # Remove leading track numbers (e.g., "01 ", "01. ", "1 ", etc.)
        name = re.sub(r'^\d+[\s\.\-_]+', '', name)

        return name + ext

    return filename



def rename_items_in_directory(target_path: str) -> None:
    if not os.path.exists(target_path):
        print(f"❌ Path does not exist: {target_path}")
        return

    if not os.path.isdir(target_path):
        print(f"❌ Path is not a directory: {target_path}")
        return

    print(f"📁 Processing directory: {target_path}")

    # Get all items in directory (files and folders)
    items = []
    try:
        items = os.listdir(target_path)
    except PermissionError:
        print(f"⚠️ Permission denied: {target_path}")
        return

    # First, process subdirectories recursively (depth-first)
    for item in items:
        item_path = os.path.join(target_path, item)

        if os.path.isdir(item_path):
            # Recursively process subdirectory
            rename_items_in_directory(item_path)

    # Then rename items in current directory (after subdirectories are processed)
    items = os.listdir(target_path)

    # Analyze if track numbers should be removed from this directory
    should_remove = should_remove_track_numbers(items, target_path)

    if should_remove:
        print(f"   🔢 Track numbers detected, will remove them")

    # Detect common patterns in filenames
    common_patterns = detect_common_patterns(items, target_path)

    if common_patterns:
        print(f"   🎯 Common patterns detected:")
        for pattern, _ in common_patterns:
            print(f"      - '{pattern}'")

    for item in items:
        old_path = os.path.join(target_path, item)

        # Get name without extension
        name, ext = os.path.splitext(item)

        # Remove common patterns first (before conversion)
        name_cleaned = remove_common_patterns(name + ext, common_patterns)
        name_cleaned_no_ext, ext = os.path.splitext(name_cleaned)

        # Convert name
        new_name = convert_name(name_cleaned_no_ext)

        # Remove track number for audio files (only if analysis determined it's needed)
        new_filename = remove_track_number(new_name + ext, should_remove)

        # Build new path
        new_path = os.path.join(target_path, new_filename)

        # Rename if different
        if old_path != new_path:
            # Check if target already exists
            if os.path.exists(new_path):
                print(f"⚠️ Target already exists, skipping: {item} -> {new_filename}")
            else:
                try:
                    os.rename(old_path, new_path)
                    print(f"✅ Renamed: {item} -> {new_filename}")
                except Exception as e:
                    print(f"❌ Error renaming {item}: {e}")



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

    # Process directory
    rename_items_in_directory(target_path)

    print("✨ All done!")
