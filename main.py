from flask import Flask, jsonify
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

app = Flask(__name__)

def fetch_polymarket_data():
    transport = RequestsHTTPTransport(
        url="https://gateway.thegraph.com/api/be264eb9877d02a1d003ae8d2c650741/subgraphs/id/81Dm16JjuFSrqz813HysXoUPvzTwE7fsfPk2RTf66nyC",
        verify=True,
        retries=3
    )
    client = Client(transport=transport, fetch_schema_from_transport=False)

    query = gql("""
    {
      conditions(first: 10) {
        id
        oracle
        questionId
        outcomeSlotCount
      }
    }
    """)

    result = client.execute(query)
    return result['conditions']

@app.route('/')
def root():
    return jsonify({
        "endpoint": "/arbs",
        "message": "Polymarket Arbitrage API - Now operational ✅"
    })

@app.route('/arbs')
def get_arbs():
    try:
        markets = fetch_polymarket_data()
        return jsonify(markets)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)



