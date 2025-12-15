"""
Reads cleaned 10-K text from S3, splits it into overlapping chunks,
and saves the result to the 'chunks' folder in S3.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, explode, monotonically_increasing_id
from pyspark.sql.types import ArrayType, StringType

# --- CONFIG ---
# Your specific bucket name from the terminal output
PROCESSED_BUCKET = "pysparkmlrag-processed-5fafcccc"
INPUT_PATH = f"s3://{PROCESSED_BUCKET}/cleaned/"
OUTPUT_PATH = f"s3://{PROCESSED_BUCKET}/chunks/"

CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks to preserve context

def chunk_text(text):
    """
    Splits long text into overlapping chunks.
    Example: If size=1000 and overlap=200, chunk 2 starts at index 800.
    """
    if not text:
        return []
    
    chunks = []
    total_len = len(text)
    start = 0
    
    while start < total_len:
        end = start + CHUNK_SIZE
        # Get the slice
        chunk = text[start:end]
        
        # Only keep chunks that aren't too tiny (e.g., leftovers < 50 chars)
        if len(chunk) > 50:
            chunks.append(chunk)
            
        # Move forward, subtracting overlap
        start += (CHUNK_SIZE - CHUNK_OVERLAP)
        
    return chunks

def main():
    print("=" * 60)
    print("STARTING CHUNKING JOB")
    print(f"Input: {INPUT_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print("=" * 60)

    # 1. Start Spark
    spark = SparkSession.builder.appName("SEC-Chunking").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # 2. Register UDF (User Defined Function)
    chunk_udf = udf(chunk_text, ArrayType(StringType()))

    # 3. Read Cleaned Data
    # (We read the parquet files we created in Phase 3)
    df = spark.read.parquet(INPUT_PATH)
    print(f"Initial Document Count: {df.count()}")

    # 4. Apply Chunking
    # This transforms 1 row (Document) -> Many rows (Chunks)
    print("Chunking documents...")
    chunked_df = df.withColumn("chunk_list", chunk_udf(col("clean_text")))
    
    # Explode the list so each chunk gets its own row
    exploded_df = chunked_df.select(
        col("ticker"),
        col("source_path"),
        explode(col("chunk_list")).alias("chunk_text")
    )

    # 5. Add unique IDs for each chunk
    final_df = exploded_df.withColumn("chunk_id", monotonically_increasing_id())

    # 6. Write to S3
    print(f"Writing chunks to {OUTPUT_PATH}...")
    final_df.write.mode("overwrite").partitionBy("ticker").parquet(OUTPUT_PATH)

    print("=" * 60)
    print("CHUNKING COMPLETE")
    print("=" * 60)
    spark.stop()

if __name__ == "__main__":
    main()