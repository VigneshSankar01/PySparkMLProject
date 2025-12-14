# AWS Region
AWS_REGION = "us-east-1"

# S3 Bucket Names
RAW_BUCKET = "pysparkmlrag-raw-5fafcccc"
PROCESSED_BUCKET = "pysparkmlrag-processed-5fafcccc"
SCRIPTS_BUCKET = "pysparkmlrag-scripts-5fafcccc"
AIRFLOW_BUCKET = "pysparkmlrag-airflow-5fafcccc"

# S3 Paths
RAW_SEC_FILINGS_PATH = f"s3://{RAW_BUCKET}/sec-filings"
PROCESSED_CLEANED_PATH = f"s3://{PROCESSED_BUCKET}/cleaned"
PROCESSED_CHUNKS_PATH = f"s3://{PROCESSED_BUCKET}/chunks"
PROCESSED_EMBEDDINGS_PATH = f"s3://{PROCESSED_BUCKET}/embeddings"

# SEC Filing Settings
SEC_FILING_TYPES = ["10-K"]
SEC_COMPANIES = [
    "AAPL",   # Apple
    "MSFT",   # Microsoft
    "GOOGL",  # Alphabet
    "NVDA",   # NVIDIA
    "AMZN",   # Amazon
    "META",   # Meta
    "JPM",    # JPMorgan
    "JNJ",    # Johnson & Johnson
    "XOM",    # ExxonMobil
    "WMT",    # Walmart
]
SEC_FILINGS_PER_COMPANY = 2  # Last 2 years of 10-K filings