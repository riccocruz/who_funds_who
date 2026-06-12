#!/usr/bin/env python3
"""
fec_loader.py — Load FEC bulk data files into SQLite.

Supported files (accepts .txt or .zip):
  weball26  → all_candidates table
  webk26    → pac_summary table
  ccl       → candidate_committee_linkage table
  itpas2    → contributions table

Usage:
  python fec_loader.py datasets/weball26.txt datasets/ccl.txt
  python fec_loader.py --db fec.db datasets/weball26.zip datasets/itpas2.zip
  python fec_loader.py --db fec.db datasets/          # load a whole directory
"""

import argparse
import csv
import io
import sqlite3
import sys
import zipfile
from pathlib import Path

BATCH_SIZE = 10_000

# ── Schema definitions ────────────────────────────────────────────────────────
# Each entry: table name, ordered (column, sqlite_type) pairs, PK, extra indexes.

SCHEMAS = {
    "weball": {
        "table": "all_candidates",
        "columns": [
            ("cand_id", "TEXT"),
            ("cand_name", "TEXT"),
            ("cand_ici", "TEXT"),
            ("pty_cd", "TEXT"),
            ("cand_pty_affiliation", "TEXT"),
            ("ttl_receipts", "REAL"),
            ("trans_from_auth", "REAL"),
            ("ttl_disb", "REAL"),
            ("trans_to_auth", "REAL"),
            ("coh_bop", "REAL"),
            ("coh_cop", "REAL"),
            ("cand_contrib", "REAL"),
            ("cand_loans", "REAL"),
            ("other_loans", "REAL"),
            ("cand_loan_repay", "REAL"),
            ("other_loan_repay", "REAL"),
            ("debts_owed_by", "REAL"),
            ("ttl_indiv_contrib", "REAL"),
            ("cand_office_st", "TEXT"),
            ("cand_office_district", "TEXT"),
            ("spec_election", "TEXT"),
            ("prim_election", "TEXT"),
            ("run_election", "TEXT"),
            ("gen_election", "TEXT"),
            ("gen_election_precent", "REAL"),
            ("other_pol_cmte_contrib", "REAL"),
            ("pol_pty_contrib", "REAL"),
            ("cvg_end_dt", "TEXT"),
            ("indiv_refunds", "REAL"),
            ("cmte_refunds", "REAL"),
        ],
        "primary_key": "cand_id",
        "indexes": [
            ("idx_weball_party", "cand_pty_affiliation"),
            ("idx_weball_state", "cand_office_st"),
            ("idx_weball_party_state", "cand_pty_affiliation, cand_office_st"),
        ],
    },
    "webk": {
        "table": "pac_summary",
        "columns": [
            ("cmte_id", "TEXT"),
            ("cmte_nm", "TEXT"),
            ("cmte_tp", "TEXT"),
            ("cmte_dsgn", "TEXT"),
            ("cmte_filing_freq", "TEXT"),
            ("ttl_receipts", "REAL"),
            ("trans_from_aff", "REAL"),
            ("indv_contrib", "REAL"),
            ("other_pol_cmte_contrib", "REAL"),
            ("cand_contrib", "REAL"),
            ("cand_loans", "REAL"),
            ("ttl_loans_received", "REAL"),
            ("ttl_disb", "REAL"),
            ("tranf_to_aff", "REAL"),
            ("indv_refunds", "REAL"),
            ("other_pol_cmte_refunds", "REAL"),
            ("cand_loan_repay", "REAL"),
            ("loan_repay", "REAL"),
            ("coh_bop", "REAL"),
            ("coh_cop", "REAL"),
            ("debts_owed_by", "REAL"),
            ("nonfed_trans_received", "REAL"),
            ("contrib_to_other_cmte", "REAL"),
            ("ind_exp", "REAL"),
            ("pty_coord_exp", "REAL"),
            ("nonfed_share_exp", "REAL"),
            ("cvg_end_dt", "TEXT"),
        ],
        "primary_key": "cmte_id",
        "indexes": [
            ("idx_webk_type", "cmte_tp"),
            ("idx_webk_dsgn", "cmte_dsgn"),
        ],
    },
    "ccl": {
        "table": "candidate_committee_linkage",
        "columns": [
            ("cand_id", "TEXT"),
            ("cand_election_yr", "INTEGER"),
            ("fec_election_yr", "INTEGER"),
            ("cmte_id", "TEXT"),
            ("cmte_tp", "TEXT"),
            ("cmte_dsgn", "TEXT"),
            ("linkage_id", "INTEGER"),
        ],
        "primary_key": "linkage_id",
        "indexes": [
            ("idx_ccl_cand_id", "cand_id"),
            ("idx_ccl_cmte_id", "cmte_id"),
            ("idx_ccl_cand_cmte", "cand_id, cmte_id"),
        ],
    },
    "itpas2": {
        "table": "contributions",
        "columns": [
            ("cmte_id", "TEXT"),
            ("amndt_ind", "TEXT"),
            ("rpt_tp", "TEXT"),
            ("transaction_pgi", "TEXT"),
            ("image_num", "TEXT"),
            ("transaction_tp", "TEXT"),
            ("entity_tp", "TEXT"),
            ("name", "TEXT"),
            ("city", "TEXT"),
            ("state", "TEXT"),
            ("zip_code", "TEXT"),
            ("employer", "TEXT"),
            ("occupation", "TEXT"),
            ("transaction_dt", "TEXT"),
            ("transaction_amt", "REAL"),
            ("other_id", "TEXT"),
            ("cand_id", "TEXT"),
            ("tran_id", "TEXT"),
            ("file_num", "INTEGER"),
            ("memo_cd", "TEXT"),
            ("memo_text", "TEXT"),
            ("sub_id", "INTEGER"),
        ],
        "primary_key": "sub_id",
        "indexes": [
            ("idx_itpas2_cmte_id", "cmte_id"),
            ("idx_itpas2_cand_id", "cand_id"),
            ("idx_itpas2_transaction_dt", "transaction_dt"),
            ("idx_itpas2_amt", "transaction_amt"),
            ("idx_itpas2_cand_cmte", "cand_id, cmte_id"),
        ],
    },
    # itoth — any transaction from one committee to another (PAC→party, PAC→PAC, etc.)
    # 21 columns; no CAND_ID — recipient is identified via OTHER_ID (their FEC committee ID).
    "itoth": {
        "table": "committee_transactions",
        "columns": [
            ("cmte_id", "TEXT"),
            ("amndt_ind", "TEXT"),
            ("rpt_tp", "TEXT"),
            ("transaction_pgi", "TEXT"),
            ("image_num", "TEXT"),
            ("transaction_tp", "TEXT"),
            ("entity_tp", "TEXT"),
            ("name", "TEXT"),
            ("city", "TEXT"),
            ("state", "TEXT"),
            ("zip_code", "TEXT"),
            ("employer", "TEXT"),
            ("occupation", "TEXT"),
            ("transaction_dt", "TEXT"),
            ("transaction_amt", "REAL"),
            ("other_id", "TEXT"),
            ("tran_id", "TEXT"),
            ("file_num", "INTEGER"),
            ("memo_cd", "TEXT"),
            ("memo_text", "TEXT"),
            ("sub_id", "INTEGER"),
        ],
        "primary_key": "sub_id",
        "indexes": [
            ("idx_itoth_cmte_id", "cmte_id"),
            ("idx_itoth_other_id", "other_id"),
            ("idx_itoth_transaction_dt", "transaction_dt"),
            ("idx_itoth_amt", "transaction_amt"),
            ("idx_itoth_cmte_other", "cmte_id, other_id"),
        ],
    },
    # indiv — contributions by individuals (>$200); employer/occupation enable
    # bundling analysis (e.g. "donated as AIPAC employee").
    # 21 columns; CMTE_ID is the *receiving* committee.
    "indiv": {
        "table": "individual_contributions",
        "columns": [
            ("cmte_id", "TEXT"),
            ("amndt_ind", "TEXT"),
            ("rpt_tp", "TEXT"),
            ("transaction_pgi", "TEXT"),
            ("image_num", "TEXT"),
            ("transaction_tp", "TEXT"),
            ("entity_tp", "TEXT"),
            ("name", "TEXT"),
            ("city", "TEXT"),
            ("state", "TEXT"),
            ("zip_code", "TEXT"),
            ("employer", "TEXT"),
            ("occupation", "TEXT"),
            ("transaction_dt", "TEXT"),
            ("transaction_amt", "REAL"),
            ("other_id", "TEXT"),
            ("tran_id", "TEXT"),
            ("file_num", "INTEGER"),
            ("memo_cd", "TEXT"),
            ("memo_text", "TEXT"),
            ("sub_id", "INTEGER"),
        ],
        "primary_key": "sub_id",
        "indexes": [
            ("idx_indiv_cmte_id", "cmte_id"),
            ("idx_indiv_other_id", "other_id"),
            ("idx_indiv_employer", "employer"),
            ("idx_indiv_transaction_dt", "transaction_dt"),
            ("idx_indiv_amt", "transaction_amt"),
            ("idx_indiv_name", "name"),
        ],
    },
}

