"""
    本文件是项目本身的构造文件
    主要包括创建 flask app 的工厂函数
    配置 Flask 扩展插件时往往在工厂函数中对 app 进行相关的初始化。
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
import pymysql
pymysql.install_as_MySQLdb()

db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)

    # 注册路由
    from .video import video as video_blueprint
    app.register_blueprint(video_blueprint, url_prefix='/video')

    return app
