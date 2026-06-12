"""
Pre-build data export script.
Run: python scripts/export_data.py
Outputs JSON files consumed by the static SvelteKit build.
"""

import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, 'fec.db')
OUT_DIR = os.path.join(ROOT, 'frontend', 'src', 'lib', 'data')


def write(file_path: str, data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"wrote {os.path.relpath(file_path, ROOT)}")


con = sqlite3.connect(DB_PATH)
con.row_factory = sqlite3.Row

# ── PACs list ─────────────────────────────────────────────────────────────────
pacs = [dict(row) for row in con.execute("""
    SELECT
        cmte_id,
        cmte_nm                         AS name,
        ROUND(ttl_receipts)             AS total_receipts,
        ROUND(indv_contrib)             AS indiv_contrib,
        ROUND(ttl_disb)                 AS total_spent,
        ROUND(coh_cop)                  AS cash_on_hand
    FROM pac_summary
    WHERE ttl_receipts >= 10000
    ORDER BY total_receipts DESC
    LIMIT 500
""").fetchall()]
write(os.path.join(OUT_DIR, 'pacs.json'), pacs)

# ── Politicians list ───────────────────────────────────────────────────────────
politicians = [dict(row) for row in con.execute("""
    SELECT
        MIN(cand_id)                    AS cand_id,
        cand_name,
        cand_pty_affiliation            AS party,
        cand_office_st                  AS state,
        MIN(cand_ici)                   AS incumbent_status,
        ROUND(MAX(ttl_receipts))        AS total_raised,
        ROUND(MAX(other_pol_cmte_contrib)) AS pac_total,
        ROUND(MAX(ttl_indiv_contrib))   AS indiv_total
    FROM all_candidates
    WHERE ttl_receipts >= 10000
    GROUP BY cand_name, cand_pty_affiliation, cand_office_st
    ORDER BY total_raised DESC
    LIMIT 500
""").fetchall()]
write(os.path.join(OUT_DIR, 'politicians.json'), politicians)

# ── Individual PAC detail pages ────────────────────────────────────────────────
pac_list = [row['cmte_id'] for row in con.execute(
    "SELECT cmte_id FROM pac_summary WHERE ttl_receipts >= 10000"
).fetchall()]

RECIPIENTS_SQL = """
    SELECT
        cand_id,
        MAX(cand_name) AS cand_name,
        MAX(party) AS party,
        MAX(state) AS state,
        ROUND(SUM(total_amt)) AS total_amt,
        ROUND(SUM(direct_amt)) AS direct_amt,
        ROUND(SUM(ie_amt)) AS ie_amt,
        ROUND(SUM(bundled_amt)) AS bundled_amt
    FROM (
        SELECT
            c.cand_id,
            COALESCE(a.cand_name, c.name) AS cand_name,
            a.cand_pty_affiliation AS party,
            a.cand_office_st AS state,
            c.transaction_amt AS total_amt,
            CASE WHEN c.transaction_tp = '24K' THEN c.transaction_amt ELSE 0 END AS direct_amt,
            CASE WHEN c.transaction_tp = '24E' THEN c.transaction_amt ELSE 0 END AS ie_amt,
            0 AS bundled_amt
        FROM contributions c
        LEFT JOIN all_candidates a ON c.cand_id = a.cand_id
        WHERE c.cmte_id = ? AND c.transaction_tp != '24A'

        UNION ALL

        SELECT
            cand_id, cand_name, party, state,
            bundled_amt AS total_amt,
            0 AS direct_amt,
            0 AS ie_amt,
            bundled_amt
        FROM pac_bundled_recipients
        WHERE pac_id = ?
    )
    GROUP BY cand_id
    ORDER BY total_amt DESC
"""

PAC_DETAIL_SQL = """
    SELECT
        cmte_nm AS name,
        cmte_tp AS committee_type,
        ROUND(ttl_receipts) AS total_receipts,
        ROUND(indv_contrib) AS indiv_contrib,
        ROUND(ttl_disb) AS total_spent,
        ROUND(coh_cop) AS cash_on_hand
    FROM pac_summary WHERE cmte_id = ?
"""

CANDIDATES_FUNDED_SQL = """
    SELECT COUNT(DISTINCT cand_id) AS candidates_funded
    FROM contributions
    WHERE cmte_id = ? AND transaction_tp != '24A'
"""

PAC_TRANSFERS_SQL = """
    SELECT
        ct.other_id AS cmte_id,
        COALESCE(p.cmte_nm, ct.name) AS pac_name,
        ROUND(SUM(ct.transaction_amt)) AS total_amt,
        COUNT(*) AS tx_count
    FROM committee_transactions ct
    LEFT JOIN pac_summary p ON ct.other_id = p.cmte_id
    WHERE ct.cmte_id = ?
      AND ct.other_id != ct.cmte_id
      AND ct.other_id NOT IN (SELECT cmte_id FROM candidate_committee_linkage)
    GROUP BY ct.other_id
    ORDER BY total_amt DESC
"""

