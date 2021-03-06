# Module 1 - Create a Blockchain

"""
To be installed:
    Flask==0.12.2: pip install Flask==0.12.2
        - Use Anaconda Prompt
    Postman HTTP Client: https://www.getpostman.com/
    requests==2.18.4: pip install requests==2.18.4
"""

# Import libraries
import datetime
import hashlib # To hash blocks
import json # To encode blocks before hashing
from flask import Flask, jsonify, request # Web application portion
# New imports
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Part 1 - Building a Blockchain

class Blockchain:
    """
    Class for forming and adding to a blockchain.
    
    Attr:
        chain - list containing blocks in the blockchain
        transactions - list of transactions completed
        nodes - list of nodes in network
    """
    
    def __init__(self):
        """
        Blockchain constructor. Form empty chain and create genesis block.
        
        :return: None
        """
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
        
     
    def create_block(self, proof, previous_hash):
        """
        Create a block with the given proof and previoush hash and append it to the blockchain.
        
        :param proof: proof of work for the block
        :param previous_hash: hash of the previous block in the chain
        :return: block as a dict
        """
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block
    
    
    def get_previous_block(self):
        """
        Grab the last block in the blockchain
        
        :return: last block
        """
        return self.chain[-1]
    
    
    def proof_of_work(self, previous_proof):
        """
        Generate the proof of work given an older proof of work.
        The "mining" method. Loop until proof (nonce) ends up with 
        four leading 0's in the resulting hash.
        
        :param previous_proof: proof of work of the previous block
        :return: new proof of work
        """
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
            
    
    def hash(self, block):
        """
        Hash the given block using SHA-256
        
        :param block: block in blockchain
        :return: encoded version of block
        """
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    
    def is_chain_valid(self, chain):
        """
        Loop through chain, make sure hashes match correctly.
        
        :param chain: blockchain to verify
        :return: boolean, true if chain is valid, false otherwise
        """
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            # Check that prev hash matches hash of previous block
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            
            # Check that proof (hash) of each block is valid 
            # (starts with four leading 0's) by recomputing hash
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()

            if hash_operation[:4] != '0000':
                return False
            
            previous_block = block
            block_index += 1
            
        return True
    
    def add_transaction(self, sender, receiver, amount):
        """
        Add transaction to the end of the list
        
        :param sender: person who is sending RT
        :param receiver: person who is receiving RT
        :param amount: amount of RT being transferred
        :return: int, index of the added block on the transactions list
        """
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount})
            
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self, address):
        """
        Add node with address to nodes list
        
        :param address: url address to extract
        """
        parsed_url = urlparse(address)  # Use urlib.parse import to parse given url
        self.nodes.add(parsed_url.netloc) 
        
    def replace_chain(self):
        """
        Replace the current "main" chain.
        """
        network = self.nodes 
        longest_chain = None
        max_length = len(self.chain)
        
        # Find length of nodes and compare with current length
        for node in network:
            # Take advantage of get_chain method below
            response = requests.get(f'http://{node}/get_chain')
            
            # IF response succeeded, get length and replace current chain if node's chain is longer
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
                    
        if longest_chain:
            self.chain = longest_chain
            return True
            
            
            
            
# Part 2 - Mining our Blockchain
# Creating a Flask-based Web App
# For more Flask info, search for "Flask quickstart"
app = Flask(__name__)

# Creating an address for the node on Port 5000
# Use uuid import here
node_address = str(uuid4()).replace('-', '')
    
# Creating a Blockchain instance
blockchain = Blockchain()

# Mining a new block
# Use Flask to interact with web
# Send GET request
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    """
    Mine and add a new block to the blockchain.
    
    :return: JSON object containing info on new block and 200 HTTP response code
    """
    # Get proof and previous_hash for the new block
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block) #Error (fixed)
    blockchain.add_transaction(sender = node_address, receiver = 'Brandon', amount = 1)
    
    # Create new block
    block = blockchain.create_block(proof, previous_hash)
    
    # Display block in Postman
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    
    # 200 represents a successful HTTP response
    return jsonify(response), 200


# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    """
    Jsonify chain information and send it out in GET request
    
    :return: JSON object, HTTP response code
    """
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    
    # 200 represents a successful HTTP response
    return jsonify(response), 200

# Check that chain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    """
    Confirm that the chain has not been tampered with.
    
    :return: JSON object, HTTP response code
    """
    valid_chain = blockchain.is_chain_valid(blockchain.chain)
    
    if valid_chain is False:
        message = 'Chain has been tampered with'
    else:
        message = 'Chain is valid'
        
    response = {'message': message,
                'is_valid': valid_chain}
    return jsonify(response), 200

# Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    """
    Adding a new transaction to the Blockchain
    
    :return: JSON object, HTTP response code
    """
    json = request.get_json()  # Put JSON file in Postman
    
    transaction_keys = ['sender', 'receiver', 'amount']
    
    # Error for missing keys
    if not all (key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'This transaction will be added to Block {index}'}
    return jsonify(response), 201

# Part 3 - Decentralizing the blockchain

# Connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    """
    Connect a node to the node network
    
    :return: JSON object, HTTP response code
    """
    json = request.get_json()
    nodes = json.get('nodes')
    
    # Make sure there are nodes
    if nodes is None:
        return "No nodes", 400
    
    for node in nodes:
        blockchain.add_node(node)
    
    response = {'message': 'All of the nodes are now connected. The RT Blockchain now contains the following nodes: ',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    """
    Replace the chain, a longer chain has been found
    
    :return: JSON object, HTTP response code
    """
    is_chain_replaced = blockchain.replace_chain()
    
    if is_chain_replaced is True:
        message = 'The nodes had different chains so the chain was replaced by the longer one.'
    else:
        message = 'All good. The chain is the largest one.'
        
    response = {'message': message,
                'chain': blockchain.chain}
    
    return jsonify(response), 200

# Running the app
# host = '0.0.0.0' to make server publicly available
# When running the app, go to File explorer and navigate to folder where code is located
# 1) Open Postman program
# 2) Choose GET request near top
# 3) Enter request URL:  http://127.0.0.1:5000/get_chain
# 4) Hit Send button
# 5) Enter request URL:  http://127.0.0.1:5000/mine_block
# 6) Hit Send button
app.run(host = '0.0.0.0', port = 5000)