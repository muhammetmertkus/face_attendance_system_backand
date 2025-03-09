import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Temel yapılandırma sınıfı"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    
    # MySQL bağlantısı için bağlantı URL'si oluştur
    # Railway'den gelen MySQL ortam değişkenlerini kullan
    DB_USER = os.environ.get('MYSQLUSER')
    DB_PASSWORD = os.environ.get('MYSQLPASSWORD')
    DB_HOST = os.environ.get('MYSQLHOST')
    DB_PORT = os.environ.get('MYSQLPORT')
    DB_NAME = os.environ.get('MYSQLDATABASE')
    
    # Eğer MySQL bilgileri varsa MySQL kullan, yoksa SQLite'a geri dön
    if DB_USER and DB_PASSWORD and DB_HOST and DB_PORT and DB_NAME:
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///face_attendance.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 saat
    JWT_REFRESH_TOKEN_EXPIRES = 86400  # 1 gün
    UPLOAD_FOLDER = 'app/static/faces'

class DevelopmentConfig(Config):
    """Geliştirme ortamı yapılandırması"""
    DEBUG = True

class TestingConfig(Config):
    """Test ortamı yapılandırması"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'

class ProductionConfig(Config):
    """Üretim ortamı yapılandırması"""
    DEBUG = False
    TESTING = False

# Yapılandırma sözlüğü
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 