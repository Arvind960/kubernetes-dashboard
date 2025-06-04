import os
import time
from flask import Flask, render_template, jsonify, send_file

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('simple.html')

@app.route('/api/data')
def get_data():
    # Define namespaces based on kubectl get ns output
    namespaces = [
        {'name': 'datadog', 'status': 'Active', 'age': '15d', 'pods': 2, 'services': 7},
        {'name': 'default', 'status': 'Active', 'age': '18d', 'pods': 0, 'services': 1},
        {'name': 'kube-node-lease', 'status': 'Active', 'age': '18d', 'pods': 0, 'services': 0},
        {'name': 'kube-public', 'status': 'Active', 'age': '18d', 'pods': 0, 'services': 0},
        {'name': 'kube-system', 'status': 'Active', 'age': '18d', 'pods': 18, 'services': 2},
        {'name': 'nginx', 'status': 'Active', 'age': '2d7h', 'pods': 1, 'services': 1},
        {'name': 'prod', 'status': 'Active', 'age': '18d', 'pods': 8, 'services': 0}
    ]
    
    return jsonify({
        'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
        'namespaces': namespaces
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8889)
