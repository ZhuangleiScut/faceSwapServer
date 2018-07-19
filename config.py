import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'zl12345678'
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    RESULT_PATH = 'static/upload/result/'
    RESULT_FOLDER = os.path.join(basedir, 'app/static/uploads/result/')

    VIDEO_PATH = os.path.join(basedir, 'app/static/upload/video/')
    IMAGE_PATH = os.path.join(basedir, 'app/static/upload/image/')

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


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
