from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/', methods=['GET'])
def root():
    return jsonify({"message": "Welcome to the Kubernetes Python App"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
