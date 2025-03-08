from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from app.services.auth_service import AuthService
import secrets
import datetime
from app import db
from app.models.user import User

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Şifre sıfırlama tokenlarını saklamak için geçici bir sözlük
# Gerçek uygulamada bu veritabanında saklanmalıdır
password_reset_tokens = {}

@bp.route('/register', methods=['POST'])
def register():
    """Yeni kullanıcı kaydı"""
    data = request.get_json()
    
    # Gerekli alanları kontrol et
    required_fields = ['email', 'password', 'first_name', 'last_name', 'role']
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"{field} alanı gerekli."), 400
    
    # Rol kontrolü
    valid_roles = ['admin', 'teacher', 'student']
    if data['role'] not in valid_roles:
        return jsonify(error="Geçersiz rol. Geçerli roller: admin, teacher, student"), 400
    
    # Kullanıcı kaydı
    success, result = AuthService.register_user(
        email=data['email'],
        password=data['password'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        role=data['role'],
        department=data.get('department'),
        title=data.get('title'),
        student_number=data.get('student_number')
    )
    
    if success:
        return jsonify(message="Kullanıcı başarıyla kaydedildi.", user=result.to_dict()), 201
    else:
        return jsonify(error=result), 400

@bp.route('/login', methods=['POST'])
def login():
    """Kullanıcı girişi"""
    data = request.get_json()
    
    # Gerekli alanları kontrol et
    if 'email' not in data or 'password' not in data:
        return jsonify(error="E-posta ve şifre gerekli."), 400
    
    # Giriş işlemi
    success, result = AuthService.login(
        email=data['email'],
        password=data['password']
    )
    
    if success:
        return jsonify(result), 200
    else:
        return jsonify(error=result), 401

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Access token yenileme"""
    user_id = get_jwt_identity()
    
    # Token yenileme
    success, result = AuthService.refresh_token(user_id)
    
    if success:
        return jsonify(result), 200
    else:
        return jsonify(error=result), 401

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    """Mevcut kullanıcı bilgilerini getir"""
    user_id = get_jwt_identity()
    
    # Kullanıcı bilgilerini getir
    success, result = AuthService.get_user_by_id(user_id)
    
    if success:
        return jsonify(result.to_dict()), 200
    else:
        return jsonify(error=result), 404

@bp.route('/me', methods=['PUT'])
@jwt_required()
def update_me():
    """Mevcut kullanıcı bilgilerini güncelle"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Kullanıcı bilgilerini güncelle
    success, result = AuthService.update_user(
        user_id=user_id,
        **data
    )
    
    if success:
        return jsonify(result.to_dict()), 200
    else:
        return jsonify(error=result), 500

@bp.route('/reset-password', methods=['POST'])
def request_password_reset():
    """Şifre sıfırlama isteği gönder"""
    data = request.get_json()
    
    if 'email' not in data:
        return jsonify(error="E-posta adresi gerekli."), 400
    
    email = data['email']
    
    # Kullanıcıyı bul
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Güvenlik nedeniyle kullanıcı bulunamasa bile başarılı yanıt döndür
        return jsonify(message="Şifre sıfırlama bağlantısı e-posta adresinize gönderildi (eğer kayıtlıysa)."), 200
    
    # Benzersiz token oluştur
    token = secrets.token_urlsafe(32)
    
    # Token'ı sakla (24 saat geçerli)
    expiry = datetime.datetime.now() + datetime.timedelta(hours=24)
    password_reset_tokens[token] = {
        'user_id': user.id,
        'expiry': expiry
    }
    
    # Gerçek uygulamada burada e-posta gönderme işlemi yapılır
    # Örnek e-posta içeriği: "Şifrenizi sıfırlamak için şu bağlantıya tıklayın: http://example.com/reset-password/{token}"
    
    return jsonify(message="Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.", token=token), 200

@bp.route('/reset-password/<token>', methods=['PUT'])
def reset_password(token):
    """Şifreyi sıfırla"""
    data = request.get_json()
    
    if 'password' not in data:
        return jsonify(error="Yeni şifre gerekli."), 400
    
    # Token'ı kontrol et
    if token not in password_reset_tokens:
        return jsonify(error="Geçersiz veya süresi dolmuş token."), 400
    
    token_data = password_reset_tokens[token]
    
    # Token'ın süresini kontrol et
    if token_data['expiry'] < datetime.datetime.now():
        # Süresi dolmuş token'ı sil
        del password_reset_tokens[token]
        return jsonify(error="Geçersiz veya süresi dolmuş token."), 400
    
    # Kullanıcıyı bul
    user = User.query.get(token_data['user_id'])
    
    if not user:
        return jsonify(error="Kullanıcı bulunamadı."), 404
    
    # Şifreyi güncelle
    user.set_password(data['password'])
    db.session.commit()
    
    # Kullanılan token'ı sil
    del password_reset_tokens[token]
    
    return jsonify(message="Şifreniz başarıyla sıfırlandı."), 200 