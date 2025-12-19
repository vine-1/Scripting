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
    print("[!] AWS profile 'default' not found. Falling back to default profile.")
    session = boto3.Session()

iam = session.client("iam")

# -----------------------------
# REPORT STRUCTURE
# -----------------------------
report = {
    "generated_at": datetime.utcnow().isoformat(),
    "iam": {
        "users": [],
        "roles": [],
        "account_summary": {}
    }
}

# -----------------------------
# IAM USERS + POLICIES
# -----------------------------
def collect_iam_users():
    paginator = iam.get_paginator("list_users")

    for page in paginator.paginate():
        for user in page["Users"]:
            user_name = user["UserName"]

            attached_policies = iam.list_attached_user_policies(
                UserName=user_name
            ).get("AttachedPolicies", [])

            inline_policies = iam.list_user_policies(
                UserName=user_name
            ).get("PolicyNames", [])

            # Admin access detection
            is_admin = any(
                p["PolicyName"] == "AdministratorAccess"
                for p in attached_policies
            )

            report["iam"]["users"].append({
                "user_name": user_name,
                "arn": user["Arn"],
                "create_date": user["CreateDate"].isoformat(),
                "admin_access": is_admin,
                "attached_policies": [p["PolicyName"] for p in attached_policies],
                "inline_policies": inline_policies
            })

# -----------------------------
# IAM ROLES + TRUST POLICY
# -----------------------------
def collect_iam_roles():
    paginator = iam.get_paginator("list_roles")

    for page in paginator.paginate():
        for role in page["Roles"]:
            report["iam"]["roles"].append({
                "role_name": role["RoleName"],
                "arn": role["Arn"],
                "create_date": role["CreateDate"].isoformat(),
                "max_session_duration": role.get("MaxSessionDuration"),
                "trusted_entities": role["AssumeRolePolicyDocument"]["Statement"]
            })

# -----------------------------
# IAM ACCOUNT SUMMARY
# -----------------------------
def collect_account_summary():
    summary = iam.get_account_summary()["SummaryMap"]
    report["iam"]["account_summary"] = summary

# -----------------------------
# EXECUTION
# -----------------------------
print("[+] Collecting IAM users and policies...")
collect_iam_users()

print("[+] Collecting IAM roles...")
collect_iam_roles()

print("[+] Collecting IAM account summary...")
collect_account_summary()

# -----------------------------
# SAVE OUTPUT
# -----------------------------
output_file = "iam_report.json"

with open(output_file, "w") as f:
    json.dump(report, f, indent=2)

print(f"[✔] IAM report generated: {output_file}")
