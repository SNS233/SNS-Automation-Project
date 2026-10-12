import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import db

rows = db.query_all("""
SELECT 
    COALESCE(NULLIF(TRIM(zone), ''), 'Unassigned Zone') AS zone_name,
    COUNT(*) AS total_villages,
    SUM(CASE WHEN (COALESCE(work_status, '') = 'Done' OR COALESCE(kml_status, '') IN ('Done', 'Verified', 'Marking Completed', 'Finalized')) THEN 1 ELSE 0 END) AS completed_villages,
    SUM(CASE WHEN kml_status = 'In Progress' AND COALESCE(work_status, '') != 'Done' THEN 1 ELSE 0 END) AS in_progress_villages,
    SUM(CASE WHEN (COALESCE(work_status, '') != 'Done' AND COALESCE(kml_status, '') NOT IN ('Done', 'Verified', 'Marking Completed', 'Finalized')) THEN 1 ELSE 0 END) AS pending_villages
FROM Villages
GROUP BY COALESCE(NULLIF(TRIM(zone), ''), 'Unassigned Zone')
ORDER BY zone_name ASC
""")
tot_all = sum(r['total_villages'] for r in rows)
done_all = sum(r['completed_villages'] for r in rows)
pend_all = sum(r['pending_villages'] for r in rows)
print(f"Total across zones: {tot_all}, Done: {done_all}, Pending: {pend_all}")
for r in rows:
    tot = r['total_villages']
    done = r['completed_villages']
    pend = r['pending_villages']
    pct = round((done / tot * 100), 1) if tot > 0 else 0.0
    print(f"  {r['zone_name']}: Total={tot}, Done={done}, Pending={pend}, InProgress={r['in_progress_villages']}, Completion={pct}%")
