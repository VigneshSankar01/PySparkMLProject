import boto3

REGION = "us-east-1"
CLUSTER_NAME = "pysparkmlrag-embedding-debug"
SCRIPTS_BUCKET = "pysparkmlrag-scripts-5fafcccc"
LOGS_BUCKET = "pysparkmlrag-scripts-5fafcccc"
SCRIPT_S3_PATH = f"s3://{SCRIPTS_BUCKET}/pyspark/spark_generate_embeddings.py"

def launch_cluster():
    emr = boto3.client("emr", region_name=REGION)
    print(f"Launching Single-Node Debug Cluster...")

    response = emr.run_job_flow(
        Name=CLUSTER_NAME,
        ReleaseLabel="emr-6.15.0",
        Applications=[{"Name": "Spark"}],
        Instances={
            # SINGLE NODE MODE (Master Only)
            "InstanceGroups": [
                {
                    "Name": "Master",
                    "Market": "ON_DEMAND",
                    "InstanceRole": "MASTER",
                    "InstanceType": "m5.xlarge",
                    "InstanceCount": 1, 
                }
            ],
            "KeepJobFlowAliveWhenNoSteps": False,
            "TerminationProtected": False,
        },
        BootstrapActions=[
            {
                "Name": "Install Dependencies",
                "ScriptBootstrapAction": {
                    "Path": f"s3://{SCRIPTS_BUCKET}/bootstrap_emr.sh"
                },
            }
        ],
        Steps=[
            {
                "Name": "Generate Embeddings",
                "ActionOnFailure": "TERMINATE_CLUSTER",
                "HadoopJarStep": {
                    "Jar": "command-runner.jar",
                    "Args": ["spark-submit", "--deploy-mode", "cluster", SCRIPT_S3_PATH],
                },
            }
        ],
        LogUri=f"s3://{LOGS_BUCKET}/emr-logs/",
        ServiceRole="pysparkmlrag-emr-service-role",
        JobFlowRole="pysparkmlrag-emr-ec2-profile",
        VisibleToAllUsers=True,
    )
    return response["JobFlowId"]

if __name__ == "__main__":
    print(f"Cluster launched! ID: {launch_cluster()}")