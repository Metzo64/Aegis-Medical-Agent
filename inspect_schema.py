"""
CLI script to inspect the Supabase PostgreSQL database schema.
Validates table presence and prints discovered columns and types
for all 7 project tables:
  1. users
  2. patients
  3. medical_records
  4. departments
  5. access_requests
  6. rl_decisions
  7. audit_logs
"""

import sys
import json
from config import SUPABASE_URL, REQUIRED_TABLES
from db import test_connection, inspect_schema, get_supabase_client


def main():
    print("=" * 70)
    print("  HOSPITAL ACCESS CONTROL RL - SUPABASE SCHEMA INSPECTION TOOL")
    print("=" * 70)

    if not SUPABASE_URL or "your-project-id" in SUPABASE_URL:
        print("\n[!] WARNING: Supabase credentials are not configured.")
        print("    Please edit the `.env` file and set:")
        print("      SUPABASE_URL=https://your-project.supabase.co")
        print("      SUPABASE_KEY=your-supabase-key")
        print("\n    Once configured, re-run: python inspect_schema.py")
        sys.exit(0)

    print(f"\n[+] Testing connection to: {SUPABASE_URL}")
    client = get_supabase_client()
    if not client:
        print("[-] Could not initialize Supabase client. Please check your credentials in .env.")
        sys.exit(1)

    print("[+] Inspecting database schema dynamically...")
    schema = inspect_schema(force_refresh=True)

    print("\n" + "-" * 70)
    print(f"{'TABLE NAME':<20} | {'STATUS':<10} | {'ROW COUNT':<10} | {'COLUMNS DETECTED'}")
    print("-" * 70)

    for tbl in REQUIRED_TABLES:
        meta = schema.get(tbl, {})
        exists = meta.get("exists", False)
        status_str = "EXISTS" if exists else "NOT FOUND"
        rows = meta.get("sample_row_count", 0)
        cols = meta.get("columns", [])
        col_preview = ", ".join(cols[:5]) + (f" (+{len(cols)-5} more)" if len(cols) > 5 else "") if cols else "(None detected)"

        print(f"{tbl:<20} | {status_str:<10} | {rows:<10} | {col_preview}")

    print("-" * 70)
    print("\nDetailed Column Breakdown:")
    for tbl in REQUIRED_TABLES:
        meta = schema.get(tbl, {})
        if meta.get("exists", False):
            print(f"\nTable [{tbl}]:")
            cols = meta.get("columns", [])
            types = meta.get("column_types", {})
            if not cols:
                print("  No columns or empty table.")
            for col in cols:
                t = types.get(col, "unknown")
                print(f"  - {col} ({t})")

    print("\n[+] Dynamic schema inspection complete. Application will automatically adapt payloads.")
    print("=" * 70)


if __name__ == "__main__":
    main()
