"""
Info-Bharat — Scheme Seed Script
Seeds the 6 prototype schemes into Amazon DynamoDB.

Usage:
    python seed_schemes.py --region ap-south-1
    python seed_schemes.py --local  (uses DynamoDB Local at localhost:8000)
"""

import json
import boto3
import argparse
from decimal import Decimal


SCHEMES = [
    {
        "scheme_id": "PMAY_GRAMIN",
        "scheme_name": "PM Awas Yojana (Gramin)",
        "ministry": "Ministry of Rural Development",
        "scheme_type": "central",
        "available_states": ["all"],
        "eligibility_rules": {
            "max_annual_income": Decimal("200000"),
            "eligible_categories": ["SC", "ST", "OBC", "GENERAL"],
            "requires_aadhaar": True,
            "requires_bpl": False,
            "housing_condition": "kutcha_house",  # Must not own pucca house
        },
        "application_url": "pmayg.nic.in",
        "helpline": "1800-11-6446",
        "documents_required": [
            "Aadhaar card",
            "Bank account details",
            "Income certificate",
            "Caste certificate (if applicable)",
            "Photo of existing house",
        ],
        "benefit": "₹1.20 lakh for plain areas, ₹1.30 lakh for hilly/difficult areas",
    },
    {
        "scheme_id": "PM_KISAN",
        "scheme_name": "PM Kisan Samman Nidhi",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "scheme_type": "central",
        "available_states": ["all"],
        "eligibility_rules": {
            "eligible_categories": ["ALL"],
            "requires_aadhaar": True,
            "land_holding_max": Decimal("9999"),  # No upper limit for farmers
            "requires_land_record": True,
            "excluded_categories": [
                "institutional_landholders",
                "government_employees",
                "income_taxpayers",
                "professionals",  # Doctors, lawyers, engineers, etc.
            ],
        },
        "application_url": "pmkisan.gov.in",
        "helpline": "155261",
        "documents_required": [
            "Aadhaar card linked to bank account",
            "Land ownership records (Khasra/Khatauni)",
            "Bank account passbook",
        ],
        "benefit": "₹6,000 per year in 3 instalments of ₹2,000",
    },
    {
        "scheme_id": "AYUSHMAN_BHARAT_PMJAY",
        "scheme_name": "Ayushman Bharat PM-JAY",
        "ministry": "Ministry of Health & Family Welfare",
        "scheme_type": "central",
        "available_states": ["all"],  # Note: Some states have opted out
        "eligibility_rules": {
            "eligible_categories": ["ALL"],
            "requires_aadhaar": False,  # SECC 2011 data used
            "secc_listed": True,        # Must be in SECC 2011 database
            "max_annual_income": Decimal("500000"),
        },
        "application_url": "beneficiary.nha.gov.in",
        "helpline": "14555",
        "documents_required": [
            "Aadhaar card or Ration card",
            "SECC 2011 listing verification",
        ],
        "benefit": "Health cover of ₹5 lakh per family per year",
    },
    {
        "scheme_id": "NSP_SCHOLARSHIP",
        "scheme_name": "National Scholarship Portal — Pre/Post Matric",
        "ministry": "Ministry of Education",
        "scheme_type": "central",
        "available_states": ["all"],
        "eligibility_rules": {
            "max_annual_income": Decimal("250000"),
            "eligible_categories": ["SC", "ST", "OBC", "MINORITY"],
            "requires_aadhaar": True,
            "min_age": Decimal("14"),
            "max_age": Decimal("35"),
            "requires_enrollment": True,  # Must be enrolled in school/college
        },
        "application_url": "scholarships.gov.in",
        "helpline": "0120-6619540",
        "documents_required": [
            "Aadhaar card",
            "Income certificate (from tehsildar)",
            "Previous year mark sheet",
            "Current enrollment certificate",
            "Bank account (in student's name)",
            "Caste certificate",
        ],
        "benefit": "₹1,000–₹20,000 per year depending on scheme variant",
    },
    {
        "scheme_id": "IGNDPS",
        "scheme_name": "Indira Gandhi National Disability Pension Scheme",
        "ministry": "Ministry of Rural Development",
        "scheme_type": "central",
        "available_states": ["all"],
        "eligibility_rules": {
            "max_annual_income": Decimal("100000"),  # BPL threshold
            "eligible_categories": ["ALL"],
            "requires_aadhaar": True,
            "min_age": Decimal("18"),
            "disability_percent_min": Decimal("80"),  # ≥ 80% disability
            "requires_disability_certificate": True,
        },
        "application_url": "nsap.nic.in",
        "helpline": "1800-111-555",
        "documents_required": [
            "Aadhaar card",
            "Disability certificate (≥80%) from Chief Medical Officer",
            "BPL card or income certificate",
            "Bank account details",
        ],
        "benefit": "₹300 per month (central) + state top-up varies",
    },
    {
        "scheme_id": "PMMVY",
        "scheme_name": "PM Matru Vandana Yojana",
        "ministry": "Ministry of Women & Child Development",
        "scheme_type": "central",
        "available_states": ["all"],
        "eligibility_rules": {
            "eligible_categories": ["ALL"],
            "requires_aadhaar": True,
            "max_annual_income": Decimal("800000"),
            "pregnancy_condition": "first_child_or_second_girl",
            "requires_anc_registration": True,  # Must register at health centre
        },
        "application_url": "wcd.nic.in/pmmvy",
        "helpline": "7998799804",
        "documents_required": [
            "Aadhaar card (mother)",
            "Aadhaar card (husband, if available)",
            "MCP card (Mother & Child Protection)",
            "Bank account in mother's name",
            "Pregnancy registration certificate",
        ],
        "benefit": "₹5,000 in 3 instalments for first living child",
    },
]


def seed(dynamodb_client, table_name: str) -> None:
    table = dynamodb_client.Table(table_name)

    print(f"Seeding {len(SCHEMES)} schemes into {table_name}...")

    for scheme in SCHEMES:
        table.put_item(Item=scheme)
        print(f"  ✓ {scheme['scheme_name']}")

    print(f"\nDone. {len(SCHEMES)} schemes seeded successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Info-Bharat scheme database")
    parser.add_argument("--region", default="ap-south-1")
    parser.add_argument("--local", action="store_true", help="Use DynamoDB Local")
    parser.add_argument("--table", default="info_bharat_schemes")
    args = parser.parse_args()

    if args.local:
        dynamodb = boto3.resource(
            "dynamodb",
            endpoint_url="http://localhost:8000",
            region_name="local",
            aws_access_key_id="fake",
            aws_secret_access_key="fake",
        )
    else:
        dynamodb = boto3.resource("dynamodb", region_name=args.region)

    seed(dynamodb, args.table)
