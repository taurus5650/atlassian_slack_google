import os


class Config:
    DEBUG = False
    PORT = 8790


class DevelopmentConfig(Config):
    DEBUG = True


class FlaskSecretKey:
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
