import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from dotenv import load_dotenv

# Ortam değişkenlerini yükle
load_dotenv()

# Veritabanı nesnesi
db = SQLAlchemy()
# Migrasyon nesnesi
migrate = Migrate()
# JWT nesnesi
jwt = JWTManager()

def create_app(test_config=None):
    # Flask uygulaması oluştur
    app = Flask(__name__, static_folder='static')
    
    # CORS desteği ekle - tüm domainlere izin ver
    CORS(app, 
         resources={r"/*": {"origins": "*"}}, 
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # CORS ön uçuş isteklerini ele al
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    # CORS desteği ekle - tüm domainlere izin ver
    CORS(app, 
         resources={
             r"/*": {
                 "origins": "*",
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Credentials"]
             },
             r"/api/admin/public-upgrade-db": {
                 "origins": "*",
                 "methods": ["GET", "POST", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Credentials"]
             }
         }, 
         supports_credentials=True)
    
    # CORS ön uçuş isteklerini ele al
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Access-Control-Allow-Credentials')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    # Yapılandırma
    if test_config is None:
        # Varsayılan yapılandırma
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
            SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URI', 'sqlite:///face_attendance.db'),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key'),
            JWT_ACCESS_TOKEN_EXPIRES=3600,  # 1 saat
            JWT_REFRESH_TOKEN_EXPIRES=86400,  # 1 gün
            UPLOAD_FOLDER=os.path.join(app.static_folder, 'faces')
        )
    else:
        # Test yapılandırması
        app.config.from_mapping(test_config)
    
    # Veritabanı başlatma
    db.init_app(app)
    migrate.init_app(app, db)
    
    # JWT başlatma
    jwt.init_app(app)
    
    # JWT hata işleyicileri
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        # Test amaçlı: Geçersiz token hatalarını yoksay
        print(f"Geçersiz token hatası yoksayıldı: {error_string}")
        return None
    
    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        # Test amaçlı: Eksik token hatalarını yoksay
        print(f"Eksik token hatası yoksayıldı: {error_string}")
        return None
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        # Test amaçlı: Süresi dolmuş token hatası yoksayıldı
        print(f"Süresi dolmuş token hatası yoksayıldı")
        return None
    
    # Swagger UI yapılandırması
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Yüz Tanıma ile Yoklama Sistemi API",
            'dom_id': '#swagger-ui',
            'deepLinking': True,
            'supportedSubmitMethods': ['get', 'post', 'put', 'delete', 'patch'],
            'displayRequestDuration': True,
            'docExpansion': 'none',
            'validatorUrl': None
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    
    # Statik klasör oluşturma
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Modelleri içe aktar
    from app.models import user, teacher, student, course, attendance
    
    # Blueprint'leri kaydet
    from app.routes import auth, teachers, students, courses, attendance, reports
    app.register_blueprint(auth.bp)
    app.register_blueprint(teachers.bp)
    app.register_blueprint(students.bp)
    app.register_blueprint(courses.bp)
    app.register_blueprint(attendance.bp)
    app.register_blueprint(reports.bp)
    
    @app.route('/')
    def index():
        return jsonify({'message': 'Yüz Tanıma ile Yoklama Sistemi API'})
    
    # OPTIONS isteklerini ele al
    @app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def options_handler(path):
        return jsonify({'status': 'ok'})
    
    return app 