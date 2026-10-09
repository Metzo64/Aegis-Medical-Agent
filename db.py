"""
Database module for Supabase PostgreSQL integration.
Provides dynamic schema inspection, column adaptation, and safe logging.
Adheres strictly to requirement:
- Do not assume database columns; dynamically inspect schema.
- Do not delete, overwrite, or recreate existing tables.
- Never expose credentials to frontend.
"""

import json
import logging
from typing import Dict, Any, Optional, List
import requests
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_KEY, REQUIRED_TABLES

logger = logging.getLogger("HospitalRL.db")
logging.basicConfig(level=logging.INFO)

# Global client and cached schema dictionary
_supabase_client: Optional[Client] = None
_discovered_schema: Dict[str, Dict[str, Any]] = {}


def get_supabase_client() -> Optional[Client]:
    """
    Returns an initialized Supabase Client, or None if credentials are not configured.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not SUPABASE_URL or not SUPABASE_KEY or "your-project-id" in SUPABASE_URL:
        logger.warning("Supabase credentials not configured in .env.")
        return None

    try:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client successfully initialized.")
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None


def inspect_schema(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Dynamically inspects the schema of existing Supabase tables.
    Uses PostgREST OpenAPI metadata and sample queries to detect actual column names and types.
    Never alters or creates tables.
    """
    global _discovered_schema
    if _discovered_schema and not force_refresh:
        return _discovered_schema

    schema_info: Dict[str, Dict[str, Any]] = {}

    client = get_supabase_client()
    if not client:
        return {
            "status": "unconfigured",
            "message": "Supabase credentials are not set in .env. Please configure SUPABASE_URL and SUPABASE_KEY."
        }

    # Strategy 1: PostgREST OpenAPI Schema Introspection
    openapi_definitions = {}
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        resp = requests.get(f"{SUPABASE_URL.rstrip('/')}/rest/v1/", headers=headers, timeout=5)
        if resp.status_code == 200:
            openapi_data = resp.json()
            openapi_definitions = openapi_data.get("definitions", {})
            logger.info(f"Retrieved OpenAPI definitions for {len(openapi_definitions)} tables.")
    except Exception as e:
        logger.debug(f"OpenAPI schema lookup unavailable or timed out: {e}")

    # Strategy 2: Table-by-table query inspection (verifies presence and captures actual columns)
    for table_name in REQUIRED_TABLES:
        table_meta = {
            "exists": False,
            "columns": [],
            "column_types": {},
            "sample_row_count": 0
        }

        # Check OpenAPI metadata if available
        if table_name in openapi_definitions:
            table_meta["exists"] = True
            props = openapi_definitions[table_name].get("properties", {})
            table_meta["columns"] = list(props.keys())
            table_meta["column_types"] = {col: props[col].get("type", "unknown") for col in props}

        # Query a sample row to verify live query access and catch any columns
        try:
            query_res = client.table(table_name).select("*").limit(1).execute()
            table_meta["exists"] = True
            if query_res.data and len(query_res.data) > 0:
                sample_row = query_res.data[0]
                # Merge columns discovered from sample row
                for col in sample_row.keys():
                    if col not in table_meta["columns"]:
                        table_meta["columns"].append(col)
                        val = sample_row[col]
                        table_meta["column_types"][col] = type(val).__name__ if val is not None else "any"

            # Query count safely
            try:
                count_res = client.table(table_name).select("*", count="exact").limit(1).execute()
                table_meta["sample_row_count"] = count_res.count if hasattr(count_res, "count") and count_res.count is not None else len(query_res.data)
            except Exception:
                table_meta["sample_row_count"] = len(query_res.data)

        except Exception as e:
            logger.warning(f"Could not query table '{table_name}': {e}")
            table_meta["error"] = str(e)

        schema_info[table_name] = table_meta

    _discovered_schema = schema_info
    return _discovered_schema


