from flask import Flask, request, jsonify, Response
import requests
import json

app = Flask(__name__)

# Your QuickNode endpoint with GoldRush Wallet API enabled
QUICKNODE_URL = "https://wandering-light-bird.quiknode.pro/0bec0c052dd2b98f5aa131b2c62e7290d2e28a39/"

HEADERS = {
    "Content-Type": "application/json"
}

@app.route('/query-wallets', methods=['POST'])
def query_wallets():
    data = request.get_json()
    wallet_addresses = data.get("wallets", [])
    token_symbol_filter = data.get("token_symbol")
    min_token_value = data.get("min_token_value", 0)

    if not wallet_addresses:
        return jsonify({"error": "No wallet addresses provided"}), 400

    results = {}

    for address in wallet_addresses:
        eth_payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"]
        }
        eth_response = requests.post(QUICKNODE_URL, headers=HEADERS, json=eth_payload)
        eth_balance = 0.0
        if eth_response.status_code == 200:
            eth_result = eth_response.json().get("result")
            if eth_result:
                eth_balance = int(eth_result, 16) / (10 ** 18)

        payload = {
            "id": 2,
            "jsonrpc": "2.0",
            "method": "qn_getWalletTokenBalances",
            "params": [{
                "wallet": address,
                "omitMetadata": False
            }]
        }

        response = requests.post(QUICKNODE_URL, headers=HEADERS, json=payload)

        if response.status_code == 200:
            tokens = response.json().get("result", {}).get("assets", [])
            filtered_tokens = []
            total_usd = 0

            eth_price_usd = fetch_eth_usd_price()
            eth_quote = eth_balance * eth_price_usd
            if eth_quote > min_token_value:
                filtered_tokens.append({
                    "symbol": "ETH",
                    "balance": eth_balance,
                    "quote_usd": eth_quote
                })
                total_usd += eth_quote

            for token in tokens:
                symbol = token.get("assetSymbol")
                quote = float(token.get("value", 0))
                if quote > min_token_value and (not token_symbol_filter or symbol == token_symbol_filter):
                    filtered_tokens.append({
                        "symbol": symbol,
                        "balance": token.get("amount"),
                        "quote_usd": quote
                    })
                    total_usd += quote

            results[address] = {
                "total_value_usd": round(total_usd, 2),
                "tokens": filtered_tokens
            }
        else:
            results[address] = {"error": f"Failed to fetch data for {address}"}

    return jsonify(results)

def fetch_eth_usd_price():
    return 3000.0

@app.route('/contract-engagers', methods=['POST'])
def contract_engagers():
    data = request.get_json()
    contract_address = data.get("contract_address")

    if not contract_address:
        return jsonify({"error": "Contract address is required"}), 400

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "qn_getTransactionsByAddress",
        "params": [
            {
                "address": contract_address,
                "page": 1,
                "perPage": 100,
                "direction": "both"
            }
        ]
    }

    response = requests.post(QUICKNODE_URL, headers=HEADERS, json=payload)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch contract transactions"}), 500

    txs = response.json().get("result", {}).get("transactions", [])
    from_wallets = {tx.get("from") for tx in txs if tx.get("from")}

    return jsonify(sorted(from_wallets))

@app.route('/wallet-nfts', methods=['POST'])
def wallet_nfts():
    data = request.get_json()
    wallet_address = data.get("wallet_address")

    if not wallet_address:
        return jsonify({"error": "Wallet address is required"}), 400

    nfts_collected = []
    for page in range(1, 3):  # Try pages 1 and 2
        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "qn_fetchNFTsByOwner",
            "params": [
                {
                    "wallet": wallet_address,
                    "perPage": 50,  # You can adjust to 100 if you prefer
                    "page": page
                }
            ]
        }

        response = requests.post(QUICKNODE_URL, headers=HEADERS, json=payload)

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch wallet NFTs"}), 500

        page_nfts = response.json().get("result", {}).get("assets", [])
        nfts_collected.extend(page_nfts)

        if len(page_nfts) == 0:
            break  # Stop early if no NFTs on current page

    if not nfts_collected:
        return jsonify({"message": "No NFTs found for this wallet."})

    return jsonify(nfts_collected)


@app.route('/token-holders', methods=['POST'])
def token_holders():
    data = request.get_json()
    token_address = data.get("token_address")

    if not token_address:
        return jsonify({"error": "Token address is required"}), 400

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "qn_getTokenHolders",
        "params": [{
            "contract": token_address
        }]
    }

    response = requests.post(QUICKNODE_URL, headers=HEADERS, json=payload)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch token holders"}), 500

    holders = response.json().get("result", {}).get("holders", [])

    return jsonify(holders)

@app.route('/openapi.json', methods=['GET'])
def openapi():
    openapi_spec = { ... }  # Use the latest openapi.json structure we prepared
    return Response(
        response=json.dumps(openapi_spec),
        status=200,
        mimetype='application/json'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
