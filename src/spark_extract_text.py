"""
Extracts clean text from SEC 10-K filings using PySpark.

SEC filings are XBRL/XML format, not plain HTML.
This script handles that format properly.
"""

import re
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, input_file_name, regexp_extract, length
from pyspark.sql.types import StringType

# bucket names - hardcoded for EMR
RAW_BUCKET = "pysparkmlrag-raw-5fafcccc"
PROCESSED_BUCKET = "pysparkmlrag-processed-5fafcccc"


def create_spark_session():
    """Spin up Spark session. On EMR, S3 access is pre-configured."""
    spark = SparkSession.builder \
        .appName("SEC-TextExtraction") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    return spark


def clean_sec_filing(content):
    """
    Extract readable text from SEC XBRL/XML filings.
    Uses regex since these aren't standard HTML.
    """
    if not content:
        return None
    
    try:
        # remove XML declarations and processing instructions
        text = re.sub(r'<\?[^>]+\?>', '', content)
        
        # remove XBRL/XML namespace declarations
        text = re.sub(r'xmlns[^=]*="[^"]*"', '', text)
        
        # remove all XML/HTML tags but keep content
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # decode common HTML entities
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&quot;', '"')
        text = text.replace('&#8217;', "'")
        text = text.replace('&#8220;', '"')
        text = text.replace('&#8221;', '"')
        text = text.replace('&#160;', ' ')
        
        # remove remaining numeric entities
        text = re.sub(r'&#\d+;', ' ', text)
        text = re.sub(r'&[a-zA-Z]+;', ' ', text)
        
        # collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # check minimum length
        if len(text) < 5000:
            print(f"Text too short: {len(text)} chars")
            return None
        
        return text
        
    except Exception as e:
        print(f"Error processing: {e}")
        return None


def main():
    print("=" * 60)
    print("SEC Filing Text Extraction")
    print("=" * 60)
    
    input_path = f"s3://{RAW_BUCKET}/sec-filings/"
    output_path = f"s3://{PROCESSED_BUCKET}/cleaned/"
    
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    
    spark = create_spark_session()
    print("Spark session started")
    
    # register UDF
    clean_filing_udf = udf(clean_sec_filing, StringType())
    
    # read all SEC filings
    print("Reading files from S3...")
    raw_df = spark.read.text(
        input_path + "sec-edgar-filings/*/*/*/full-submission.txt",
        wholetext=True
    )
    raw_df = raw_df.withColumn("source_path", input_file_name())
    
    file_count = raw_df.count()
    print(f"Found {file_count} files")
    
    # pull ticker from path
    raw_df = raw_df.withColumn(
        "ticker",
        regexp_extract(col("source_path"), r"sec-edgar-filings/([A-Z]+)/10-K", 1)
    )
    
    # extract text
    print("Extracting text from XBRL/XML...")
    cleaned_df = raw_df.withColumn("clean_text", clean_filing_udf(col("value")))
    
    # show some debug info before filtering
    print("Checking extraction results...")
    cleaned_df.select("ticker", length(col("clean_text")).alias("len")).show(20)
    
    # drop failures
    cleaned_df = cleaned_df.filter(col("clean_text").isNotNull())
    
    # add text length
    cleaned_df = cleaned_df.withColumn("text_length", length(col("clean_text")))
    
    # final columns
    result_df = cleaned_df.select(
        col("ticker"),
        col("source_path"),
        col("clean_text"),
        col("text_length")
    )
    
    success_count = result_df.count()
    print(f"Successfully cleaned {success_count} / {file_count} documents")
    
    if success_count > 0:
        # save as parquet
        print(f"Writing to {output_path}...")
        result_df.write \
            .mode("overwrite") \
            .partitionBy("ticker") \
            .parquet(output_path)
        
        # preview
        print("\nSample:")
        result_df.select("ticker", "text_length").show(10)
    else:
        print("WARNING: No documents were successfully processed!")
    
    spark.stop()
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()