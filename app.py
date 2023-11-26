from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()


def create_app():
    app = Flask(__name__)

    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_server = os.getenv("DB_SERVER")
    db_name = os.getenv("DB_NAME")

    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = f"mysql://{db_user}:{db_pass}@{db_server}/{db_name}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = (
        os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS") == "True"
    )
    app.secret_key = os.getenv("SECRET_KEY")

    return app