# ── File-type detection ───────────────────────────────────────────────────────


_ALIASES = {
    "itcont": "indiv",
}


def detect_schema_key(filename: str) -> str | None:
    """Return the SCHEMAS key for a given filename, or None if unrecognised."""
    stem = Path(filename).stem.lower()
    if stem in _ALIASES:
        return _ALIASES[stem]
    for key in SCHEMAS:
        if stem.startswith(key):
            return key
    return None


# ── Database helpers ──────────────────────────────────────────────────────────


def create_table(conn: sqlite3.Connection, schema: dict) -> None:
    table = schema["table"]
    pk = schema["primary_key"]
    cols = schema["columns"]

    col_defs = []
    for name, dtype in cols:
        suffix = " PRIMARY KEY" if name == pk else ""
        col_defs.append(f"    {name} {dtype}{suffix}")

    ddl = f"CREATE TABLE IF NOT EXISTS {table} (\n" + ",\n".join(col_defs) + "\n);"
    conn.execute(ddl)

    for idx_name, idx_cols in schema["indexes"]:
        conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({idx_cols});")

    conn.commit()


def coerce_row(row: list[str], columns: list[tuple]) -> tuple:
    """Convert each field to its target type; empty strings become None."""
    out = []
    for value, (_, dtype) in zip(row, columns):
        v = value.strip()
        if v == "":
            out.append(None)
        elif dtype == "REAL":
            try:
                out.append(float(v.replace(",", "")))
            except ValueError:
                out.append(None)
        elif dtype == "INTEGER":
            try:
                out.append(int(v))
            except ValueError:
                out.append(None)
        else:
            out.append(v)
    return tuple(out)


