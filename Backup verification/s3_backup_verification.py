import boto3
import json
from datetime import datetime
from botocore.exceptions import ProfileNotFound

# -----------------------------
# SESSION
# -----------------------------
try:
    session = boto3.Session(profile_name="default")
except ProfileNotFound:
    session = boto3.Session()

s3 = session.client("s3")

report = {
    "generated_at": datetime.utcnow().isoformat(),
    "service": "S3",
    "buckets": []
}

# -----------------------------
# S3 BACKUP CHECK (Versioning)
# -----------------------------
buckets = s3.list_buckets()["Buckets"]

for b in buckets:
    try:
        versioning = s3.get_bucket_versioning(Bucket=b["Name"])
        enabled = versioning.get("Status") == "Enabled"
    except:
        enabled = False

    report["buckets"].append({
        "bucket_name": b["Name"],
        "versioning_enabled": enabled
    })

# -----------------------------
# OUTPUT
# -----------------------------
with open("s3_backup_report.json", "w") as f:
    json.dump(report, f, indent=2)

print("[✔] S3 backup verification completed.")
