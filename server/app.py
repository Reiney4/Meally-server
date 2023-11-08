from flask import Flask

app = Flask(__name__)

# Define the route for the welcome message
@app.route('/')
def welcome():
    return "Welcome to Mealy!"

if __name__ == '__main__':
    app.run(debug=True)
