import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Temel yapılandırma sınıfı"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    
    # Veritabanı bağlantı URL'sini belirle
    # 1. Önce DATABASE_URI ve DATABASE_URL ortam değişkenlerini kontrol et
    # 2. Eğer bunlar yoksa, PostgreSQL bağlantı parametrelerini kullan
    # 3. Eğer bu değişkenler de yoksa, varsayılan SQLite veritabanını kullan
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or os.environ.get('DATABASE_URL')
    
    # Eğer DATABASE_URI ve DATABASE_URL yoksa, PostgreSQL bağlantı parametrelerini kullan
    if not SQLALCHEMY_DATABASE_URI:
        pg_user = os.environ.get('PGUSER') or os.environ.get('POSTGRES_USER')
        pg_password = os.environ.get('PGPASSWORD') or os.environ.get('POSTGRES_PASSWORD')
        pg_host = os.environ.get('PGHOST')
        pg_port = os.environ.get('PGPORT', '5432')
        pg_database = os.environ.get('PGDATABASE') or os.environ.get('POSTGRES_DB')
        
        if pg_user and pg_password and pg_host and pg_database:
            SQLALCHEMY_DATABASE_URI = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
    
    # Eğer hala SQLALCHEMY_DATABASE_URI yoksa, varsayılan SQLite veritabanını kullan
    if not SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///face_attendance.db'
    
    # PostgreSQL URL'si 'postgres://' ile başlıyorsa 'postgresql://' ile değiştir
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # Dışarıdan erişim için public veritabanı URL'si (eğer varsa)
    DATABASE_PUBLIC_URL = os.environ.get('DATABASE_PUBLIC_URL')
    
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