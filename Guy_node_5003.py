# Module 1 - Create a Cryptocurrency

# To be installed:
# Flask==0.12.2: pip install Flask==0.12.2
# Postman HTTP Client: https://www.getpostman.com/

# Importing the libraries
# requests==2.18.4
import datetime
import hashlib
import json
from uuid import uuid4

import requests
from flask import Flask, jsonify, request
from urllib.parse import urlparse

# Part 1 - Building a Blockchain


class Blockchain:

    def __init__(self):
        self.chain = []
        self.transactions = []
        self.REWARD = 1.6
        self.create_block(proof=1, previous_hash='0')
        self.nodes = set()

    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'transactions': self.transactions,
                 'previous_hash': previous_hash}
        self.transactions = []  # empty any pre-added transactions
        self.chain.append(block)
        return block

    def get_latest_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    @staticmethod
    def hash(block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    def add_transaction(self, sender, receiver, amount):
        """
        Method which adds a transaction in dict type to the list of transactions
        :param sender: String
        :param receiver: String
        :param amount: Float
        :return: index of the Block that would hold the created transaction
        """
        self.transactions.append({'sender': sender, 'receiver': receiver, 'amount': amount})
        return self.get_latest_block()['index'] + 1

    def add_node(self, address):
        """
        Methods which adds a new node to the list of the Blockchain's nodes
        :param address: an IP address with a Port
        :return: dict type of error or success
        """
        parsed_url = urlparse(address)
        try:
            self.nodes.add(parsed_url.netloc)
        except Exception as e:
            return {'error': e}
        return {'message': 'Node added successfully'}

    def replace_chain(self):
        """
        Method that replaces a node's chain by the longest chain available of the Blockchain
        :return: Boolean: True if a longer chain in the network ws found and replaced current chain,
        False otherwise
        """
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)  # The chain of the Blockchain inside the node that would be replaced if
        # a longer chain was found
        for node in network:
            #  Nodes in our network are differentiated by their IP and Port
            get_chain_response = requests.get(f'http://{node}/get_chain')
            if get_chain_response.status_code == 200:
                length = get_chain_response.json()['length']
                chain = get_chain_response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False


# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__)

# Creating an address for the node on Port 5003
node_address = str(uuid4()).replace('-', '')

# Creating a Blockchain
blockChain = Blockchain()

# Mining a new block


@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockChain.get_latest_block()
    previous_proof = previous_block['proof']
    proof = blockChain.proof_of_work(previous_proof)
    previous_hash = blockChain.hash(previous_block)
    blockChain.add_transaction(node_address, 'GuyG', blockChain.REWARD)
    block = blockChain.create_block(proof, previous_hash)
    #  Adding the Coinbase transaction
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200


# Getting the full Blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': blockChain.chain,
                'length': len(blockChain.chain)}
    return jsonify(response), 200


# Checking if the Blockchain is valid
@app.route('/is_valid', methods=['GET'])
def is_valid():
    valid_flag = blockChain.is_chain_valid(blockChain.chain)
    if valid_flag:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'Houston, we have a problem. The Blockchain is not valid.'}
    return jsonify(response), 200


@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockChain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'One or more nodes replaced their chain', 'new_chain': blockChain.chain}
    else:
        response = {'message': 'No chain was replaced'}
    return jsonify(response), 200


# Adding a new transactions to the Blockchain
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    """
    This method will be invoked using a json file which contains a bulk of transaction dict-objects
    :return: # of new transactions
    """
    body = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in body for key in transaction_keys):
        return jsonify('Invalid Transactions Headers', 400)
    index = blockChain.add_transaction(body[transaction_keys[0]], body[transaction_keys[1]], body[transaction_keys[2]])
    response = {'message': f'Transation will be added to Block {index}'}
    return jsonify(response, 201)

# Connecting new nodes


@app.route('/connect_node', methods = ['POST'])
def connect_node():
    body = request.get_json()
    nodes = body.get('nodes', None)  # Excepts the address of the node
    if nodes:
        for node in nodes:
            blockChain.add_node(node)
        response = {'message': 'all nodes are connected', 'all_nodes': list(blockChain.nodes)}
        return jsonify(response, 200)
    return jsonify('No nodes specified', 400)


# Running the app
app.run(host='0.0.0.0', port=5003)

# Part 3 - Decentralizing our Blockchain



