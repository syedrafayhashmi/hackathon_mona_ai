#!/usr/bin/env python
from app.workflows import execute_workflow

if __name__ == "__main__":
    result, confidence, decision, requires_approval, events = execute_workflow("1", "invoice-batch", "test-filenames")
    print("Invoice | Vendor | Total")
    print("-" * 80)
    for row in result.table.rows:
        print(f"{row['Invoice']} | {row['Vendor']} | {row['Total']}")
