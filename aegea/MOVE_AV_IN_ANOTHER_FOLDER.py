import os
import shutil

# Ask the user to input the source and target folder paths
source_folder = input("Enter the path to the source folder: ")
target_folder = input("Enter the path to the target folder: ")

# Create the target folder if it doesn't exist
if not os.path.exists(target_folder):
    os.makedirs(target_folder)

# Use os.walk() to iterate through each folder, subfolders and files
for folderName, subfolders, filenames in os.walk(source_folder):
    for filename in filenames:
        # Check if the filename starts with 'AV_'
        if filename.startswith('AV_'):
            # Construct full file path
            source_file = os.path.join(folderName, filename)
            target_file = os.path.join(target_folder, filename)

            # Move the file
            shutil.move(source_file, target_file)
            print(f'Moved: {filename}')

print('All matching files have been moved.')
