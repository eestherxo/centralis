from datetime import timedelta
import os
import click

from flask import Flask
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from app.routes.resources import inventory_bp
from app.routes.visitors import visitors_bp
from app.routes.auth import auth_bp
from app.routes.reports import reports_bp
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

app.register_blueprint(inventory_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(visitors_bp)
app.register_blueprint(reports_bp)



# CLI to create root admin 
@app.cli.command("create-first-admin")
def create_first_admin():
    if any(
        user.get("role") == Role.ADMIN.value
        for user in data_access.get_all_records("user")
    ):
        raise click.ClickException(
            "An admin already exists. Use the authenticated /auth/users endpoint."
        )

    name = click.prompt("Name", default="Root Admin")
    email = click.prompt("Email")
    password = click.prompt(
        "Password",
        hide_input=True,
        confirmation_prompt=True,
    )

    user, status = create_user({
        "name": name,
        "email": email,
        "password": password,
        "role": Role.ADMIN.value,
    })

    if status != 201:
        raise click.ClickException(user["error"])

    click.echo(f"Created admin account for {user['email']}")

if __name__ == "__main__":
    app.run(debug=True)
