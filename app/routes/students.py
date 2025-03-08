from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.student import Student
from app.services.auth_service import AuthService
from app.services.face_recognition_service import FaceRecognitionService
from app.utils.helpers import admin_required, teacher_required, get_pagination_params, paginate_query

bp = Blueprint('students', __name__, url_prefix='/api/students')

@bp.route('/create-with-face', methods=['POST'])
@jwt_required()
@teacher_required
def create_student_with_face():
    """Yeni öğrenci oluştur ve yüz fotoğrafı yükle"""
    try:
        # Form verilerini al
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        student_number = request.form.get('student_number')
        department = request.form.get('department')
        
        # Fotoğrafı al
        if 'file' not in request.files:
            return jsonify(error="Fotoğraf gerekli."), 400
        
        photo_file = request.files['file']
        
        if photo_file.filename == '':
            return jsonify(error="Fotoğraf seçilmedi."), 400
        
        # Gerekli alanları kontrol et
        required_fields = [email, password, first_name, last_name, student_number, department]
        if not all(required_fields):
            return jsonify(error="Tüm alanlar gerekli."), 400
        
        # Öğrenci numarası kontrolü
        existing_student = Student.query.filter_by(student_number=student_number).first()
        if existing_student:
            return jsonify(error="Bu öğrenci numarası zaten kullanılıyor."), 400
        
        # E-posta kontrolü
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify(error="Bu e-posta adresi zaten kullanılıyor."), 400
        
        # Öğrenci kaydı
        success, result = AuthService.register_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='student',
            student_number=student_number,
            department=department
        )
        
        if not success:
            return jsonify(error=result), 400
        
        # Öğrenciyi al
        student = result.student
        
        # Yüz fotoğrafını kaydet
        success, face_result = FaceRecognitionService.save_face_photo(student.id, photo_file)
        
        if not success:
            # Öğrenciyi sil
            db.session.delete(student)
            db.session.delete(result)
            db.session.commit()
            return jsonify(error=face_result), 400
        
        # Yüz kodlamasını ve URL'yi kaydet
        photo_url, face_encoding = face_result
        
        # Yüz kodlamasını JSON formatına dönüştür
        encoded_face = FaceRecognitionService.encode_face_encoding(face_encoding)
        
        # Öğrenciyi güncelle
        student.face_encoding = encoded_face
        student.face_photo_url = photo_url
        db.session.commit()
        
        return jsonify(student.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@bp.route('', methods=['GET'])
@jwt_required()
def get_students():
    """Tüm öğrencileri listele"""
    try:
        # Sayfalama parametrelerini al
        page, per_page = get_pagination_params()
        
        # Öğrencileri sorgula
        query = Student.query.order_by(Student.id)
        
        # Sayfalama
        result = paginate_query(query, page, per_page)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student(student_id):
    """Öğrenci detayını getir"""
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify(error="Öğrenci bulunamadı."), 404
        
        return jsonify(student.to_dict()), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/<int:student_id>', methods=['PUT'])
@jwt_required()
def update_student(student_id):
    """Öğrenci bilgilerini güncelle"""
    try:
        # Kullanıcı kimliğini al
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Öğrenciyi bul
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify(error="Öğrenci bulunamadı."), 404
        
        # Yetki kontrolü: Admin, öğretmen veya kendisi
        if user.role not in ['admin', 'teacher'] and (not user.student or user.student.id != student_id):
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
                user_id=student.user_id,
                **user_data
            )
            
            if not success:
                return jsonify(error=result), 500
        
        # Öğrenci bilgilerini güncelle
        if 'department' in data:
            student.department = data['department']
        
        db.session.commit()
        
        return jsonify(student.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Öğrenci şifre hatırlatma"""
    data = request.get_json()
    
    if 'email' not in data:
        return jsonify(error="E-posta adresi gerekli."), 400
    
    # Kullanıcıyı bul
    user = User.query.filter_by(email=data['email'], role='student').first()
    
    if not user:
        return jsonify(error="Bu e-posta adresiyle kayıtlı öğrenci bulunamadı."), 404
    
    # Şifre hatırlatma
    success, result = AuthService.forgot_password(data['email'])
    
    if success:
        return jsonify(message=result), 200
    else:
        return jsonify(error=result), 500 