from flask import Flask, make_response
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)

class Welcome(Resource):
    def get(self):
        response_message = {
            "message": "WELCOME TO MEALY API."
        }
        return make_response(response_message, 200)

api.add_resource(Welcome, '/')

if __name__ == '__main__':
    app.run(debug=True, port=5555)
