from flask import Flask, request, jsonify
from functools import wraps
import jwt
import logging
from src.config import Config
from src.workflow import WorkflowManager

logging.basicConfig(level=logging.INFO)

def create_app():
    app = Flask(__name__)
    workflow = WorkflowManager()

    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'message': 'Token missing'}), 401
            try:
                if 'Bearer ' in token: token = token.split(' ')[1]
                jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
            except Exception:
                return jsonify({'message': 'Invalid token'}), 401
            return f(*args, **kwargs)
        return decorated

    @app.route('/webhook/3a386c57-e834-4b90-81d9-02ddf5bb027d', methods=['POST'])
    @token_required
    def n8n_webhook():
        try:
            result = workflow.run(request.json)
            return jsonify({
                "status": "success",
                "analysis": result
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app
