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

ec2 = session.client("ec2")

report = {
    "generated_at": datetime.utcnow().isoformat(),
    "service": "EC2",
    "instances": []
}

# -----------------------------
# EC2 BACKUP CHECK (Snapshots)
# -----------------------------
snapshots = ec2.describe_snapshots(OwnerIds=["self"])["Snapshots"]
has_snapshots = len(snapshots) > 0

reservations = ec2.describe_instances()["Reservations"]
for r in reservations:
    for i in r["Instances"]:
        report["instances"].append({
            "instance_id": i["InstanceId"],
            "backup_enabled": has_snapshots
        })

# -----------------------------
# OUTPUT
# -----------------------------
with open("ec2_backup_report.json", "w") as f:
    json.dump(report, f, indent=2)

print("[✔] EC2 backup verification completed.")
