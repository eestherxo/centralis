from datetime import timedelta
import os

from flask import Flask
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from app.routes.resources import inventory_bp
from app.routes.visitors import visitors_bp
from app.routes.auth import auth_bp
from app.routes.reports import reports_bp
from app.routes.sales import sales_bp
from app.routes.reservations import reservations_bp
from app.routes.fines import fines_bp
from app.models import Role 
from app.modules.authentication import create_user
from app import data_access

load_dotenv()

app = Flask(__name__)

jwt_secret = os.getenv("JWT_SECRET_KEY")

app.config.update(
    JWT_SECRET_KEY=jwt_secret,
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=60),
)

JWTManager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(visitors_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(sales_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(reservations_bp)
app.register_blueprint(fines_bp)



if __name__ == "__main__":
    app.run()
