from flask import Flask, jsonify
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

app = Flask(__name__)

# Setup the GraphQL client
transport = RequestsHTTPTransport(
    url="https://gateway.thegraph.com/api/be264eb9877d02a1d003ae8d2c650741/subgraphs/id/81Dm16JjuFSrqz813HysXoUPvzTwE7fsfPk2RTf66nyC",
    verify=True,
    retries=3,
)
client = Client(transport=transport, fetch_schema_from_transport=False)

# Query outcome token prices and metadata
def fetch_polymarket_prices():
    query = gql("""
    {
      outcomeTokenPrices(first: 30, orderBy: price, orderDirection: desc) {
        id
        price
        outcomeSlot
        condition {
          id
          questionId
        }
      }
    }
    """)
    result = client.execute(query)
    return result["outcomeTokenPrices"]

# Detect arbitrage by grouping YES/NO prices by condition
def detect_arbitrage(tokens):
    condition_map = {}

    for token in tokens:
        condition_id = token["condition"]["id"]
        if condition_id not in condition_map:
            condition_map[condition_id] = {
                "questionId": token["condition"]["questionId"],
                "outcomes": {}
            }

        slot = int(token["outcomeSlot"])
        price = float(token["price"])
        condition_map[condition_id]["outcomes"][slot] = price

    arbs = []
    for condition_id, data in condition_map.items():
        outcomes = data["outcomes"]
        if 0 in outcomes and 1 in outcomes:
            yes = outcomes[0]
            no = outcomes[1]
            total = yes + no
            if total < 0.995:
                arbs.append({
                    "conditionId": condition_id,
                    "questionId": data["questionId"],
                    "yes": yes,
                    "no": no,
                    "total": round(total, 4),
                    "profit_margin": round((1 - total) * 100, 2),
                    "suggestion": f"YES {round((no / total) * 100)}%, NO {round((yes / total) * 100)}%"
                })

    return arbs

@app.route('/')
def root():
    return jsonify({
        "endpoint": "/arbs",
        "message": "Polymarket Arbitrage API - Now operational ✅"
    })

@app.route('/arbs')
def get_arbs():
    try:
        tokens = fetch_polymarket_prices()
        arbs = detect_arbitrage(tokens)
        return jsonify(arbs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
