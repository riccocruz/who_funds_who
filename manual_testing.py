import sqlite3

db = sqlite3.connect("fec.db")
db.row_factory = sqlite3.Row

# Table summary
for table, pk in [
    ("all_candidates", "cand_id"),
    ("pac_summary", "cmte_id"),
    ("contributions", "sub_id"),
    ("candidate_committee_linkage", "linkage_id"),
]:
    count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table:30} {count:>8,} rows")

print("\n--- Sample candidates ---")
for row in db.execute(
    "SELECT cand_name, cand_office_st, ROUND(ttl_receipts) as amt "
    "FROM all_candidates ORDER BY ttl_receipts DESC LIMIT 5"
):
    print(f'{row["cand_name"]:30} {row["cand_office_st"]} ${row["amt"]:>12,.0f}')

print("\n--- Total contributions to candidates ---")
row = db.execute(
    "SELECT COUNT(*) as cnt, ROUND(SUM(transaction_amt)) as total "
    "FROM contributions WHERE cand_id IS NOT NULL"
).fetchone()
print(f'  {row["cnt"]:,} transactions totaling ${row["total"]:,.0f}')

# ── PAC → Candidate funding ───────────────────────────────────────────────────
# transaction_tp meanings:
#   24K = direct contribution to candidate
#   24E = independent expenditure FOR candidate
#   24A = independent expenditure AGAINST candidate

print("\n--- Top PACs by total direct contributions (24K) to candidates ---")
for row in db.execute("""
    SELECT
        ps.cmte_nm          AS pac_name,
        COUNT(*)            AS num_transactions,
        ROUND(SUM(c.transaction_amt)) AS total_given
    FROM contributions c
    JOIN pac_summary ps ON c.cmte_id = ps.cmte_id
    WHERE c.cand_id IS NOT NULL
      AND c.transaction_tp = '24K'
    GROUP BY c.cmte_id
    ORDER BY total_given DESC
    LIMIT 10
"""):
    print(
        f'  {row["pac_name"][:45]:45}  ${row["total_given"]:>12,.0f}  ({row["num_transactions"]} txns)'
    )

print("\n--- Candidates receiving the most PAC money ---")
for row in db.execute("""
    SELECT
        ac.cand_name        AS candidate,
        ac.cand_office_st   AS state,
        ac.cand_pty_affiliation AS party,
        COUNT(*)            AS num_pacs,
        ROUND(SUM(c.transaction_amt)) AS total_received
    FROM contributions c
    JOIN all_candidates ac ON c.cand_id = ac.cand_id
    WHERE c.transaction_tp = '24K'
    GROUP BY c.cand_id
    ORDER BY total_received DESC
    LIMIT 10
"""):
    print(
        f'  {row["candidate"][:35]:35} {row["state"]} {row["party"]:4}  ${row["total_received"]:>12,.0f}  ({row["num_pacs"]} PACs)'
    )

print("\n--- Who funds a specific candidate? (top donors to most-funded candidate) ---")
top_cand = db.execute("""
    SELECT c.cand_id, ac.cand_name
    FROM contributions c
    JOIN all_candidates ac ON c.cand_id = ac.cand_id
    WHERE c.transaction_tp = '24K'
    GROUP BY c.cand_id
    ORDER BY SUM(c.transaction_amt) DESC
    LIMIT 1
""").fetchone()

print(f"  Candidate: {top_cand['cand_name']}")
for row in db.execute(
    """
    SELECT
        COALESCE(ps.cmte_nm, c.name)  AS donor_name,
        c.transaction_tp,
        ROUND(SUM(c.transaction_amt)) AS total
    FROM contributions c
    LEFT JOIN pac_summary ps ON c.cmte_id = ps.cmte_id
    WHERE c.cand_id = ?
    GROUP BY c.cmte_id
    ORDER BY total DESC
    LIMIT 10
""",
    (top_cand["cand_id"],),
):
    print(
        f'    {row["donor_name"][:50]:50}  ${row["total"]:>10,.0f}  [{row["transaction_tp"]}]'
    )

# ── AIPAC-funded candidates ───────────────────────────────────────────────────
# AIPAC operates through multiple affiliated committees:
#   - AMERICAN ISRAEL PUBLIC AFFAIRS COMMITTEE POLITICAL ACTION COMMITTEE (direct PAC)
#   - UNITED DEMOCRACY PROJECT / UDP (super PAC arm — largest spender)
# NOTE: this dataset covers only the current election cycle (weball26 = 2025-2026).
#       OpenSecrets figures may reflect prior cycles or career totals.
aipac_committees = db.execute("""
    SELECT cmte_id, cmte_nm FROM pac_summary
    WHERE cmte_nm LIKE '%AMERICAN ISRAEL PUBLIC AFFAIRS%'
       OR cmte_nm LIKE '%UNITED DEMOCRACY PROJECT%'
""").fetchall()

