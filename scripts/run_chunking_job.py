"""
Launches an EMR cluster to run the CHUNKING job.
"""
import boto3
import time

# --- CONFIG ---
REGION = "us-east-1"
CLUSTER_NAME = "pysparkmlrag-chunking-job"
# Bucket for scripts (from your config)
SCRIPTS_BUCKET = "pysparkmlrag-scripts-5fafcccc"
LOGS_BUCKET = "pysparkmlrag-scripts-5fafcccc"

# Path to the script we just made
SCRIPT_S3_PATH = f"s3://{SCRIPTS_BUCKET}/pyspark/spark_chunk_documents.py"

# IAM Roles (created by Vignesh's terraform)
SERVICE_ROLE = "pysparkmlrag-emr-service-role"
INSTANCE_PROFILE = "pysparkmlrag-emr-ec2-profile"

def launch_cluster():
    emr = boto3.client("emr", region_name=REGION)
    
    print(f"Launching EMR Cluster for: {SCRIPT_S3_PATH}")

    response = emr.run_job_flow(
        Name=CLUSTER_NAME,
        ReleaseLabel="emr-7.0.0",
        Applications=[{"Name": "Spark"}],
        Instances={
            "MasterInstanceType": "m5.xlarge", # Chunking is lighter than extraction, xlarge is fine
            "SlaveInstanceType": "m5.xlarge",
            "InstanceCount": 2,
            "KeepJobFlowAliveWhenNoSteps": False,
            "TerminationProtected": False,
        },
        Steps=[
            {
                "Name": "Chunk Documents",
                "ActionOnFailure": "TERMINATE_CLUSTER",
                "HadoopJarStep": {
                    "Jar": "command-runner.jar",
                    "Args": [
                        "spark-submit",
                        "--deploy-mode", "cluster",
                        SCRIPT_S3_PATH
                    ],
                },
            }
        ],
        LogUri=f"s3://{LOGS_BUCKET}/emr-logs/",
        ServiceRole=SERVICE_ROLE,
        JobFlowRole=INSTANCE_PROFILE,
        VisibleToAllUsers=True,
    )
    return response["JobFlowId"]

def main():
    cluster_id = launch_cluster()
    print(f"Cluster launched! ID: {cluster_id}")
    print("Go to AWS Console -> EMR to monitor.")
    print("The cluster will auto-terminate when done.")

if __name__ == "__main__":
    main()