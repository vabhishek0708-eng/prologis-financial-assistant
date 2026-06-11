"""
upload_sec_to_s3.py
Uploads SEC mock data and press releases to S3 for cloud integration.
Usage: python upload_sec_to_s3.py
"""
import boto3, json, os

S3_BUCKET  = "prologis-financial-assistant-362612348837"
AWS_REGION = "us-east-2"

s3 = boto3.client("s3", region_name=AWS_REGION)

files = {
    "data/sec_mock.json":        "data/sec_mock.json",
    "data/press_releases.json":  "data/press_releases.json",
}

for local_path, s3_key in files.items():
    if os.path.exists(local_path):
        s3.upload_file(local_path, S3_BUCKET, s3_key)
        print(f"✅ Uploaded {local_path} → s3://{S3_BUCKET}/{s3_key}")
    else:
        print(f"❌ File not found: {local_path}")

print("\nDone! SEC data now served from S3.")
