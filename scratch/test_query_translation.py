import re

def adapt_sql_for_sqlite(sql, params=None):
    params = list(params) if params else []
    
    # 1. ISNULL -> COALESCE
    sql = re.sub(r'\bISNULL\s*\(', 'COALESCE(', sql, flags=re.IGNORECASE)
    
    # 2. GETDATE() -> CURRENT_TIMESTAMP
    sql = re.sub(r'\bGETDATE\s*\(\s*\)', 'CURRENT_TIMESTAMP', sql, flags=re.IGNORECASE)
    
    # 3. OFFSET ? ROWS FETCH NEXT ? ROWS ONLY -> LIMIT ? OFFSET ?
    # Case with ? placeholders
    m = re.search(r'OFFSET\s+(\?|\d+)\s+ROWS\s+FETCH\s+NEXT\s+(\?|\d+)\s+ROWS\s+ONLY', sql, flags=re.IGNORECASE)
    if m:
        p1, p2 = m.group(1), m.group(2)
        if p1 == '?' and p2 == '?':
            # In SQL Server: query_params = params + [offset, page_size]
            # In SQLite: LIMIT page_size OFFSET offset
            # So if params has [..., offset, page_size], we swap the last two params
            if len(params) >= 2:
                params[-2], params[-1] = params[-1], params[-2]
            sql = sql[:m.start()] + 'LIMIT ? OFFSET ?' + sql[m.end():]
        elif p1.isdigit() and p2.isdigit():
            sql = sql[:m.start()] + f'LIMIT {p2} OFFSET {p1}' + sql[m.end():]
            
    return sql, params

# Test
sql1 = "SELECT ISNULL(SUM(CAST(dugwells AS BIGINT)), 0) FROM Villages WHERE created_at <= GETDATE()"
s1, p1 = adapt_sql_for_sqlite(sql1)
print("Adapted SQL 1:", s1)

sql2 = "SELECT * FROM Villages WHERE 1=1 ORDER BY id OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
s2, p2 = adapt_sql_for_sqlite(sql2, [10, 20])
print("Adapted SQL 2:", s2, p2)