print(f"Exporting {len(pac_list)} PAC detail pages...")
for cmte_id in pac_list:
    pac = con.execute(PAC_DETAIL_SQL, (cmte_id,)).fetchone()
    if pac is None:
        continue
    stats = con.execute(CANDIDATES_FUNDED_SQL, (cmte_id,)).fetchone()
    recipients = [dict(row) for row in con.execute(RECIPIENTS_SQL, (cmte_id, cmte_id)).fetchall()]
    pac_transfers = [dict(row) for row in con.execute(PAC_TRANSFERS_SQL, (cmte_id,)).fetchall()]
    write(
        os.path.join(OUT_DIR, 'pacs', f'{cmte_id}.json'),
        {'pac': dict(pac), 'stats': dict(stats), 'recipients': recipients, 'pacTransfers': pac_transfers, 'cmte_id': cmte_id}
    )

# ── Individual politician detail pages ─────────────────────────────────────────
politician_list = [
    {'cand_id': row['cand_id'], 'state': row['state']}
    for row in con.execute("""
        SELECT MIN(cand_id) AS cand_id, cand_office_st AS state
        FROM all_candidates
        WHERE ttl_receipts >= 10000
        GROUP BY cand_name, cand_pty_affiliation, cand_office_st
    """).fetchall()
]

POLITICIAN_DETAIL_SQL = """
    SELECT cand_name, cand_pty_affiliation AS party, cand_office_st AS state,
        ROUND(ttl_indiv_contrib) AS indiv_total,
        ROUND(other_pol_cmte_contrib) AS pac_receipts_summary
    FROM all_candidates WHERE cand_id = ?
    ORDER BY ttl_receipts DESC LIMIT 1
"""

DONATIONS_SQL = """
    SELECT
        c.cmte_id,
        COALESCE(p.cmte_nm, c.name) AS pac_name,
        ROUND(SUM(c.transaction_amt)) AS total_amt,
        ROUND(SUM(CASE WHEN c.transaction_tp = '24K' THEN c.transaction_amt ELSE 0 END)) AS direct_amt,
        ROUND(SUM(CASE WHEN c.transaction_tp = '24E' THEN c.transaction_amt ELSE 0 END)) AS ie_amt
    FROM contributions c
    LEFT JOIN pac_summary p ON c.cmte_id = p.cmte_id
    WHERE c.cand_id = ? AND c.transaction_tp != '24A'
    GROUP BY c.cmte_id
    ORDER BY total_amt DESC
"""

INDIV_STATS_SQL = """
    SELECT
        COUNT(*) AS unique_donors,
        COUNT(CASE WHEN state != :state THEN 1 END) AS oos_donors,
        ROUND(SUM(CASE WHEN state != :state THEN amt ELSE 0 END)) AS oos_total
    FROM (
        SELECT ic.name, ic.zip_code, ic.state, SUM(ic.transaction_amt) AS amt
        FROM individual_contributions ic
        JOIN candidate_committee_linkage ccl ON ic.cmte_id = ccl.cmte_id
        WHERE ccl.cand_id = :cand_id AND ic.transaction_amt > 0
        GROUP BY ic.name, ic.zip_code, ic.state
    )
"""

OPPOSITION_SQL = """
    SELECT
        c.cmte_id,
        COALESCE(p.cmte_nm, c.name) AS pac_name,
        ROUND(SUM(c.transaction_amt)) AS total_amt
    FROM contributions c
    LEFT JOIN pac_summary p ON c.cmte_id = p.cmte_id
    WHERE c.cand_id = ? AND c.transaction_tp = '24A'
    GROUP BY c.cmte_id
    ORDER BY total_amt DESC
"""

print(f"Exporting {len(politician_list)} politician detail pages...")
for entry in politician_list:
    cand_id = entry['cand_id']
    state = entry['state']
    politician = con.execute(POLITICIAN_DETAIL_SQL, (cand_id,)).fetchone()
    if politician is None:
        continue
    donations = [dict(row) for row in con.execute(DONATIONS_SQL, (cand_id,)).fetchall()]
    indiv_stats = con.execute(INDIV_STATS_SQL, {'state': state, 'cand_id': cand_id}).fetchone()
    opposition = [dict(row) for row in con.execute(OPPOSITION_SQL, (cand_id,)).fetchall()]
    write(
        os.path.join(OUT_DIR, 'politicians', f'{cand_id}.json'),
        {
            'politician': dict(politician),
            'donations': donations,
            'indivStats': dict(indiv_stats) if indiv_stats else None,
            'opposition': opposition,
        }
    )

# ── Search index ───────────────────────────────────────────────────────────────
search_politicians = [dict(row) for row in con.execute("""
    SELECT MIN(cand_id) AS cand_id, cand_name,
        cand_pty_affiliation AS party,
        cand_office_st AS state,
        SUBSTR(MIN(cand_id), 1, 1) AS office_code
    FROM all_candidates
    WHERE ttl_receipts >= 10000
    GROUP BY cand_name, cand_pty_affiliation, cand_office_st
    ORDER BY MAX(ttl_receipts) DESC
""").fetchall()]

search_pacs = [dict(row) for row in con.execute("""
    SELECT cmte_id, cmte_nm AS name, cmte_tp AS committee_type
    FROM pac_summary
    WHERE ttl_receipts >= 10000
    ORDER BY ttl_receipts DESC
""").fetchall()]

write(os.path.join(OUT_DIR, 'search-index.json'), {'politicians': search_politicians, 'pacs': search_pacs})

con.close()
print('Done.')
