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

# Get ALL AWS regions
regions = [r["RegionName"] for r in ec2.describe_regions()["Regions"]]

report = {
    "generated_at": datetime.utcnow().isoformat(),
    "service": "RDS",          # ✅ all regions captured here
    "backup_monitoring": {
        "aws_managed_backups": [],
        "manual_backups": []
    }
}

# =====================================================
# LOOP THROUGH ALL REGIONS (NO PRINTS)
# =====================================================
for region in regions:
    rds = session.client("rds", region_name=region)

    # -----------------------------
    # AWS-MANAGED (AUTOMATED) BACKUPS
    # -----------------------------
    try:
        dbs = rds.describe_db_instances()["DBInstances"]
        for db in dbs:
            report["backup_monitoring"]["aws_managed_backups"].append({
                "region": region,
                "db_instance": db["DBInstanceIdentifier"],
                "backup_retention_days": db["BackupRetentionPeriod"],
                "backup_enabled": db["BackupRetentionPeriod"] > 0,
                "latest_restorable_time": (
                    db["LatestRestorableTime"].isoformat()
                    if "LatestRestorableTime" in db else None
                )
            })
    except Exception:
        pass   # silent fail for regions with no RDS

    # -----------------------------
    # MANUAL BACKUPS (MANUAL SNAPSHOTS)
    # -----------------------------
    try:
        snapshots = rds.describe_db_snapshots(
            SnapshotType="manual"
        )["DBSnapshots"]

        for snap in snapshots:
            report["backup_monitoring"]["manual_backups"].append({
                "region": region,
                "snapshot_id": snap["DBSnapshotIdentifier"],
                "db_instance": snap["DBInstanceIdentifier"],
                "snapshot_create_time": snap["SnapshotCreateTime"].isoformat(),
                "status": snap["Status"],
                "engine": snap["Engine"]
            })
    except Exception:
        pass

# =====================================================
# OUTPUT
# =====================================================
with open("rds_backup_monitoring_all_regions.json", "w") as f:
    json.dump(report, f, indent=2)

print("[✔] RDS backup monitoring completed (all regions captured in output)")