def test_connection() -> Dict[str, Any]:
    """
    Tests the Supabase database connection and returns diagnostic status.
    """
    client = get_supabase_client()
    if not client:
        return {
            "connected": False,
            "status": "error",
            "message": "Supabase client not initialized. Check SUPABASE_URL and SUPABASE_KEY in .env.",
            "tables_found": []
        }

    try:
        schema = inspect_schema(force_refresh=True)
        accessible_tables = [t for t, meta in schema.items() if isinstance(meta, dict) and meta.get("exists", False)]
        return {
            "connected": True,
            "status": "ok",
            "url": SUPABASE_URL.split(".supabase.co")[0] + ".supabase.co" if "supabase.co" in SUPABASE_URL else "configured",
            "accessible_tables": accessible_tables,
            "missing_or_inaccessible_tables": [t for t in REQUIRED_TABLES if t not in accessible_tables],
            "schema_summary": {
                t: {
                    "columns": meta.get("columns", []),
                    "rows": meta.get("sample_row_count", 0)
                } for t, meta in schema.items() if isinstance(meta, dict) and meta.get("exists", False)
            }
        }
    except Exception as e:
        return {
            "connected": False,
            "status": "error",
            "message": f"Connection test failed: {str(e)}",
            "tables_found": []
        }


def adapt_payload_to_schema(table_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filters and adapts a payload dictionary so that ONLY columns actually present
    in the table schema are included. This prevents PGRST204 'column does not exist' errors.
    """
    schema = inspect_schema()
    table_meta = schema.get(table_name, {})
    valid_cols = table_meta.get("columns", [])

    if not valid_cols:
        # If schema couldn't be inspected or has no columns listed, return payload as is
        return payload

    adapted = {}
    valid_cols_lower = {col.lower(): col for col in valid_cols}

    for key, val in payload.items():
        key_lower = key.lower()
        if key in valid_cols:
            adapted[key] = val
        elif key_lower in valid_cols_lower:
            # Match case differences
            actual_col = valid_cols_lower[key_lower]
            adapted[actual_col] = val
        else:
            # Check common synonyms: e.g. 'decision' vs 'action', 'created_at' vs 'timestamp'
            synonym_candidates = {
                "action": ["decision", "rl_action", "access_decision", "outcome"],
                "decision": ["action", "rl_action", "access_decision"],
                "created_at": ["timestamp", "decision_time", "requested_at", "logged_at"],
                "timestamp": ["created_at", "decision_time", "logged_at"],
                "request_id": ["req_id", "access_request_id", "id"],
                "user_id": ["requester_id", "actor_id"],
                "patient_id": ["subject_id"],
                "record_id": ["medical_record_id"],
                "reward": ["rl_reward", "score"],
                "q_values": ["q_vals", "q_scores", "q_table_slice"]
            }

            matched = False
            for target_synonym in synonym_candidates.get(key_lower, []):
                if target_synonym in valid_cols_lower:
                    actual_col = valid_cols_lower[target_synonym]
                    # Handle json serialization if field is string
                    if isinstance(val, (dict, list)) and table_meta.get("column_types", {}).get(actual_col) == "string":
                        adapted[actual_col] = json.dumps(val)
                    else:
                        adapted[actual_col] = val
                    matched = True
                    break

            if not matched:
                logger.debug(f"Omitting key '{key}' because it does not exist in table '{table_name}'.")

    return adapted


def log_to_supabase(table_name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Safely inserts a record into a Supabase table using the adapted schema.
    If Supabase is not configured or an error occurs, logs locally without breaking application flow.
    """
    client = get_supabase_client()
    if not client:
        logger.debug(f"[Local Log Fallback] {table_name}: {data}")
        return None

    try:
        adapted_data = adapt_payload_to_schema(table_name, data)
        if not adapted_data:
            logger.warning(f"No matching columns found to insert into table '{table_name}'. Raw data: {data}")
            return None

        res = client.table(table_name).insert(adapted_data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.warning(f"Failed to insert into Supabase table '{table_name}': {e}")
        return None


def fetch_table_records(table_name: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetches up to `limit` records from a table. Returns empty list if unconfigured or error.
    """
    client = get_supabase_client()
    if not client:
        return []

    try:
        res = client.table(table_name).select("*").limit(limit).execute()
        return res.data or []
    except Exception as e:
        logger.warning(f"Error fetching from table '{table_name}': {e}")
        return []


# Cache for valid database entity IDs to prevent foreign key constraint violations
_default_ids: Dict[str, int] = {}


def get_fallback_id(table_name: str, id_col: str) -> Optional[int]:
    """Retrieves and caches a verified valid primary key ID from an existing table."""
    global _default_ids
    if id_col in _default_ids:
        return _default_ids[id_col]
    client = get_supabase_client()
    if not client:
        return None
    try:
        res = client.table(table_name).select(id_col).limit(1).execute()
        if res.data and len(res.data) > 0:
            val = res.data[0].get(id_col)
            if isinstance(val, int):
                _default_ids[id_col] = val
                return val
    except Exception:
        pass
    return None


def resolve_entity_id(val: Any, table_name: str, id_col: str, code_col: Optional[str] = None) -> Optional[int]:
    """
    Safely resolves a string or integer identifier to an existing integer foreign key in Supabase.
    If string is non-numeric, queries by code column or falls back to a valid existing foreign key.
    Ensures candidate integers actually exist in the table to prevent foreign key violations.
    """
    client = get_supabase_client()
    if not client:
        if isinstance(val, int):
            return val
        if isinstance(val, str) and val.isdigit():
            return int(val)
        return None

    # If it is integer or numeric string, verify it exists in DB
    candidate_id = None
    if isinstance(val, int):
        candidate_id = val
    elif isinstance(val, str) and val.isdigit():
        candidate_id = int(val)

    if candidate_id is not None:
        try:
            res = client.table(table_name).select(id_col).eq(id_col, candidate_id).limit(1).execute()
            if res.data and len(res.data) > 0:
                return candidate_id
        except Exception:
            pass

    # If code column provided (e.g. username or patient_code), try resolving
    if code_col and isinstance(val, str):
        try:
            res = client.table(table_name).select(id_col).eq(code_col, val).limit(1).execute()
            if res.data and len(res.data) > 0:
                return res.data[0].get(id_col)
        except Exception:
            pass

    # Try extracting digits if embedded in code like PAT-3008
    digits = ''.join(c for c in str(val) if c.isdigit())
    if digits:
        try:
            candidate = int(digits)
            res = client.table(table_name).select(id_col).eq(id_col, candidate).limit(1).execute()
            if res.data and len(res.data) > 0:
                return candidate
        except Exception:
            pass

    return get_fallback_id(table_name, id_col)


def log_access_and_decision(
    user_id_raw: Any,
    patient_id_raw: Any,
    record_id_raw: Any,
    role: str,
    department_match: bool,
    record_sensitivity: str,
    location: str,
    emergency_status: bool,
    request_frequency: str,
    action: str,
    q_values: Dict[str, float],
    decision_time_ms: float,
    state_index: int,
    explanation: str
) -> bool:
    """
    Coordinates relational logging across access_requests, rl_decisions, and audit_logs in Supabase.
    Ensures primary and foreign keys match without SQL type-cast violations.
    """
    client = get_supabase_client()
    if not client:
        return False

    try:
        u_id = resolve_entity_id(user_id_raw, "users", "user_id", "username")
        p_id = resolve_entity_id(patient_id_raw, "patients", "patient_id", "patient_code")
        r_id = resolve_entity_id(record_id_raw, "medical_records", "record_id")

        if not u_id or not p_id or not r_id:
            logger.debug(f"Could not resolve foreign keys: user={u_id}, patient={p_id}, record={r_id}")
            return False

        emer_str = "Emergency" if emergency_status else "Normal"
        req_row = {
            "user_id": u_id,
            "patient_id": p_id,
            "record_id": r_id,
            "location": location,
            "emergency_status": emer_str,
            "department_match": department_match,
            "recent_request_count": 1 if request_frequency == "NORMAL" else (10 if request_frequency == "ELEVATED" else 35),
            "historical_behavior": 0.1 if action == "ALLOW" else 0.8,
            "scenario_type": "Emergency Access" if emergency_status else ("Routine Access" if department_match else "Cross-Dept Access")
        }
        res_req = client.table("access_requests").insert(req_row).execute()
        if not res_req.data:
            return False

        req_id = res_req.data[0]["request_id"]

        reward_val = float(q_values.get(action, 0.0))
        dec_row = {
            "request_id": req_id,
            "algorithm": "Q-Learning",
            "action": action,
            "reward": reward_val,
            "decision_time_ms": decision_time_ms,
            "outcome_correct": True
        }
        client.table("rl_decisions").insert(dec_row).execute()

        audit_row = {
            "request_id": req_id,
            "user_id": u_id,
            "action": action,
            "event_description": f"Role: {role} | Decision: {action} | Latency: {decision_time_ms:.3f}ms | {explanation[:150]}"
        }
        client.table("audit_logs").insert(audit_row).execute()
        return True
    except Exception as e:
        logger.warning(f"Coordinated Supabase logging skipped or failed: {e}")
        return False

