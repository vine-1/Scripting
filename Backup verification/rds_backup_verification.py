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

rds = session.client("rds")

report = {
    "generated_at": datetime.utcnow().isoformat(),
    "service": "RDS",
    "databases": []
}

# -----------------------------
# RDS BACKUP CHECK
# -----------------------------
dbs = rds.describe_db_instances()["DBInstances"]

for db in dbs:
    report["databases"].append({
        "db_instance": db["DBInstanceIdentifier"],
        "backup_retention_days": db["BackupRetentionPeriod"],
        "backup_enabled": db["BackupRetentionPeriod"] > 0
    })

# -----------------------------
# OUTPUT
# -----------------------------
with open("rds_backup_report.json", "w") as f:
    json.dump(report, f, indent=2)

print("[✔] RDS backup verification completed.")
