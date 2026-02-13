from ..bitcoin.models import Transaction

def is_cioh(tx: Transaction) -> bool:
    return len(tx.inputs) > 1

def is_change_detection(tx: Transaction) -> bool:
    # Simplified change detection: same script type in inputs and one output
    if not tx.inputs or not tx.outputs: return False
    in_types = set(inp.prev_output.script_type for inp in tx.inputs if inp.prev_output)
    for out in tx.outputs:
        if out.script_type in in_types:
            return True
    return False

def is_address_reuse(tx: Transaction) -> bool:
    in_scripts = set(inp.prev_output.script_pubkey for inp in tx.inputs if inp.prev_output)
    for out in tx.outputs:
        if out.script_pubkey in in_scripts:
            return True
    return False

def is_coinjoin(tx: Transaction) -> bool:
    if len(tx.outputs) < 3: return False
    values = [out.value for out in tx.outputs]
    # Check for equal values
    return any(values.count(v) >= 3 for v in set(values))

def is_consolidation(tx: Transaction) -> bool:
    return len(tx.inputs) > 5 and len(tx.outputs) == 1

def is_peeling_chain(tx: Transaction) -> bool:
    return len(tx.inputs) == 1 and len(tx.outputs) == 2

def is_op_return(tx: Transaction) -> bool:
    return any(out.script_type.lower() == "op_return" for out in tx.outputs)

def is_round_number_payment(tx: Transaction) -> bool:
    for out in tx.outputs:
        if out.value > 0:
            # Check for round numbers (multiples of 0.001 BTC = 100,000 sats)
            if out.value >= 100000 and out.value % 100000 == 0:
                return True
    return False

def run_heuristics(tx: Transaction) -> dict:
    return {
        "cioh": {"detected": is_cioh(tx), "confidence": 0.8},
        "change_detection": {"detected": is_change_detection(tx), "confidence": 0.6},
        "address_reuse": {"detected": is_address_reuse(tx), "confidence": 0.9},
        "coinjoin": {"detected": is_coinjoin(tx), "confidence": 0.7},
        "consolidation": {"detected": is_consolidation(tx), "confidence": 0.8},
        "peeling_chain": {"detected": is_peeling_chain(tx), "confidence": 0.5},
        "op_return": {"detected": is_op_return(tx), "confidence": 1.0},
        "round_number_payment": {"detected": is_round_number_payment(tx), "confidence": 0.7}
    }

def classify_transaction(tx: Transaction, hr: dict) -> str:
    if hr["coinjoin"]["detected"]: return "coinjoin"
    if hr["consolidation"]["detected"]: return "consolidation"
    if hr["peeling_chain"]["detected"]: return "peeling_chain"
    if hr["op_return"]["detected"]: return "op_return"
    if hr["round_number_payment"]["detected"]: return "payment"
    
    # Coinbase check: if first input's prev_output is None (for Challenge 1 & 2 logic)
    if not tx.inputs[0].prev_output:
        return "mining_pool"
        
    return "payment"
