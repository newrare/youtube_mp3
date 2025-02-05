import os



###METHOD###
def rename():
    # Get arguments
    pattern_remove      = input("Enter a string pattern to remove: ")
    directory_target    = input("Enter an absolute target directory: ")
    directory_target    = os.path.expanduser(directory_target)

    # Check target directory
    if not os.path.isdir(directory_target):
        print(f"The directory {directory_target} does not exist!")
        return

    # Parse files in the target directory
    for file in os.listdir(directory_target):
        file_path_origin = os.path.join(directory_target, file)

        print(f"Scanning file: {file_path_origin} ...")

        if file.endswith('.mp3') and pattern_remove in file:
            # Rename file
            file_new        = file.replace(pattern_remove, '').strip()
            file_path_new   = os.path.join(directory_target, file_new)

            os.rename(file_path_origin, file_path_new)
            print(f" -> File renamed: {file_path_new}")
        else:
            print(f" -> File not changed: {file_path_origin}")



###MAIN###
if __name__ == "__main__":
    rename()
