from flask import Flask, jsonify
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

app = Flask(__name__)

def fetch_conditions_with_prices():
    transport = RequestsHTTPTransport(
        url="https://gateway.thegraph.com/api/be264eb9877d02a1d003ae8d2c650741/subgraphs/id/81Dm16JjuFSrqz813HysXoUPvzTwE7fsfPk2RTf66nyC",
        verify=True,
        retries=3
    )

    client = Client(transport=transport, fetch_schema_from_transport=False)

    query = gql("""
    {
      conditions(first: 20) {
        id
        oracle
        questionId
        outcomeSlotCount
        outcomeSlot {
          indexSet
          payouts
        }
        fixedProductMarketMakers {
          id
          outcomeTokenAmounts
          outcomeTokenPrices
        }
      }
    }
    """)

    result = client.execute(query)
    return result['conditions']

def detect_arbitrage(conditions):
    opportunities = []
    for cond in conditions:
        markets = cond.get('fixedProductMarketMakers', [])
        for market in markets:
            prices = market.get('outcomeTokenPrices', [])
            if len(prices) == 2:
                yes = float(prices[0])
                no = float(prices[1])
                total = yes + no

                if total < 0.99:  # Adjust threshold as needed
                    opportunities.append({
                        "marketId": market['id'],
                        "conditionId": cond['id'],
                        "questionId": cond['questionId'],
                        "yes": yes,
                        "no": no,
                        "total": round(total, 4),
                        "recommendation": f"Bet YES: {round(yes * 100)}% / NO: {round(no * 100)}%"
                    })
    return opportunities

@app.route('/')
def index():
    return jsonify({
        "message": "Polymarket Arbitrage API ✅",
        "endpoint": "/arbs"
    })

@app.route('/arbs')
def arbs():
    try:
        data = fetch_conditions_with_prices()
        arbs = detect_arbitrage(data)
        return jsonify(arbs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)

