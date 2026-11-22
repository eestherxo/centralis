from datetime import timedelta
import os

from flask import Flask
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from app.routes.resources import inventory_bp
from app.routes.visitors import visitors_bp
from app.routes.auth import auth_bp

load_dotenv()

app = Flask(__name__)

jwt_secret = os.getenv("JWT_SECRET_KEY")

app.config.update(
    JWT_SECRET_KEY=jwt_secret,
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=60)
)

JWTManager(app)

app.register_blueprint(inventory_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(visitors_bp)

if __name__ == "__main__":
    app.run(debug=True)
