from flask import Flask, request, jsonify
import requests

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
        payload = {
            "id": 1,
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
            for token in tokens:
                symbol = token.get("assetSymbol")
                quote = float(token.get("value", 0))  # Use value in USD if available
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
