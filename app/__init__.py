import os
from flask import Flask, jsonify, request
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
    
    # İzin verilen originler listesi - frontend uygulamanızın URL'sini buraya ekleyin
    allowed_origins = [
        'http://localhost:3000',  # Yerel geliştirme için
        'http://localhost:5000',  # Yerel geliştirme için
        'http://127.0.0.1:5000',  # Yerel geliştirme için (alternatif)
        'https://faceattendancesystemfrontend.vercel.app',  # Vercel'de deploy edilmiş frontend
        'https://your-frontend-domain.com',  # Frontend uygulamanızın domain'i
        # Diğer izin verilen domainleri buraya ekleyin
    ]
    
    # CORS desteği ekle - belirli domainlere izin ver
    CORS(app, 
         resources={
             r"/*": {
                 "origins": allowed_origins,
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Credentials"]
             },
             r"/api/admin/public-upgrade-db": {
                 "origins": "*",  # Bu endpoint için tüm originlere izin ver
                 "methods": ["GET", "POST", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Credentials"]
             }
         }, 
         supports_credentials=True)
    
    # CORS ön uçuş isteklerini ele al
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        # Eğer origin izin verilen listede ise, o origin'i header'a ekle
        if origin and origin in allowed_origins:
            response.headers.set('Access-Control-Allow-Origin', origin)
            response.headers.set('Access-Control-Allow-Credentials', 'true')
            response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, Access-Control-Allow-Credentials')
            response.headers.set('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
        # Eğer /api/admin/public-upgrade-db endpoint'i için istek geliyorsa, tüm originlere izin ver
        elif request.path.startswith('/api/admin/public-upgrade-db'):
            response.headers.set('Access-Control-Allow-Origin', '*')
            response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, Access-Control-Allow-Credentials')
            response.headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        # Diğer durumlarda, varsayılan olarak ilk izin verilen origin'i kullan
        elif allowed_origins:
            response.headers.set('Access-Control-Allow-Origin', allowed_origins[0])
            response.headers.set('Access-Control-Allow-Credentials', 'true')
            response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, Access-Control-Allow-Credentials')
            response.headers.set('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
            
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
        # Geçersiz token hatası için uygun bir JSON yanıtı döndür
        return jsonify({
            'status': 'error',
            'message': 'Geçersiz token',
            'error': str(error_string)
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        # Eksik token hatası için uygun bir JSON yanıtı döndür
        return jsonify({
            'status': 'error',
            'message': 'Eksik token',
            'error': str(error_string)
        }), 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        # Süresi dolmuş token hatası için uygun bir JSON yanıtı döndür
        return jsonify({
            'status': 'error',
            'message': 'Süresi dolmuş token',
            'error': 'Token süresi dolmuş'
        }), 401
    
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
        origin = request.headers.get('Origin')
        response = jsonify({'status': 'ok'})
        
        # Eğer origin izin verilen listede ise, o origin'i header'a ekle
        if origin and origin in allowed_origins:
            response.headers.set('Access-Control-Allow-Origin', origin)
        # Eğer /api/admin/public-upgrade-db endpoint'i için istek geliyorsa, tüm originlere izin ver
        elif path.startswith('api/admin/public-upgrade-db'):
            response.headers.set('Access-Control-Allow-Origin', '*')
        # Diğer durumlarda, varsayılan olarak ilk izin verilen origin'i kullan
        elif allowed_origins:
            response.headers.set('Access-Control-Allow-Origin', allowed_origins[0])
            
        response.headers.set('Access-Control-Allow-Credentials', 'true')
        response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, Access-Control-Allow-Credentials')
        response.headers.set('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
        return response
    
    return app 