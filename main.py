from flask import Flask, jsonify
import requests

app = Flask(__name__)

def fetch_market_data():
    try:
        response = requests.get("https://gamma-api.polymarket.com/markets")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": f"Error fetching market data: {e}"}

def detect_arbitrage(markets):
    opportunities = []
    for market in markets:
        outcomes = market.get("outcomes", [])
        prices = market.get("outcomePrices", [])
        if len(outcomes) == 2 and len(prices) == 2:
            try:
                price_yes = float(prices[0])
                price_no = float(prices[1])
                total = price_yes + price_no
                if total < 1.0:
                    opportunity = {
                        "question": market.get("question", "N/A"),
                        "marketId": market.get("id", "N/A"),
                        "conditionId": market.get("conditionId", "N/A"),
                        "outcomes": outcomes,
                        "yes_price": price_yes,
                        "no_price": price_no,
                        "total": total,
                        "arbitrage_margin": round((1.0 - total) * 100, 2),
                        "recommendation": f"Split stake: YES {round((1 - price_no / total) * 100)}%, NO {round((1 - price_yes / total) * 100)}%"
                    }
                    opportunities.append(opportunity)
            except (ValueError, TypeError):
                continue
    return opportunities

@app.route('/')
def root():
    return jsonify({
        "endpoint": "/arbs",
        "message": "Polymarket Arbitrage API - Powered by Gamma ✅"
    })

@app.route('/arbs')
def get_arbs():
    data = fetch_market_data()
    if isinstance(data, dict) and "error" in data:
        return jsonify(data), 500
    arbs = detect_arbitrage(data)
    return jsonify(arbs)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)


