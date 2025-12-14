"""
Downloads SEC 10-K filings and uploads them to S3.

This script pulls annual reports from SEC EDGAR for a list of companies,
saves them locally first, then pushes everything to our raw S3 bucket.
"""

import sys
from pathlib import Path

import boto3
from tqdm import tqdm
from sec_edgar_downloader import Downloader

# add parent dir to path so we can import our config
sys.path.append(str(Path(__file__).parent.parent))
from configs.aws_config import (
    RAW_BUCKET,
    AWS_REGION,
    SEC_COMPANIES,
    SEC_FILING_TYPES,
    SEC_FILINGS_PER_COMPANY,
)


def download_filings(download_dir, email):
    """
    Pull SEC filings from EDGAR and save locally.
    Returns a dict with 'success' and 'failed' lists.
    """
    print("=" * 60)
    print("Downloading SEC 10-K Filings")
    print("=" * 60)
    
    dl = Downloader("PySparkMLRAG", email, download_dir)
    results = {"success": [], "failed": []}
    
    for ticker in tqdm(SEC_COMPANIES, desc="Progress"):
        try:
            for filing_type in SEC_FILING_TYPES:
                dl.get(filing_type, ticker, limit=SEC_FILINGS_PER_COMPANY)
            results["success"].append(ticker)
            print(f"  {ticker} - done")
        except Exception as e:
            results["failed"].append({"ticker": ticker, "error": str(e)})
            print(f"  {ticker} - failed: {e}")
    
    return results


def upload_to_s3(local_dir, bucket, s3_prefix):
    """
    Push all files from local_dir to S3.
    Preserves folder structure under the given prefix.
    """
    print("\n" + "=" * 60)
    print("Uploading to S3")
    print("=" * 60)
    
    s3 = boto3.client("s3", region_name=AWS_REGION)
    local_path = Path(local_dir)
    
    all_files = [f for f in local_path.rglob("*") if f.is_file()]
    uploaded = 0
    
    for fpath in tqdm(all_files, desc="Uploading"):
        # build the s3 key from relative path
        rel_path = fpath.relative_to(local_path)
        s3_key = f"{s3_prefix}/{rel_path}".replace("\\", "/")
        
        try:
            s3.upload_file(str(fpath), bucket, s3_key)
            uploaded += 1
        except Exception as e:
            print(f"  failed to upload {fpath.name}: {e}")
    
    print(f"\nUploaded {uploaded} files to s3://{bucket}/{s3_prefix}/")
    return uploaded


def check_s3_upload(bucket, s3_prefix):
    """Quick sanity check - list some files in S3 to confirm upload worked."""
    print("\n" + "=" * 60)
    print("Checking S3")
    print("=" * 60)
    
    s3 = boto3.client("s3", region_name=AWS_REGION)
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=s3_prefix, MaxKeys=10)
    if "Contents" in resp:
        print(f"Found {len(resp['Contents'])} files (showing up to 10):\n")
        for obj in resp["Contents"]:
            size_kb = obj["Size"] / 1024
            print(f"  {obj['Key']} ({size_kb:.1f} KB)")
    else:
        print("No files found - something went wrong!")


if __name__ == "__main__":
    # local folder to download files to first
    LOCAL_DIR = "./data/sec_filings"
    S3_PREFIX = "sec-filings"
    
    # SEC requires an email for EDGAR access - put yours here
    EMAIL = "iamvigneshsankar@gmail.com"  # <-- change this!
    
    if EMAIL == "your_email@gmail.com":
        print("ERROR: Update the EMAIL variable with your actual email.")
        print("SEC requires this for EDGAR API access.")
        sys.exit(1)
    
    # download from SEC
    print("\n[1/3] Downloading filings from SEC EDGAR...\n")
    results = download_filings(LOCAL_DIR, EMAIL)
    print(f"\nDone: {len(results['success'])} succeeded, {len(results['failed'])} failed")
    
    # upload to s3
    print("\n[2/3] Uploading to S3...\n")
    upload_to_s3(LOCAL_DIR, RAW_BUCKET, S3_PREFIX)
    
    # verify
    print("\n[3/3] Verifying...\n")
    check_s3_upload(RAW_BUCKET, S3_PREFIX)
    
    print("\n" + "=" * 60)
    print("All done!")
    print(f"Files available at: s3://{RAW_BUCKET}/{S3_PREFIX}/")
    print("=" * 60)