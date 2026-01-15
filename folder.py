import os
import re
import sys

from collections import Counter

from Tool import convert_name, AUDIO_EXTENSIONS



###METHOD###
def detect_common_patterns(filenames: list) -> list:
    """Detect common prefixes and suffixes in a list of filenames (without path)"""
    # Filter to only audio files and extract names without extension
    names = []
    for item in filenames:
        name, ext = os.path.splitext(item)
        if ext.lower() in AUDIO_EXTENSIONS:
            names.append(name)

    if len(names) < 2:
        return []

    patterns = []
    found_prefixes = set()

    # Try to find common prefixes at the start of filenames
    # Check different separator patterns
    separators = [' - ', ' – ', ' — ', ' _ ', ' | ']

    for separator in separators:
        # Collect all potential prefixes (everything before first, second, third occurrence of separator)
        prefix_candidates = []

        for fname in names:
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
                files_starting_with_prefix = sum(1 for f in names if f.startswith(prefix))

                if files_starting_with_prefix >= min(3, len(names) * 0.3):
                    patterns.append((prefix, 'prefix'))
                    found_prefixes.add(prefix)

    # Try to find common word-based prefixes (e.g., "Aespa " without separator)
    # Split each filename into words and check common starting words
    word_prefix_candidates = []

    for fname in names:
        words = fname.split()
        # Try 1, 2, 3 starting words as potential prefixes
        for num_words in range(1, min(4, len(words))):
            prefix = ' '.join(words[:num_words]) + ' '
            word_prefix_candidates.append(prefix)

    if word_prefix_candidates:
        prefix_counts = Counter(word_prefix_candidates)

        for prefix, count in prefix_counts.most_common():
            # Skip short prefixes (less than 3 chars before space)
            if len(prefix.strip()) < 3:
                continue

            # Skip if already found or is substring of existing prefix
            if prefix in found_prefixes or any(prefix in p for p in found_prefixes):
                continue

            files_starting_with_prefix = sum(1 for f in names if f.startswith(prefix))

            # Need higher threshold for word-based prefixes (70% of files)
            if files_starting_with_prefix >= len(names) * 0.7:
                patterns.append((prefix, 'prefix'))
                found_prefixes.add(prefix)

    # Try to find common suffixes at the end of filenames
    found_suffixes = set()
    suffix_separators = [' - ', ' – ', ' — ', ' | ', ' ']

    for separator in suffix_separators:
        suffix_candidates = []

        for fname in names:
            if separator in fname:
                parts = fname.rsplit(separator, 3)  # Split from right, max 3 times
                # Try different suffix lengths
                for i in range(1, len(parts)):
                    suffix = separator + separator.join(parts[-i:])
                    suffix_candidates.append(suffix)

        if suffix_candidates:
            suffix_counts = Counter(suffix_candidates)

            for suffix, count in suffix_counts.most_common():
                if suffix in found_suffixes:
                    continue

                files_ending_with_suffix = sum(1 for f in names if f.endswith(suffix))

                if files_ending_with_suffix >= min(3, len(names) * 0.3):
                    patterns.append((suffix, 'suffix'))
                    found_suffixes.add(suffix)

    # Sort patterns by length (longest first) to remove longer patterns first
    patterns.sort(key=lambda x: len(x[0]), reverse=True)

    # Remove redundant patterns (patterns that are substrings of longer patterns of same type)
    filtered_patterns = []

    for pattern, ptype in patterns:
        # Check if this pattern is a substring of an already added longer pattern of same type
        is_redundant = False

        for existing_pattern, existing_type in filtered_patterns:
            if ptype == existing_type and pattern in existing_pattern:
                is_redundant = True
                break

        if not is_redundant:
            filtered_patterns.append((pattern, ptype))

    return filtered_patterns



def remove_common_patterns(filename: str, patterns: list) -> str:
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
            # Remove suffix if it ends with this pattern
            elif pattern_type == 'suffix' and name.endswith(pattern):
                name = name[:-len(pattern)].strip()
                changed = True

    return name + ext



def clean_html_39(filename: str) -> str:
    """Remove '39' artifacts from HTML &#39; encoding bug - always applied"""
    name, ext = os.path.splitext(filename)

    if ext.lower() in AUDIO_EXTENSIONS:
        # Remove isolated '39' (the artifact from &#39;)
        # Pattern: word boundary + 39 + word boundary
        name = re.sub(r'\b39\b', '', name)
        # Clean up multiple spaces
        name = re.sub(r'\s+', ' ', name).strip()

        return name + ext

    return filename



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

    # HTML '39' artifacts are always cleaned (from &#39; bug)
    print(f"   🧹 Cleaning HTML '39' artifacts (from &#39;)")

    # Analyze if track numbers should be removed from this directory
    should_remove = should_remove_track_numbers(items, target_path)

    if should_remove:
        print(f"   🔢 Track numbers detected, will remove them")

    # Detect common patterns in filenames (using cleaned names without 39 artifacts)
    # Create a temporary list of cleaned names for pattern detection
    cleaned_items_for_detection = []
    for item in items:
        item_path = os.path.join(target_path, item)
        if os.path.isfile(item_path):
            name, ext = os.path.splitext(item)
            if ext.lower() in AUDIO_EXTENSIONS:
                cleaned_name = clean_html_39(item)
                cleaned_items_for_detection.append(cleaned_name)
            else:
                cleaned_items_for_detection.append(item)
        else:
            cleaned_items_for_detection.append(item)

    common_patterns = detect_common_patterns(cleaned_items_for_detection)

    if common_patterns:
        prefixes = [(p, t) for p, t in common_patterns if t == 'prefix']
        suffixes = [(p, t) for p, t in common_patterns if t == 'suffix']

        if prefixes:
            print(f"   🎯 Common prefixes detected:")
            for pattern, _ in prefixes:
                print(f"      - '{pattern}'")

        if suffixes:
            print(f"   🎯 Common suffixes detected:")
            for pattern, _ in suffixes:
                print(f"      - '{pattern}'")

    for item in items:
        old_path = os.path.join(target_path, item)

        # Get name without extension
        name, ext = os.path.splitext(item)

        # Clean HTML 39 artifacts first
        name_cleaned = clean_html_39(name + ext)

        # Remove common patterns (before conversion)
        name_cleaned = remove_common_patterns(name_cleaned, common_patterns)
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
