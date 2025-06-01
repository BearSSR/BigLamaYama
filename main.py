from flask import Flask, jsonify
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import os

app = Flask(__name__)

def fetch_polymarket_data():
    transport = RequestsHTTPTransport(
        url="https://api.thegraph.com/subgraphs/name/Polymarket/polymarket"
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    query = gql("""
    {
      markets(first: 20, orderBy: volume, orderDirection: desc) {
        id
        question
        outcomes {
          name
          price
        }
      }
    }
    """)

    result = client.execute(query)
    return result.get('markets', [])

def detect_arbitrage(markets):
    opportunities = []
    for market in markets:
        outcomes = market.get('outcomes', [])
        if len(outcomes) == 2:
            try:
                yes = float(outcomes[0]['price'])
                no = float(outcomes[1]['price'])
                combined = yes + no

                if combined < 0.995:
                    arb = {
                        "market": market['question'],
                        "yes": yes,
                        "no": no,
                        "combined": round(combined, 4),
                        "recommendation": f"Bet proportionally on YES/NO to lock profit (YES {round(yes * 100)}%, NO {round(no * 100)}%)"
                    }
                    opportunities.append(arb)
            except (KeyError, ValueError, TypeError):
                continue
    return opportunities

@app.route('/')
def root():
    return jsonify({
        "endpoint": "/arbs",
        "message": "Polymarket Arbitrage Detector API"
    })

@app.route('/arbs')
def get_arbs():
    try:
        markets = fetch_polymarket_data()
        arbs = detect_arbitrage(markets)
        return jsonify(arbs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

