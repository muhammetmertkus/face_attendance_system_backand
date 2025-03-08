from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.teacher import Teacher
from app.models.course import Course
from app.services.auth_service import AuthService
from app.utils.helpers import admin_required, teacher_required, get_pagination_params, paginate_query

bp = Blueprint('teachers', __name__, url_prefix='/api/teachers')

@bp.route('', methods=['GET'])
@jwt_required()
def get_teachers():
    """Tüm öğretmenleri listele"""
    try:
        # Sayfalama parametrelerini al
        page, per_page = get_pagination_params()
        
        # Öğretmenleri sorgula
        query = Teacher.query.order_by(Teacher.id)
        
        # Sayfalama
        result = paginate_query(query, page, per_page)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def create_teacher():
    """Yeni öğretmen oluştur"""
    data = request.get_json()
    
    # Gerekli alanları kontrol et
    required_fields = ['email', 'password', 'first_name', 'last_name', 'department']
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"{field} alanı gerekli."), 400
    
    # Öğretmen kaydı
    success, result = AuthService.register_user(
        email=data['email'],
        password=data['password'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        role='teacher',
        department=data['department'],
        title=data.get('title')
    )
    
    if success:
        return jsonify(message="Öğretmen başarıyla oluşturuldu.", teacher=result.teacher.to_dict()), 201
    else:
        return jsonify(error=result), 400

@bp.route('/<int:teacher_id>', methods=['GET'])
@jwt_required()
def get_teacher(teacher_id):
    """Öğretmen detayını getir"""
    try:
        teacher = Teacher.query.get(teacher_id)
        
        if not teacher:
            return jsonify(error="Öğretmen bulunamadı."), 404
        
        return jsonify(teacher.to_dict()), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/<int:teacher_id>', methods=['PUT'])
@jwt_required()
def update_teacher(teacher_id):
    """Öğretmen bilgilerini güncelle"""
    try:
        # Kullanıcı kimliğini al
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Öğretmeni bul
        teacher = Teacher.query.get(teacher_id)
        
        if not teacher:
            return jsonify(error="Öğretmen bulunamadı."), 404
        
        # Yetki kontrolü: Admin veya kendisi
        if user.role != 'admin' and (not user.teacher or user.teacher.id != teacher_id):
            return jsonify(error="Bu işlem için yetkiniz yok."), 403
        
        # Güncelleme verilerini al
        data = request.get_json()
        
        # Kullanıcı bilgilerini güncelle
        user_data = {}
        if 'email' in data:
            user_data['email'] = data['email']
        if 'first_name' in data:
            user_data['first_name'] = data['first_name']
        if 'last_name' in data:
            user_data['last_name'] = data['last_name']
        if 'password' in data:
            user_data['password'] = data['password']
        
        if user_data:
            success, result = AuthService.update_user(
                user_id=teacher.user_id,
                **user_data
            )
            
            if not success:
                return jsonify(error=result), 500
        
        # Öğretmen bilgilerini güncelle
        if 'department' in data:
            teacher.department = data['department']
        if 'title' in data:
            teacher.title = data['title']
        
        db.session.commit()
        
        return jsonify(teacher.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@bp.route('/<int:teacher_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_teacher(teacher_id):
    """Öğretmeni sil"""
    try:
        teacher = Teacher.query.get(teacher_id)
        
        if not teacher:
            return jsonify(error="Öğretmen bulunamadı."), 404
        
        # Aktif dersleri kontrol et
        active_courses = Course.query.filter_by(teacher_id=teacher_id).count()
        if active_courses > 0:
            return jsonify(error="Öğretmenin aktif dersleri var. Önce dersleri silin veya başka bir öğretmene atayın."), 400
        
        # Kullanıcıyı bul
        user = User.query.get(teacher.user_id)
        
        # Öğretmeni ve kullanıcıyı sil
        db.session.delete(teacher)
        if user:
            db.session.delete(user)
        
        db.session.commit()
        
        return jsonify(message="Öğretmen başarıyla silindi."), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@bp.route('/<int:teacher_id>/courses', methods=['GET'])
@jwt_required()
def get_teacher_courses(teacher_id):
    """Öğretmenin derslerini getir"""
    try:
        # Kullanıcı kimliğini al
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Öğretmeni bul
        teacher = Teacher.query.get(teacher_id)
        
        if not teacher:
            return jsonify(error="Öğretmen bulunamadı."), 404
        
        # Yetki kontrolü: Admin veya kendisi
        if user.role != 'admin' and (not user.teacher or user.teacher.id != teacher_id):
            return jsonify(error="Bu işlem için yetkiniz yok."), 403
        
        # Sayfalama parametrelerini al
        page, per_page = get_pagination_params()
        
        # Dersleri sorgula
        query = Course.query.filter_by(teacher_id=teacher_id).order_by(Course.id)
        
        # Sayfalama
        result = paginate_query(query, page, per_page)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Öğretmen şifre hatırlatma"""
    data = request.get_json()
    
    if 'email' not in data:
        return jsonify(error="E-posta adresi gerekli."), 400
    
    # Kullanıcıyı bul
    user = User.query.filter_by(email=data['email'], role='teacher').first()
    
    if not user:
        return jsonify(error="Bu e-posta adresiyle kayıtlı öğretmen bulunamadı."), 404
    
    # Şifre hatırlatma
    success, result = AuthService.forgot_password(data['email'])
    
    if success:
        return jsonify(message=result), 200
    else:
        return jsonify(error=result), 500 