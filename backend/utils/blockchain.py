import hashlib
import json
import time
from datetime import datetime

class BloodBlockchain:
    def __init__(self):
        self.chain = []
        # Create the 'Genesis Block' (The start of the Mumbai Ledger)
        self.create_block(proof=100, previous_hash='0', data="RaktaSetu Ledger Initialized")

    def create_block(self, proof, previous_hash, data):
        """Creates a new block in the blockchain."""
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash,
            'data': data # This will store the Donor-Patient Match details
        }
        self.chain.append(block)
        return block

    def get_last_block(self):
        return self.chain[-1]

    def hash(self, block):
        """Creates a SHA-256 hash (fingerprint) of a block."""
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self):
        """Validates the integrity of the blood records."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            # Check if the link is broken
            if current['previous_hash'] != self.hash(previous):
                return False
        return True

# Initialize the ledger for the whole system
blood_ledger = BloodBlockchain()

# =====================================================================
# B2B MARKETPLACE CRYPTOGRAPHY
# =====================================================================

def create_secure_trade_hash(sender, receiver, payload):
    """
    Utility function for the B2B Marketplace.
    Generates a true SHA-256 hash based on transaction parameters.
    """
    # Generate exact UNIX timestamp in milliseconds
    timestamp = str(int(time.time() * 1000)) 
    
    # Concatenate transaction details into a single string block
    block_data = f"{sender}|{receiver}|{payload}|{timestamp}"
    
    # Generate the SHA-256 hash and truncate to 32 chars for clean DB storage
    secure_hash = "blk_" + hashlib.sha256(block_data.encode('utf-8')).hexdigest()[:32]
    
    return secure_hash, timestamp