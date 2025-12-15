import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import ArrayType, FloatType
import pandas as pd
from sentence_transformers import SentenceTransformer

# Standard Cache Paths
os.environ['HF_HOME'] = '/tmp/hf_cache'
os.environ['TORCH_HOME'] = '/tmp/torch_cache'
os.environ['SENTENCE_TRANSFORMERS_HOME'] = '/tmp/st_cache'

PROCESSED_BUCKET = "pysparkmlrag-processed-5fafcccc"
INPUT_PATH = f"s3://{PROCESSED_BUCKET}/chunks/"
OUTPUT_PATH = f"s3://{PROCESSED_BUCKET}/embeddings/"
MODEL_NAME = 'all-MiniLM-L6-v2' 

model = None

def get_model():
    global model
    if model is None:
        print(f"Loading model: {MODEL_NAME}...")
        model = SentenceTransformer(MODEL_NAME, device='cpu')
    return model

@pandas_udf(ArrayType(FloatType()))
def generate_embeddings(text_series: pd.Series) -> pd.Series:
    local_model = get_model()
    embeddings = local_model.encode(text_series.tolist(), show_progress_bar=False)
    return pd.Series(list(embeddings))

def main():
    spark = SparkSession.builder.appName("SEC-Embeddings").getOrCreate()
    df = spark.read.parquet(INPUT_PATH)
    # Repartition to 8 since we only have 1 node (don't overload it)
    df = df.repartition(8)
    embedding_df = df.withColumn("embedding", generate_embeddings("chunk_text"))
    embedding_df.write.mode("overwrite").partitionBy("ticker").parquet(OUTPUT_PATH)
    spark.stop()

if __name__ == "__main__":
    main()