if aipac_committees:
    aipac_ids = [r["cmte_id"] for r in aipac_committees]
    print(f"\n--- AIPAC committees found ({len(aipac_ids)}) ---")
    for r in aipac_committees:
        print(f"  {r['cmte_id']}  {r['cmte_nm']}")

    placeholders = ",".join("?" * len(aipac_ids))
    print(
        f"\n--- Top 10 candidates funded by AIPAC (all transaction types, by total) ---"
    )
    for row in db.execute(
        f"""
        SELECT
            ac.cand_name                        AS candidate,
            ac.cand_office_st                   AS state,
            ac.cand_pty_affiliation             AS party,
            ROUND(SUM(c.transaction_amt))       AS total,
            ROUND(SUM(CASE WHEN c.transaction_tp = '24K' THEN c.transaction_amt ELSE 0 END)) AS direct,
            ROUND(SUM(CASE WHEN c.transaction_tp = '24E' THEN c.transaction_amt ELSE 0 END)) AS indep_for,
            ROUND(SUM(CASE WHEN c.transaction_tp = '24A' THEN c.transaction_amt ELSE 0 END)) AS indep_against,
            COUNT(*)                            AS num_transactions
        FROM contributions c
        JOIN all_candidates ac ON c.cand_id = ac.cand_id
        WHERE c.cmte_id IN ({placeholders})
        GROUP BY c.cand_id
        ORDER BY total DESC
        LIMIT 10
    """,
        aipac_ids,
    ):
        print(
            f'  {row["candidate"][:35]:35} {row["state"]} {row["party"]:4}'
            f'  total=${row["total"]:>10,.0f}'
            f'  direct=${row["direct"]:>9,.0f}'
            f'  indep_for=${row["indep_for"]:>9,.0f}'
            f'  indep_against=${row["indep_against"]:>9,.0f}'
        )
else:
    print("\n--- AIPAC: no matching committee found in this dataset ---")
    print("  Try browsing pac names with:")
    print(
        "  SELECT cmte_id, cmte_nm FROM pac_summary WHERE cmte_nm LIKE '%<keyword>%';"
    )

# ── AIPAC → Committee money flow (itoth) ─────────────────────────────────────
# committee_transactions (itoth) records committee-to-committee transfers.
# 18K = earmarked contribution to intermediary/conduit
# 24K = direct contribution to another committee
# 22Z = contribution to registered party committee
if aipac_committees:
    print(f"\n--- Top 20 committees AIPAC gives money to (committee_transactions) ---")
    for row in db.execute(
        f"""
        SELECT
            ct.other_id                                         AS recipient_id,
            COALESCE(ps.cmte_nm, ac_ccl.cand_name, ct.other_id) AS recipient_name,
            ct.transaction_tp,
            COUNT(*)                                            AS txns,
            ROUND(SUM(ct.transaction_amt))                      AS total
        FROM committee_transactions ct
        LEFT JOIN pac_summary ps ON ct.other_id = ps.cmte_id
        LEFT JOIN candidate_committee_linkage ccl ON ct.other_id = ccl.cmte_id
        LEFT JOIN all_candidates ac_ccl ON ccl.cand_id = ac_ccl.cand_id
        WHERE ct.cmte_id IN ({placeholders})
        GROUP BY ct.other_id, ct.transaction_tp
        ORDER BY total DESC
        LIMIT 20
    """,
        aipac_ids,
    ):
        print(
            f'  [{row["transaction_tp"]}]  {row["recipient_name"][:50]:50}'
            f'  ${row["total"]:>10,.0f}  ({row["txns"]} txns)  [{row["recipient_id"]}]'
        )

# ── AIPAC bundled individual donations (indiv26) ─────────────────────────────
# individual_contributions (itcont) with other_id = AIPAC committee ID means
# the individual donated through AIPAC as a conduit (transaction_tp = 15E,
# memo_text = "EARMARKED FROM AMERICAN ISRAEL PUBLIC AFFAIRS COMMITTEE...").
# This is the bundling mechanism OpenSecrets counts in their org totals.
if aipac_committees:
    print(f"\n--- Top 20 candidates receiving AIPAC-bundled individual donations ---")
    for row in db.execute(
        f"""
        SELECT
            ac.cand_name                        AS candidate,
            ac.cand_office_st                   AS state,
            ac.cand_pty_affiliation             AS party,
            COUNT(*)                            AS donors,
            ROUND(SUM(ic.transaction_amt))      AS total
        FROM individual_contributions ic
        JOIN candidate_committee_linkage ccl ON ic.cmte_id = ccl.cmte_id
        JOIN all_candidates ac ON ccl.cand_id = ac.cand_id
        WHERE ic.other_id IN ({placeholders})
        GROUP BY ac.cand_id
        ORDER BY total DESC
        LIMIT 50
    """,
        aipac_ids,
    ):
        print(
            f'  {row["candidate"][:35]:35} {row["state"]} {row["party"]:4}'
            f'  ${row["total"]:>10,.0f}  ({row["donors"]} donors)'
        )

db.close()
