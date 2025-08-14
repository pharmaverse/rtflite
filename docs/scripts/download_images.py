#!/usr/bin/env python3
"""
Download required images from gh-pages branch for documentation build.

This script ensures the required images are available for the documentation
build process. It downloads images from the authoritative gh-pages branch.
"""

import os
import urllib.request


# Configuration
IMAGES_DIR = "docs/articles/images"
BASE_URL = "https://raw.githubusercontent.com/pharmaverse/rtflite/gh-pages/articles/images"
REQUIRED_IMAGES = [
    "age-histogram-treatment-0.png",
    "age-histogram-treatment-1.png", 
    "age-histogram-treatment-2.png"
]


def download_image(url, filepath):
    """Download a single image file."""
    try:
        urllib.request.urlretrieve(url, filepath)
        return True
    except Exception as e:
        print(f"  Error downloading {os.path.basename(filepath)}: {e}")
        return False


def main():
    """Download required images from gh-pages branch."""
    # Ensure images directory exists
    os.makedirs(IMAGES_DIR, exist_ok=True)
    
    print("Downloading images from gh-pages branch...")
    
    success_count = 0
    for img_file in REQUIRED_IMAGES:
        img_path = os.path.join(IMAGES_DIR, img_file)
        
        # Skip if file exists and has reasonable size
        if os.path.exists(img_path) and os.path.getsize(img_path) > 1000:
            print(f"  {img_file}: exists")
            success_count += 1
            continue
        
        # Download the image
        print(f"  {img_file}: downloading...")
        img_url = f"{BASE_URL}/{img_file}"
        
        if download_image(img_url, img_path):
            print(f"  {img_file}: downloaded")
            success_count += 1
        else:
            print(f"  {img_file}: failed")
    
    print(f"Images ready: {success_count}/{len(REQUIRED_IMAGES)}")
    
    # Also ensure RTF directory exists for the build
    os.makedirs("docs/articles/rtf", exist_ok=True)
    
    return 0 if success_count == len(REQUIRED_IMAGES) else 1


if __name__ == "__main__":
    exit(main())