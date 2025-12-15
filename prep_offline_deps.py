import os
import subprocess
import boto3
import shutil

# --- CONFIG ---
BUCKET_NAME = "pysparkmlrag-scripts-5fafcccc"
S3_WHEEL_PATH = "wheels"  # s3://bucket/wheels/
LOCAL_DIR = "emr_deps"

def main():
    print(f"--- 1. Cleaning old {LOCAL_DIR} ---")
    if os.path.exists(LOCAL_DIR):
        shutil.rmtree(LOCAL_DIR)
    os.makedirs(LOCAL_DIR)

    print(f"--- 2. Downloading Linux Binaries (This may take time) ---")
    # We force pip to download files compatible with EMR (Linux x86_64, Python 3.9)
    packages = [
        "sentence-transformers",
        "pandas",
        "numpy<2.0"
    ]
    
    cmd = [
        "pip", "download",
        "--dest", LOCAL_DIR,
        "--platform", "manylinux2014_x86_64", # Force Linux version
        "--python-version", "3.9",            # EMR 6.15 uses Python 3.9
        "--only-binary=:all:",                # Don't download source code
        "--implementation", "cp",
        "--abi", "cp39"
    ] + packages

    print("Running pip download...")
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        print("!! Download failed. Check internet connection !!")
        return

    print(f"--- 3. Uploading to S3: {BUCKET_NAME}/{S3_WHEEL_PATH}/ ---")
    s3 = boto3.client("s3")
    
    files = os.listdir(LOCAL_DIR)
    total_files = len(files)
    
    for i, filename in enumerate(files):
        local_path = os.path.join(LOCAL_DIR, filename)
        s3_key = f"{S3_WHEEL_PATH}/{filename}"
        print(f"[{i+1}/{total_files}] Uploading {filename}...")
        s3.upload_file(local_path, BUCKET_NAME, s3_key)

    print("\nSUCCESS! All libraries are on S3. You are ready for the Offline Bootstrap.")

if __name__ == "__main__":
    main()