def insert_rows(
    conn: sqlite3.Connection,
    schema: dict,
    reader: csv.reader,
) -> int:
    table = schema["table"]
    columns = schema["columns"]
    n_cols = len(columns)
    col_names = ", ".join(c for c, _ in columns)
    placeholders = ", ".join("?" * n_cols)
    sql = f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders});"

    batch: list[tuple] = []
    total = 0

    for raw in reader:
        if len(raw) < n_cols:
            # Pad short rows (trailing empty fields sometimes omitted)
            raw = raw + [""] * (n_cols - len(raw))
        elif len(raw) > n_cols:
            raw = raw[:n_cols]

        batch.append(coerce_row(raw, columns))

        if len(batch) >= BATCH_SIZE:
            conn.executemany(sql, batch)
            conn.commit()
            total += len(batch)
            batch.clear()
            print(f"  … {total:,} rows inserted", end="\r")

    if batch:
        conn.executemany(sql, batch)
        conn.commit()
        total += len(batch)

    return total


# ── File reading (zip or plain text) ─────────────────────────────────────────


def open_text_stream(path: Path):
    """
    Yield a text stream for the given path.
    If the path is a .zip, locate the first matching .txt inside it.
    """
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            txt_names = [n for n in zf.namelist() if n.lower().endswith(".txt")]
            if not txt_names:
                raise ValueError(f"No .txt file found inside {path}")
            target = txt_names[0]
            print(f"  Extracting {target} from {path.name}")
            with zf.open(target) as raw:
                yield io.TextIOWrapper(raw, encoding="latin-1")
    else:
        with path.open(encoding="latin-1") as fh:
            yield fh


