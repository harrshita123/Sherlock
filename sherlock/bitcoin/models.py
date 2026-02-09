from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class BlockHeader:
    version: int
    prev_hash: str
    merkle_root: str
    timestamp: int
    bits: int
    nonce: int

@dataclass
class Input:
    txid: str
    vout: int
    script_sig: bytes
    sequence: int
    witness: List[bytes] = field(default_factory=list)
    prev_output: Optional['Output'] = None

@dataclass
class Output:
    value: int
    script_pubkey: bytes
    script_type: str = "unknown"
    address: str = ""

@dataclass
class Transaction:
    version: int
    inputs: List[Input]
    outputs: List[Output]
    locktime: int
    txid: str
    has_witness: bool = False

@dataclass
class Block:
    header: BlockHeader
    transactions: List[Transaction]
    hash: str
    height: int
