from flask import Flask, request, jsonify, Response
import requests
import json
import os

app = Flask(__name__)

# Your QuickNode endpoint with GoldRush Wallet API enabled
QUICKNODE_URL = os.getenv("QUICKNODE_URL")

HEADERS = {
    "Content-Type": "application/json"
}

@app.route('/wallet-nfts', methods=['POST'])
def wallet_nfts():
    data = request.get_json()
    wallet_address = data.get("wallet_address")

    if not wallet_address:
        return jsonify({"error": "Wallet address is required"}), 400

    # Try QuickNode
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "qn_fetchNFTsByOwner",
        "params": [
            {
                "wallet": wallet_address,
                "perPage": 50,
                "page": 1
            }
        ]
    }
    quicknode_response = requests.post(QUICKNODE_URL, headers=HEADERS, json=payload)

    if quicknode_response.status_code == 200:
        quicknode_nfts = quicknode_response.json().get("result", {}).get("assets", [])
        if not quicknode_nfts:
            return jsonify({"message": "No NFTs found for this wallet."})
        limited_quicknode_nfts = quicknode_nfts[:10]
        return jsonify(limited_quicknode_nfts)
    else:
        return jsonify({"error": "Failed to fetch NFTs from QuickNode."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
