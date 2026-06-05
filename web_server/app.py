# web_server/app.py
from flask import Flask
from routes.view_routes import view_bp
from routes.api_routes import api_bp

app = Flask(__name__)

# 註冊藍圖 (Blueprint)
app.register_blueprint(view_bp)
app.register_blueprint(api_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)