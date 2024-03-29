from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
import pymysql
pymysql.install_as_MySQLdb()
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
csrf = CSRFProtect()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    csrf.init_app(app)

    from .main import video as video_blueprint
    app.register_blueprint(video_blueprint, url_prefix='/video')

    return app
