import boto3

# 1. Increase timeout (for slow connections)
# 2. Trust pypi (for SSL issues)
# 3. Write output to a log file we can read later
script_content = b"""#!/bin/bash
set -e
sudo pip3 install sentence-transformers --default-timeout=1000 --no-cache-dir > /tmp/install_log.txt 2>&1
aws s3 cp /tmp/install_log.txt s3://pysparkmlrag-scripts-5fafcccc/install_logs/bootstrap_log.txt
"""

BUCKET_NAME = "pysparkmlrag-scripts-5fafcccc"
FILE_KEY = "bootstrap_emr.sh"

def upload_binary():
    s3 = boto3.client("s3")
    print(f"Uploading binary bootstrap script to {BUCKET_NAME}/{FILE_KEY}...")
    s3.put_object(Bucket=BUCKET_NAME, Key=FILE_KEY, Body=script_content)
    print("Success! Debug script uploaded.")

if __name__ == "__main__":
    upload_binary()