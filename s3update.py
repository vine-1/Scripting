import boto3
import json
from datetime import datetime
from botocore.exceptions import ProfileNotFound

# -----------------------------
# SESSION (Global)
# -----------------------------
try:
    session = boto3.Session(profile_name="default")
except ProfileNotFound:
    session = boto3.Session()

s3 = session.client("s3")

report = {
    "generated_at": datetime.utcnow().isoformat(),
    "service": "S3",
    "summary": {
        "total_buckets": 0,
        "versioning_enabled": 0,
        "versioning_disabled": 0
    },
    "region_summary": {},
    "backup_monitoring": []
}

# -----------------------------
# LIST ALL BUCKETS (GLOBAL)
# -----------------------------
buckets = s3.list_buckets()["Buckets"]

for b in buckets:
    bucket_name = b["Name"]

    # -------- Get bucket region
    try:
        location = s3.get_bucket_location(Bucket=bucket_name)
        region = location.get("LocationConstraint")
        if region is None:
            region = "us-east-1"
    except Exception:
        region = "UNKNOWN"

    # Initialize region summary
    if region not in report["region_summary"]:
        report["region_summary"][region] = {
            "bucket_count": 0,
            "versioning_enabled": 0,
            "versioning_disabled": 0
        }

    # -------- Check versioning (backup indicator)
    try:
        versioning = s3.get_bucket_versioning(Bucket=bucket_name)
        versioning_enabled = versioning.get("Status") == "Enabled"
    except Exception:
        versioning_enabled = False

    # -------- Store bucket details
    report["backup_monitoring"].append({
        "bucket_name": bucket_name,
        "region": region,
        "versioning_enabled": versioning_enabled
    })

    # -------- Update counts
    report["summary"]["total_buckets"] += 1
    report["region_summary"][region]["bucket_count"] += 1

    if versioning_enabled:
        report["summary"]["versioning_enabled"] += 1
        report["region_summary"][region]["versioning_enabled"] += 1
    else:
        report["summary"]["versioning_disabled"] += 1
        report["region_summary"][region]["versioning_disabled"] += 1

# -----------------------------
# OUTPUT
# -----------------------------
with open("s3_backup_monitoring_all_regions.json", "w") as f:
    json.dump(report, f, indent=2)

print("[✔] S3 backup monitoring completed with counts (ALL regions)")
