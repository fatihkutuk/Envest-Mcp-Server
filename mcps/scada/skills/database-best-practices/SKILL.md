---
name: database-best-practices
description: |
  Best practices for database analysis and querying.
  Use when: analyzing database schemas, writing queries, optimizing tables.
version: "1.0.0"
---

# Database Best Practices

## Query Writing
- Always use LIMIT for large tables to avoid overwhelming results
- Use COUNT(*) before SELECT * to check row count first
- Index columns used in WHERE clauses for better performance
- Prefer specific column names over SELECT * in production queries
- Use aliases for readability in complex joins

## Schema Analysis
- Start with list_tables to get an overview
- Use describe_table for detailed column info and sample data
- Use find_related_tables to understand relationships before writing JOINs
- Check analyze_table for data quality (null percentages, distinct counts)

## Performance Tips
- Check row counts before running broad queries
- Use WHERE clauses to filter early
- Avoid LIKE '%value%' on large tables (no index usage)
- Use EXPLAIN to understand query execution plans
- Consider time-range filters for timestamp columns

## Data Quality Checks
- Look for high null percentages in required fields
- Check distinct counts vs row counts (detect duplicates)
- Verify foreign key relationships exist in both directions
- Check min/max ranges for numeric fields (detect outliers)

## Common Patterns
- Top N analysis: SELECT col, COUNT(*) GROUP BY col ORDER BY COUNT(*) DESC LIMIT N
- Date range: WHERE date_col BETWEEN '2024-01-01' AND '2024-12-31'
- Null audit: SELECT COUNT(*) - COUNT(col) AS nulls FROM table
- Duplicate check: SELECT col, COUNT(*) HAVING COUNT(*) > 1
