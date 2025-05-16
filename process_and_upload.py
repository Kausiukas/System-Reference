import os
import shutil
from pathlib import Path

def process_and_upload_file():
    # Source file path
    source_file = "test_data/sample_document.txt"
    
    # Destination directory
    dest_dir = "D:/DATA/uploads"
    
    # Create destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)
    
    # Destination file path
    dest_file = os.path.join(dest_dir, "sample_document.txt")
    
    try:
        # Copy the file to the destination
        shutil.copy2(source_file, dest_file)
        print(f"Successfully uploaded file to: {dest_file}")
        return True
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return False

if __name__ == "__main__":
    process_and_upload_file() 