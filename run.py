from flask import Flask
from app.routes.resources import inventory_bp
from app.routes.visitors import visitors_bp

app = Flask(__name__)


app.register_blueprint(inventory_bp, url_prefix="/inventory")
app.register_blueprint(visitors_bp)

if __name__ == "__main__":
    app.run(debug=True)