# ── Main loading logic ────────────────────────────────────────────────────────


def load_file(conn: sqlite3.Connection, path: Path) -> None:
    schema_key = detect_schema_key(path.name)
    if schema_key is None:
        print(
            f"[skip] {path.name}: unrecognised filename (expected weball/webk/ccl/itpas2/itoth/itcont)"
        )
        return

    schema = SCHEMAS[schema_key]
    print(f"[load] {path.name} → table '{schema['table']}'")

    create_table(conn, schema)

    for stream in open_text_stream(path):
        reader = csv.reader(
            stream, delimiter="|", quoting=csv.QUOTE_NONE, escapechar="\\"
        )
        count = insert_rows(conn, schema, reader)

    print(f"  Done: {count:,} rows loaded into '{schema['table']}'")


def build_derived_tables(conn: sqlite3.Connection) -> None:
    required = {"individual_contributions", "candidate_committee_linkage", "all_candidates"}
    existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = required - existing
    if missing:
        print(f"  [skip] Missing tables: {', '.join(missing)} — load required files first.")
        return

    print("Building pac_bundled_recipients...")
    conn.execute("DROP TABLE IF EXISTS pac_bundled_recipients")
    conn.execute(
        """CREATE TABLE pac_bundled_recipients AS
        SELECT
            ic.other_id AS pac_id,
            ccl.cand_id,
            MAX(ac.cand_name) AS cand_name,
            ac.cand_pty_affiliation AS party,
            ac.cand_office_st AS state,
            ROUND(SUM(ic.transaction_amt)) AS bundled_amt
        FROM individual_contributions ic
        JOIN candidate_committee_linkage ccl ON ic.cmte_id = ccl.cmte_id
        JOIN all_candidates ac ON ccl.cand_id = ac.cand_id
        WHERE ic.other_id IS NOT NULL AND ic.other_id != ''
        GROUP BY ic.other_id, ccl.cand_id"""
    )
    conn.execute(
        "CREATE INDEX idx_pbr_pac_id ON pac_bundled_recipients (pac_id, bundled_amt DESC)"
    )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM pac_bundled_recipients").fetchone()[0]
    print(f"  Done: {count:,} rows")


def collect_paths(inputs: list[str]) -> list[Path]:
    """Expand directories to their .txt/.zip children; pass files through."""
    paths: list[Path] = []
    for raw in inputs:
        p = Path(raw)
        if p.is_dir():
            paths.extend(sorted(p.glob("*.txt")))
            paths.extend(sorted(p.glob("*.zip")))
        elif p.exists():
            paths.append(p)
        else:
            print(f"[warn] {raw}: path not found, skipping", file=sys.stderr)
    return paths


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load FEC bulk data files into SQLite."
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        metavar="FILE_OR_DIR",
        help=".txt or .zip FEC data files, or a directory containing them",
    )
    parser.add_argument(
        "--db",
        default="fec.db",
        metavar="PATH",
        help="SQLite database file to write to (default: fec.db)",
    )
    parser.add_argument(
        "--build-derived",
        action="store_true",
        help="Skip file loading; just rebuild derived tables from existing data",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    print(f"Database: {db_path.resolve()}")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")

    if not args.build_derived:
        paths = collect_paths(args.inputs)
        if not paths:
            print("No files to load.", file=sys.stderr)
            sys.exit(1)

        for path in paths:
            load_file(conn, path)

    build_derived_tables(conn)
    conn.close()
    print("\nAll done.")


if __name__ == "__main__":
    main()
