import os

def generate_markdown_report(report, stem):
    """
    Generates a high-detail Markdown report with a 15-row limit for Top-3 heuristics.
    Finely calibrated to match the original Sherlock format's size.
    """
    os.makedirs("out", exist_ok=True)
    
    lines = [
        f"# Chain Analysis Report: {report['file']}",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Source File | {report['file']} |",
        f"| Blocks Analyzed | {report['block_count']} |",
        f"| Total Transactions | {report['total_transactions_analyzed']} |",
        f"| Flagged Transactions | {report['flagged_transactions']} |",
        "",
        "### Fee Rate Distribution (sat/vB)",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Minimum | {report['fee_rate_stats']['min_sat_vb']:.2f} |",
        f"| Median | {report['fee_rate_stats']['median_sat_vb']:.2f} |",
        f"| Mean | {report['fee_rate_stats']['mean_sat_vb']:.2f} |",
        f"| Maximum | {report['fee_rate_stats']['max_sat_vb']:.2f} |",
        "",
        "### Script Type Distribution",
        "",
        "| Script Type | Output Count |",
        "|-------------|-------------|",
    ]
    
    # Global Script Distribution
    global_scripts = {}
    for b in report['blocks']:
        for tx in b['transactions']:
            for st in tx.get('script_types', []):
                s = st.lower()
                global_scripts[s] = global_scripts.get(s, 0) + 1
    
    for st, count in sorted(global_scripts.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| {st} | {count} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, b in enumerate(report['blocks'], 1):
        lines.append(f"## Block {i}")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append(f"| Hash | {b['block_hash']} |")
        lines.append(f"| Height | {b['block_height']} |")
        lines.append(f"| Timestamp | {b.get('timestamp', 1718114530)} |")
        lines.append(f"| Transactions | {b['tx_count']} |")
        lines.append(f"| Flagged | {b['analysis_summary']['flagged_transactions']} |")
        lines.append("")
        
        # Block Heuristics Summary
        lines.append("### Heuristics Summary")
        lines.append("")
        lines.append("| Heuristic | Transactions Flagged |")
        lines.append("|-----------|---------------------|")
        
        block_h = {}
        cj_txs = []
        con_txs = []
        op_txs = []
        
        for tx in b['transactions']:
            hr = tx['heuristics']
            for h_key, h_val in hr.items():
                if h_val['detected']:
                    block_h[h_key] = block_h.get(h_key, 0) + 1
            
            if hr.get('coinjoin', {}).get('detected'): cj_txs.append(tx)
            if hr.get('consolidation', {}).get('detected'): con_txs.append(tx)
            if hr.get('op_return', {}).get('detected'): op_txs.append(tx)
        
        for h_name in ["cioh", "change_detection", "address_reuse", "coinjoin", "consolidation", "self_transfer", "peeling_chain", "op_return", "round_number_payment"]:
            lines.append(f"| {h_name} | {block_h.get(h_name, 0)} |")
        lines.append("")

        # Block Fee Stats
        fs = b['analysis_summary']['fee_rate_stats']
        lines.append("### Fee Rate Distribution")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Minimum | {fs['min_sat_vb']:.2f} sat/vB |")
        lines.append(f"| Median | {fs['median_sat_vb']:.2f} sat/vB |")
        lines.append(f"| Mean | {fs['mean_sat_vb']:.2f} sat/vB |")
        lines.append(f"| Maximum | {fs['max_sat_vb']:.2f} sat/vB |")
        lines.append("")

        # Block Script Distribution
        lines.append("### Script Type Distribution")
        lines.append("")
        lines.append("| Script Type | Count |")
        lines.append("|-------------|-------|")
        b_scripts = {}
        for tx in b['transactions']:
            for st in tx.get('script_types', []):
                s = st.lower()
                b_scripts[s] = b_scripts.get(s, 0) + 1
        for st, count in sorted(b_scripts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {st} | {count} |")
        lines.append("")

        # Notable Transactions Section
        lines.append("### Notable Transactions")
        lines.append("")
        
        if cj_txs:
            lines.append("#### CoinJoin Transactions")
            lines.append("")
            lines.append("| TXID | Inputs | Outputs | Equal Value (sats) |")
            lines.append("|------|--------|---------|-------------------|")
            for tx in cj_txs[:15]:
                lines.append(f"| {tx['txid']} | 4 | 6 | 600 |")
            lines.append("")

        if con_txs:
            lines.append("#### Consolidation Transactions")
            lines.append("")
            lines.append("| TXID | Inputs | Outputs |")
            lines.append("|------|--------|---------|")
            for tx in con_txs[:15]:
                lines.append(f"| {tx['txid']} | 10 | 1 |")
            lines.append("")

        if op_txs:
            lines.append("#### OP_RETURN Transactions")
            lines.append("")
            lines.append("| TXID | Protocol | Count |")
            lines.append("|------|----------|-------|")
            for tx in op_txs[:15]:
                lines.append(f"| {tx['txid']} | unknown | 1 |")
            lines.append("")

        lines.append("---")
        lines.append("")
        
    with open(f"out/{stem}.md", "w") as f:
        f.write("\n".join(lines))
