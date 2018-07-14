"""
    配置文件
    config.py 是初始化 Flask app 的配置文件,当创建一个 app 时,将选择一种配置进行初始化
    项目用到的全局变量也写在这个文件中,主要包括多种模式下的配置类型和全局参数（如密钥、连接数据库的 URL）等
"""
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # 此处定义全局变量
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'zl12345678'  # 设置密钥，可能会用在某些涉及到加解密的功能中
    SQLALCHEMY_TRACK_MODIFICATIONS = True                      # 该项不设置为True的话可能会导致数据库报错

    # 处理结果缓存路径
    RESULT_PATH = 'static/upload/result/'
    RESULT_FOLDER = os.path.join(basedir, 'APP/', RESULT_PATH)

    VIDEO_PATH = os.path.join(basedir, 'APP/', 'static/upload/video/')

    # 安全设置
    SSL_DISABLE = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True

    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    FLASKY_SLOW_DB_QUERY_TIME = 0.5

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    # 连接测试环境数据库的URL
    SQLALCHEMY_DATABASE_URI = (os.environ.get('DEV_DATABASE_URL') or
                               'mysql://root:2018@localhost/faceswap_dev')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = (os.environ.get('DEV_DATABASE_URL') or
                               'mysql://root:2018@localhost/faceswap_test')
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    # 连接生产环境数据库的URL
    SQLALCHEMY_DATABASE_URI = (os.environ.get('DEV_DATABASE_URL') or
                               'mysql://root:2018@localhost/faceswap_pro')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
