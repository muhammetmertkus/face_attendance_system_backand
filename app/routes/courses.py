from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.course import Course, LessonTime, CourseStudent
from app.models.student import Student
from app.utils.helpers import admin_required, teacher_required, course_teacher_required, get_pagination_params, paginate_query

bp = Blueprint('courses', __name__, url_prefix='/api/courses')

@bp.route('', methods=['GET'])
@jwt_required()
def get_courses():
    """Tüm dersleri listele"""
    try:
        # Kullanıcı kimliğini al
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Sayfalama parametrelerini al
        page, per_page = get_pagination_params()
        
        # Sorguyu oluştur
        query = Course.query
        
        # Öğretmen ise, sadece kendi derslerini göster
        if user.role == 'teacher' and user.teacher:
            query = query.filter_by(teacher_id=user.teacher.id)
        
        # Öğrenci ise, sadece kayıtlı olduğu dersleri göster
        elif user.role == 'student' and user.student:
            query = query.join(CourseStudent).filter(CourseStudent.student_id == user.student.id)
        
        # Sıralama
        query = query.order_by(Course.id)
        
        # Sayfalama
        result = paginate_query(query, page, per_page)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('', methods=['POST'])
@jwt_required()
@teacher_required
def create_course():
    """Yeni ders oluştur"""
    try:
        # Kullanıcı kimliğini al
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Öğretmen değilse ve admin değilse
        if user.role != 'admin' and (not user.teacher):
            return jsonify(error="Bu işlem için öğretmen yetkisi gerekli."), 403
        
        # Verileri al
        data = request.get_json()
        
        # Gerekli alanları kontrol et
        required_fields = ['code', 'name', 'semester', 'teacher_id', 'lesson_times']
        for field in required_fields:
            if field not in data:
                return jsonify(error=f"{field} alanı gerekli."), 400
        
        # Ders saatlerini kontrol et
        if not isinstance(data['lesson_times'], list) or len(data['lesson_times']) == 0:
            return jsonify(error="En az bir ders saati gerekli."), 400
        
        # Ders oluştur
        course = Course(
            code=data['code'],
            name=data['name'],
            semester=data['semester'],
            teacher_id=data['teacher_id']
        )
        
        db.session.add(course)
        db.session.flush()  # ID'yi almak için flush
        
        # Ders saatlerini ekle
        for i, lesson_time_data in enumerate(data['lesson_times']):
            # Gerekli alanları kontrol et
            if not all(field in lesson_time_data for field in ['day', 'start_time', 'end_time']):
                db.session.rollback()
                return jsonify(error="Ders saati için gün, başlangıç ve bitiş saati gerekli."), 400
            
            # Ders saati oluştur
            lesson_time = LessonTime(
                course_id=course.id,
                lesson_number=i + 1,
                day=lesson_time_data['day'],
                start_time=lesson_time_data['start_time'],
                end_time=lesson_time_data['end_time']
            )
            
            db.session.add(lesson_time)
        
        # Değişiklikleri kaydet
        db.session.commit()
        
        return jsonify(course.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@bp.route('/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course(course_id):
    """Belirli bir dersi getir"""
    try:
        # Kullanıcı kimliğini al
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Dersi bul
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify(error="Ders bulunamadı."), 404
        
        # Yetki kontrolü
        if user.role == 'admin':
            # Admin her şeyi görebilir
            pass
        elif user.role == 'teacher' and user.teacher:
            # Öğretmen sadece kendi derslerini görebilir
            if course.teacher_id != user.teacher.id:
                return jsonify(error="Bu dersi görüntüleme yetkiniz yok."), 403
        elif user.role == 'student' and user.student:
            # Öğrenci sadece kayıtlı olduğu dersleri görebilir
            student_in_course = CourseStudent.query.filter_by(
                course_id=course_id,
                student_id=user.student.id
            ).first()
            
            if not student_in_course:
                return jsonify(error="Bu dersi görüntüleme yetkiniz yok."), 403
        else:
            return jsonify(error="Bu dersi görüntüleme yetkiniz yok."), 403
        
        return jsonify(course.to_dict()), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/<int:course_id>', methods=['PUT'])
@jwt_required()
@course_teacher_required
def update_course(course_id):
    """Ders bilgilerini güncelle"""
    try:
        # Dersi bul
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify(error="Ders bulunamadı."), 404
        
        # Verileri al
        data = request.get_json()
        
        # Ders bilgilerini güncelle
        if 'code' in data:
            course.code = data['code']
        if 'name' in data:
            course.name = data['name']
        if 'semester' in data:
            course.semester = data['semester']
        if 'teacher_id' in data:
            course.teacher_id = data['teacher_id']
        
        # Ders saatlerini güncelle
        if 'lesson_times' in data and isinstance(data['lesson_times'], list):
            # Mevcut ders saatlerini sil
            LessonTime.query.filter_by(course_id=course_id).delete()
            
            # Yeni ders saatlerini ekle
            for i, lesson_time_data in enumerate(data['lesson_times']):
                # Gerekli alanları kontrol et
                if not all(field in lesson_time_data for field in ['day', 'start_time', 'end_time']):
                    db.session.rollback()
                    return jsonify(error="Ders saati için gün, başlangıç ve bitiş saati gerekli."), 400
                
                # Ders saati oluştur
                lesson_time = LessonTime(
                    course_id=course.id,
                    lesson_number=i + 1,
                    day=lesson_time_data['day'],
                    start_time=lesson_time_data['start_time'],
                    end_time=lesson_time_data['end_time']
                )
                
                db.session.add(lesson_time)
        
        # Değişiklikleri kaydet
        db.session.commit()
        
        return jsonify(course.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@bp.route('/<int:course_id>', methods=['DELETE'])
@jwt_required()
@course_teacher_required
def delete_course(course_id):
    """Dersi sil"""
    try:
        # Dersi bul
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify(error="Ders bulunamadı."), 404
        
        # Dersi sil
        db.session.delete(course)
        db.session.commit()
        
        return jsonify(message="Ders başarıyla silindi."), 204
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@bp.route('/<int:course_id>/students', methods=['GET'])
@jwt_required()
@course_teacher_required
def get_course_students(course_id):
    """Dersin öğrencilerini getir"""
    try:
        # Dersi bul
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify(error="Ders bulunamadı."), 404
        
        # Sayfalama parametrelerini al
        page, per_page = get_pagination_params()
        
        # Öğrencileri sorgula
        query = Student.query.join(CourseStudent).filter(CourseStudent.course_id == course_id)
        
        # Sayfalama
        result = paginate_query(query, page, per_page)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/<int:course_id>/students', methods=['POST'])
@jwt_required()
@course_teacher_required
def add_students_to_course(course_id):
    """Derse öğrenci ekle"""
    try:
        # Dersi bul
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify(error="Ders bulunamadı."), 404
        
        # Verileri al
        data = request.get_json()
        
        if 'student_ids' not in data or not isinstance(data['student_ids'], list):
            return jsonify(error="Öğrenci ID'leri gerekli."), 400
        
        # Eklenen öğrencileri sakla
        added_students = []
        
        # Öğrencileri ekle
        for student_id in data['student_ids']:
            # Öğrenciyi bul
            student = Student.query.get(student_id)
            
            if not student:
                continue
            
            # Öğrenci zaten ekli mi kontrol et
            existing = CourseStudent.query.filter_by(
                course_id=course_id,
                student_id=student_id
            ).first()
            
            if existing:
                continue
            
            # Öğrenciyi derse ekle
            course_student = CourseStudent(
                course_id=course_id,
                student_id=student_id
            )
            
            db.session.add(course_student)
            added_students.append(student.to_dict())
        
        # Değişiklikleri kaydet
        db.session.commit()
        
        return jsonify(message=f"{len(added_students)} öğrenci başarıyla eklendi.", students=added_students), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@bp.route('/<int:course_id>/students/<int:student_id>', methods=['DELETE'])
@jwt_required()
@course_teacher_required
def remove_student_from_course(course_id, student_id):
    """Dersten öğrenci çıkar"""
    try:
        # Dersi bul
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify(error="Ders bulunamadı."), 404
        
        # Öğrenciyi bul
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify(error="Öğrenci bulunamadı."), 404
        
        # Öğrenci derse kayıtlı mı kontrol et
        course_student = CourseStudent.query.filter_by(
            course_id=course_id,
            student_id=student_id
        ).first()
        
        if not course_student:
            return jsonify(error="Öğrenci bu derse kayıtlı değil."), 404
        
        # Öğrenciyi dersten çıkar
        db.session.delete(course_student)
        db.session.commit()
        
        return jsonify(message="Öğrenci başarıyla çıkarıldı."), 204
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500 