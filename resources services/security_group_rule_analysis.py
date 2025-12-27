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
    "control": "Security Group Rule Analysis",
    "findings": []
}

# =====================================================
# SECURITY GROUP RULE ANALYSIS
# =====================================================
def analyze_security_groups():
    security_groups = ec2.describe_security_groups()["SecurityGroups"]

    for sg in security_groups:
        sg_id = sg["GroupId"]
        sg_name = sg.get("GroupName")

        for rule in sg.get("IpPermissions", []):
            from_port = rule.get("FromPort")
            to_port = rule.get("ToPort")
            protocol = rule.get("IpProtocol")

            for ip_range in rule.get("IpRanges", []):
                cidr = ip_range.get("CidrIp")

                if cidr == "0.0.0.0/0":
                    # Ignore HTTP & HTTPS
                    if from_port in (80, 443):
                        continue

                    report["findings"].append({
                        "security_group_id": sg_id,
                        "security_group_name": sg_name,
                        "protocol": protocol,
                        "port_range": f"{from_port}-{to_port}",
                        "cidr": cidr,
                        "risk": "OPEN_TO_WORLD"
                    })

# =====================================================
# EXECUTION
# =====================================================
print("[+] Analyzing security group rules...")
analyze_security_groups()

# =====================================================
# OUTPUT
# =====================================================
with open("security_group_analysis_report.json", "w") as f:
    json.dump(report, f, indent=2)

print("[✔] Security group rule analysis completed.")
print("[✔] Report saved as security_group_analysis_report.json")