import boto3
import time

# config
REGION = "us-east-1"
CLUSTER_NAME = "pysparkmlrag-text-extraction"

# s3 paths
SCRIPTS_BUCKET = "pysparkmlrag-scripts-5fafcccc"
LOGS_BUCKET = "pysparkmlrag-scripts-5fafcccc"
SCRIPT_PATH = f"s3://{SCRIPTS_BUCKET}/pyspark/spark_extract_text.py"

# IAM roles (from terraform output)
SERVICE_ROLE = "pysparkmlrag-emr-service-role"
INSTANCE_PROFILE = "pysparkmlrag-emr-ec2-profile"


def launch_cluster():
    """Launch EMR cluster with our spark job."""
    
    emr = boto3.client("emr", region_name=REGION)
    
    print("=" * 60)
    print("Launching EMR Cluster")
    print("=" * 60)
    print(f"Script: {SCRIPT_PATH}")
    
    response = emr.run_job_flow(
        Name=CLUSTER_NAME,
        ReleaseLabel="emr-7.0.0",
        
        Applications=[
            {"Name": "Spark"},
        ],
        
        Instances={
            "MasterInstanceType": "m5.2xlarge",
            "SlaveInstanceType": "m5.2xlarge",
            "InstanceCount": 2,  # 1 master + 1 worker
            "KeepJobFlowAliveWhenNoSteps": False,  # auto-terminate when done
        },
        
        Steps=[
            {
                "Name": "Extract Text from SEC Filings",
                "ActionOnFailure": "TERMINATE_CLUSTER",
                "HadoopJarStep": {
                    "Jar": "command-runner.jar",
                    "Args": [
                        "spark-submit",
                        "--deploy-mode", "cluster",
                        "--py-files", f"s3://{SCRIPTS_BUCKET}/pyspark/dependencies.zip",
                        SCRIPT_PATH,
                    ],
                },
            }
        ],
        
        LogUri=f"s3://{LOGS_BUCKET}/emr-logs/",
        
        ServiceRole=SERVICE_ROLE,
        JobFlowRole=INSTANCE_PROFILE,
        
        Configurations=[
            {
                "Classification": "spark-defaults",
                "Properties": {
                    "spark.executor.memory": "8g",
                    "spark.driver.memory": "8g",
                    "spark.executor.memoryOverhead": "2g",
                },
            },
        ],
        
        VisibleToAllUsers=True,
        
        Tags=[
            {"Key": "Project", "Value": "PySparkMLRAG"},
            {"Key": "Environment", "Value": "dev"},
        ],
    )
    
    cluster_id = response["JobFlowId"]
    print(f"\nCluster launched: {cluster_id}")
    
    return cluster_id


def wait_for_cluster(cluster_id):
    """Poll cluster status until it completes or fails."""
    
    emr = boto3.client("emr", region_name=REGION)
    
    print("\nWaiting for cluster to complete...")
    print("(This takes 10-15 minutes - cluster needs to spin up)\n")
    
    while True:
        response = emr.describe_cluster(ClusterId=cluster_id)
        state = response["Cluster"]["Status"]["State"]
        
        print(f"  Status: {state}")
        
        if state in ["TERMINATED", "TERMINATED_WITH_ERRORS"]:
            # check if success or failure
            state_reason = response["Cluster"]["Status"].get("StateChangeReason", {})
            message = state_reason.get("Message", "No message")
            
            if state == "TERMINATED" and "All steps completed" in message:
                print("\n✓ Job completed successfully!")
                return True
            else:
                print(f"\n✗ Job failed: {message}")
                return False
        
        elif state in ["WAITING", "RUNNING"]:
            # check step status
            steps = emr.list_steps(ClusterId=cluster_id)["Steps"]
            if steps:
                step_state = steps[0]["Status"]["State"]
                print(f"  Step:   {step_state}")
        
        time.sleep(30)


def main():
    cluster_id = launch_cluster()
    
    print("\n" + "-" * 60)
    print("You can also monitor in AWS Console:")
    print(f"https://{REGION}.console.aws.amazon.com/emr/home?region={REGION}#/clusterDetails/{cluster_id}")
    print("-" * 60)
    
    success = wait_for_cluster(cluster_id)
    
    if success:
        print("\n" + "=" * 60)
        print("EMR job finished!")
        print("Check processed data: s3://pysparkmlrag-processed-5fafcccc/cleaned/")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("EMR job failed. Check logs in AWS Console.")
        print("=" * 60)


if __name__ == "__main__":
    main()