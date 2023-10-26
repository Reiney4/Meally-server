from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/welcome', methods=['GET'])
def welcome():
    response = {
        'message': 'Welcome to Mealy!',
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
