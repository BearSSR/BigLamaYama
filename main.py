from flask import Flask, jsonify
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

app = Flask(__name__)

def fetch_polymarket_data():
    transport = RequestsHTTPTransport(
        url="https://gateway.thegraph.com/api/be264eb9877d02a1d003ae8d2c650741/subgraphs/id/81Dm16JjuFSrqz813HysXoUPvzTwE7fsfPk2RTf66nyC",
        verify=True,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=False)

    query = gql("""
    {
      conditionMarkets(first: 20, orderBy: volumeUSD, orderDirection: desc) {
        id
        title
        outcomes {
          name
          price
        }
      }
    }
    """)

    result = client.execute(query)
    return result['conditionMarkets']

def detect_arbitrage(markets):
    opportunities = []
    for market in markets:
        if len(market['outcomes']) == 2:
            yes = float(market['outcomes'][0]['price'])
            no = float(market['outcomes'][1]['price'])
            combined = yes + no

            if combined < 0.995:
                arb = {
                    "market": market['title'],
                    "yes": yes,
                    "no": no,
                    "combined": round(combined, 4),
                    "recommendation": f"Bet proportionally on YES/NO to lock profit (YES {round(yes * 100)}%, NO {round(no * 100)}%)"
                }
                opportunities.append(arb)
    return opportunities

@app.route('/')
def root():
    return jsonify({
        "endpoint": "/arbs",
        "message": "Polymarket Arbitrage Detector API"
    })

@app.route('/arbs')
def get_arbs():
    markets = fetch_polymarket_data()
    arbs = detect_arbitrage(markets)
    return jsonify(arbs)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
