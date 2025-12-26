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

ec2_global = session.client("ec2")

# Get ALL AWS regions
regions = [r["RegionName"] for r in ec2_global.describe_regions()["Regions"]]

report = {
    "generated_at": datetime.utcnow().isoformat(),
    "service": "EC2",
    "regions_scanned": regions,
    "summary": {
        "total_regions": len(regions),
        "total_instances": 0,
        "instances_with_backup": 0,
        "instances_without_backup": 0
    },
    "region_summary": {},
    "backup_monitoring": []
}

# =====================================================
# LOOP THROUGH ALL REGIONS
# =====================================================
for region in regions:
    ec2 = session.client("ec2", region_name=region)

    report["region_summary"][region] = {
        "instance_count": 0,
        "running": 0,
        "stopped": 0
    }

    # -----------------------------
    # SNAPSHOT CHECK (PAGINATED)
    # -----------------------------
    snapshot_exists = False
    try:
        snap_paginator = ec2.get_paginator("describe_snapshots")
        for snap_page in snap_paginator.paginate(OwnerIds=["self"]):
            if snap_page.get("Snapshots"):
                snapshot_exists = True
                break
    except Exception:
        snapshot_exists = False

    # -----------------------------
    # INSTANCE LISTING (PAGINATED)
    # -----------------------------
    try:
        inst_paginator = ec2.get_paginator("describe_instances")
        for page in inst_paginator.paginate():
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    state = instance["State"]["Name"]

                    report["backup_monitoring"].append({
                        "region": region,
                        "instance_id": instance["InstanceId"],
                        "instance_state": state,
                        "backup_enabled": snapshot_exists
                    })

                    # -------- Update counts
                    report["summary"]["total_instances"] += 1
                    report["region_summary"][region]["instance_count"] += 1

                    if state == "running":
                        report["region_summary"][region]["running"] += 1
                    elif state == "stopped":
                        report["region_summary"][region]["stopped"] += 1

                    if snapshot_exists:
                        report["summary"]["instances_with_backup"] += 1
                    else:
                        report["summary"]["instances_without_backup"] += 1

    except Exception:
        pass  # region may not be enabled / no EC2

# =====================================================
# OUTPUT
# =====================================================
with open("ec2_backup_monitoring_all_regions.json", "w") as f:
    json.dump(report, f, indent=2)

print("[✔] EC2 backup monitoring completed with counts")
