from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.course import Course, CourseStudent
from app.models.student import Student
from app.models.attendance import Attendance, AttendanceRecord
from app.services.face_recognition_service import FaceRecognitionService
from app.services.emotion_recognition_service import EmotionRecognitionService
from app.utils.helpers import admin_required, teacher_required, course_teacher_required, get_pagination_params, paginate_query

bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')

@bp.route('/course/<int:course_id>', methods=['POST'])
@jwt_required()
@course_teacher_required
def take_attendance(course_id):
    """Yoklama Al"""
    try:
        # Dersi bul
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify(error="Ders bulunamadı."), 404
        
        # Fotoğrafı al
        if 'photo' not in request.files:
            return jsonify(error="Fotoğraf gerekli."), 400
        
        photo_file = request.files['photo']
        
        if photo_file.filename == '':
            return jsonify(error="Fotoğraf seçilmedi."), 400
        
        # Ders saati numarasını al
        lesson_number = request.form.get('lesson_number', 1, type=int)
        
        # Bugün için yoklama var mı kontrol et
        today = datetime.now().date()
        existing_attendance = Attendance.query.filter_by(
            course_id=course_id,
            date=today,
            lesson_number=lesson_number
        ).first()
        
        if existing_attendance:
            return jsonify(error="Bu ders için bugün zaten yoklama alınmış."), 400
        
        # Derse kayıtlı öğrencileri al
        students = Student.query.join(CourseStudent).filter(CourseStudent.course_id == course_id).all()
        
        if not students:
            return jsonify(error="Bu derse kayıtlı öğrenci bulunamadı."), 400
        
        # Yoklama oluştur
        attendance = Attendance(
            course_id=course_id,
            date=today,
            lesson_number=lesson_number
        )
        
        db.session.add(attendance)
        db.session.flush()  # ID'yi almak için flush
        
        # Fotoğrafı kaydet
        success, photo_url = FaceRecognitionService.save_attendance_photo(attendance.id, photo_file)
        
        if success:
            attendance.photo_url = photo_url
        
        # Fotoğraftaki yüzleri tanı
        photo_file.seek(0)  # Dosya işaretçisini başa al
        success, recognized_students = FaceRecognitionService.recognize_faces(photo_file, students)
        
        if not success:
            # Hata durumunda, tüm öğrencileri yoklamada "ABSENT" olarak işaretle
            for student in students:
                record = AttendanceRecord(
                    attendance_id=attendance.id,
                    student_id=student.id,
                    status="ABSENT",
                    note="Yüz tanıma hatası: " + recognized_students
                )
                db.session.add(record)
        else:
            # Tanınan öğrencileri "PRESENT" olarak işaretle
            for student in students:
                status = "PRESENT" if student.id in recognized_students else "ABSENT"
                record = AttendanceRecord(
                    attendance_id=attendance.id,
                    student_id=student.id,
                    status=status
                )
                db.session.add(record)
        
        # Duygu analizi yap
        photo_file.seek(0)  # Dosya işaretçisini başa al
        success, emotion_data = EmotionRecognitionService.analyze_emotions(photo_file)
        
        if success:
            attendance.emotion_data = emotion_data
        
        # Değişiklikleri kaydet
        db.session.commit()
        
        return jsonify(message="Yoklama başarıyla alındı.", attendance=attendance.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

# Eski endpoint'i koruyalım ve yeni endpoint'e yönlendirelim
@bp.route('/courses/<int:course_id>/attendance', methods=['POST'])
@jwt_required()
@course_teacher_required
def take_attendance_alternative(course_id):
    """Yoklama Al (Alternatif endpoint)"""
    return take_attendance(course_id)

@bp.route('', methods=['GET'])
@jwt_required()
def get_attendances():
    """Tüm yoklamaları listele"""
    try:
        # Kullanıcı kimliğini al
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Filtreleme parametrelerini al
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        course_id = request.args.get('course_id', type=int)
        
        # Sayfalama parametrelerini al
        page, per_page = get_pagination_params()
        
        # Sorguyu oluştur
        query = Attendance.query
        
        # Tarih filtresi
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        
        # Ders filtresi
        if course_id:
            query = query.filter_by(course_id=course_id)
        
        # Rol bazlı filtreleme
        if user.role == 'teacher' and user.teacher:
            # Öğretmen sadece kendi derslerinin yoklamalarını görebilir
            query = query.join(Course).filter(Course.teacher_id == user.teacher.id)
        elif user.role == 'student' and user.student:
            # Öğrenci sadece kayıtlı olduğu derslerin yoklamalarını görebilir
            query = query.join(Course).join(CourseStudent).filter(CourseStudent.student_id == user.student.id)
        
        # Sıralama
        query = query.order_by(Attendance.date.desc(), Attendance.lesson_number)
        
        # Sayfalama
        result = paginate_query(query, page, per_page)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/<int:attendance_id>', methods=['GET'])
@jwt_required()
def get_attendance(attendance_id):
    """Yoklama detayını getir"""
    try:
        # Kullanıcı kimliğini al
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Yoklamayı bul
        attendance = Attendance.query.get(attendance_id)
        
        if not attendance:
            return jsonify(error="Yoklama bulunamadı."), 404
        
        # Yetki kontrolü
        if user.role == 'admin':
            # Admin her şeyi görebilir
            pass
        elif user.role == 'teacher' and user.teacher:
            # Öğretmen sadece kendi derslerinin yoklamalarını görebilir
            course = Course.query.get(attendance.course_id)
            if not course or course.teacher_id != user.teacher.id:
                return jsonify(error="Bu yoklamayı görüntüleme yetkiniz yok."), 403
        elif user.role == 'student' and user.student:
            # Öğrenci sadece kayıtlı olduğu derslerin yoklamalarını görebilir
            student_in_course = CourseStudent.query.filter_by(
                course_id=attendance.course_id,
                student_id=user.student.id
            ).first()
            
            if not student_in_course:
                return jsonify(error="Bu yoklamayı görüntüleme yetkiniz yok."), 403
        else:
            return jsonify(error="Bu yoklamayı görüntüleme yetkiniz yok."), 403
        
        # Yoklama kayıtlarını al
        records = AttendanceRecord.query.filter_by(attendance_id=attendance_id).all()
        
        # Sonucu oluştur
        result = attendance.to_dict()
        result['records'] = [record.to_dict() for record in records]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/course/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course_attendances(course_id):
    """Dersin yoklamalarını getir"""
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
            # Öğretmen sadece kendi derslerinin yoklamalarını görebilir
            if course.teacher_id != user.teacher.id:
                return jsonify(error="Bu dersin yoklamalarını görüntüleme yetkiniz yok."), 403
        elif user.role == 'student' and user.student:
            # Öğrenci sadece kayıtlı olduğu derslerin yoklamalarını görebilir
            student_in_course = CourseStudent.query.filter_by(
                course_id=course_id,
                student_id=user.student.id
            ).first()
            
            if not student_in_course:
                return jsonify(error="Bu dersin yoklamalarını görüntüleme yetkiniz yok."), 403
        else:
            return jsonify(error="Bu dersin yoklamalarını görüntüleme yetkiniz yok."), 403
        
        # Filtreleme parametrelerini al
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Sayfalama parametrelerini al
        page, per_page = get_pagination_params()
        
        # Sorguyu oluştur
        query = Attendance.query.filter_by(course_id=course_id)
        
        # Tarih filtresi
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        
        # Sıralama
        query = query.order_by(Attendance.date.desc(), Attendance.lesson_number)
        
        # Sayfalama
        result = paginate_query(query, page, per_page)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/<int:attendance_id>/students/<int:student_id>', methods=['POST'])
@jwt_required()
@course_teacher_required
def add_student_to_attendance(attendance_id, student_id):
    """Öğrenciyi manuel olarak yoklamaya ekle"""
    try:
        # Yoklamayı bul
        attendance = Attendance.query.get(attendance_id)
        
        if not attendance:
            return jsonify(error="Yoklama bulunamadı."), 404
        
        # Öğrenciyi bul
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify(error="Öğrenci bulunamadı."), 404
        
        # Öğrenci derse kayıtlı mı kontrol et
        student_in_course = CourseStudent.query.filter_by(
            course_id=attendance.course_id,
            student_id=student_id
        ).first()
        
        if not student_in_course:
            return jsonify(error="Öğrenci bu derse kayıtlı değil."), 400
        
        # Verileri al
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify(error="Durum (status) gerekli."), 400
        
        # Geçerli durumlar
        valid_statuses = ['PRESENT', 'ABSENT', 'LATE', 'EXCUSED']
        if data['status'] not in valid_statuses:
            return jsonify(error=f"Geçersiz durum. Geçerli durumlar: {', '.join(valid_statuses)}"), 400
        
        # Öğrenci zaten yoklamada var mı kontrol et
        existing_record = AttendanceRecord.query.filter_by(
            attendance_id=attendance_id,
            student_id=student_id
        ).first()
        
        if existing_record:
            # Mevcut kaydı güncelle
            existing_record.status = data['status']
            existing_record.note = data.get('note')
            db.session.commit()
            
            return jsonify(message="Öğrenci yoklama durumu güncellendi.", record=existing_record.to_dict()), 200
        else:
            # Yeni kayıt oluştur
            record = AttendanceRecord(
                attendance_id=attendance_id,
                student_id=student_id,
                status=data['status'],
                note=data.get('note')
            )
            
            db.session.add(record)
            db.session.commit()
            
            return jsonify(message="Öğrenci yoklamaya eklendi.", record=record.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@bp.route('/course/<int:course_id>/student/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_attendances(course_id, student_id):
    """Belirli bir derste öğrencinin yoklamalarını getir"""
    try:
        # Kullanıcı kimliğini al
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Dersi bul
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify(error="Ders bulunamadı."), 404
        
        # Öğrenciyi bul
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify(error="Öğrenci bulunamadı."), 404
        
        # Yetki kontrolü
        if user.role == 'admin':
            # Admin her şeyi görebilir
            pass
        elif user.role == 'teacher' and user.teacher:
            # Öğretmen sadece kendi derslerinin yoklamalarını görebilir
            if course.teacher_id != user.teacher.id:
                return jsonify(error="Bu dersin yoklamalarını görüntüleme yetkiniz yok."), 403
        elif user.role == 'student' and user.student:
            # Öğrenci sadece kendi yoklamalarını görebilir
            if user.student.id != student_id:
                return jsonify(error="Bu öğrencinin yoklamalarını görüntüleme yetkiniz yok."), 403
        else:
            return jsonify(error="Bu öğrencinin yoklamalarını görüntüleme yetkiniz yok."), 403
        
        # Filtreleme parametrelerini al
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Sayfalama parametrelerini al
        page, per_page = get_pagination_params()
        
        # Sorguyu oluştur
        query = AttendanceRecord.query.join(Attendance).filter(
            Attendance.course_id == course_id,
            AttendanceRecord.student_id == student_id
        )
        
        # Tarih filtresi
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        
        # Sıralama
        query = query.order_by(Attendance.date.desc(), Attendance.lesson_number)
        
        # Sayfalama
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Sonuçları hazırla
        items = []
        for record in paginated.items:
            attendance = Attendance.query.get(record.attendance_id)
            item = record.to_dict()
            item['attendance'] = attendance.to_dict() if attendance else None
            items.append(item)
        
        result = {
            'items': items,
            'page': paginated.page,
            'per_page': paginated.per_page,
            'total': paginated.total,
            'pages': paginated.pages
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/<int:attendance_id>', methods=['PUT'])
@jwt_required()
@course_teacher_required
def update_attendance(attendance_id):
    """Yoklama bilgilerini güncelle"""
    try:
        # Yoklamayı bul
        attendance = Attendance.query.get(attendance_id)
        
        if not attendance:
            return jsonify(error="Yoklama bulunamadı."), 404
        
        # Kullanıcı kimliğini al
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Yetki kontrolü
        if user.role != 'admin':
            # Öğretmen sadece kendi derslerinin yoklamalarını güncelleyebilir
            course = Course.query.get(attendance.course_id)
            if not course or (user.role == 'teacher' and user.teacher and course.teacher_id != user.teacher.id):
                return jsonify(error="Bu yoklamayı güncelleme yetkiniz yok."), 403
        
        # Verileri al
        data = request.get_json()
        
        # Yoklama bilgilerini güncelle
        if 'date' in data:
            try:
                attendance.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify(error="Geçersiz tarih formatı. Doğru format: YYYY-MM-DD"), 400
        
        if 'lesson_number' in data:
            attendance.lesson_number = data['lesson_number']
        
        # Yoklama kayıtlarını güncelle
        if 'records' in data and isinstance(data['records'], list):
            for record_data in data['records']:
                if 'student_id' not in record_data or 'status' not in record_data:
                    continue
                
                # Geçerli durumlar
                valid_statuses = ['PRESENT', 'ABSENT', 'LATE', 'EXCUSED']
                if record_data['status'] not in valid_statuses:
                    continue
                
                # Yoklama kaydını bul veya oluştur
                record = AttendanceRecord.query.filter_by(
                    attendance_id=attendance_id,
                    student_id=record_data['student_id']
                ).first()
                
                if record:
                    # Mevcut kaydı güncelle
                    record.status = record_data['status']
                    if 'note' in record_data:
                        record.note = record_data['note']
                    if 'emotion' in record_data:
                        record.emotion = record_data['emotion']
                else:
                    # Yeni kayıt oluştur
                    record = AttendanceRecord(
                        attendance_id=attendance_id,
                        student_id=record_data['student_id'],
                        status=record_data['status'],
                        note=record_data.get('note'),
                        emotion=record_data.get('emotion')
                    )
                    db.session.add(record)
        
        # Değişiklikleri kaydet
        db.session.commit()
        
        # Güncellenmiş yoklama bilgilerini döndür
        result = attendance.to_dict()
        result['records'] = [record.to_dict() for record in attendance.records]
        
        return jsonify(message="Yoklama başarıyla güncellendi.", attendance=result), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@bp.route('/<int:attendance_id>', methods=['DELETE'])
@jwt_required()
@course_teacher_required
def delete_attendance(attendance_id):
    """Yoklamayı sil"""
    try:
        # Yoklamayı bul
        attendance = Attendance.query.get(attendance_id)
        
        if not attendance:
            return jsonify(error="Yoklama bulunamadı."), 404
        
        # Kullanıcı kimliğini al
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Yetki kontrolü
        if user.role != 'admin':
            # Öğretmen sadece kendi derslerinin yoklamalarını silebilir
            course = Course.query.get(attendance.course_id)
            if not course or (user.role == 'teacher' and user.teacher and course.teacher_id != user.teacher.id):
                return jsonify(error="Bu yoklamayı silme yetkiniz yok."), 403
        
        # Yoklama kayıtlarını sil
        AttendanceRecord.query.filter_by(attendance_id=attendance_id).delete()
        
        # Yoklamayı sil
        db.session.delete(attendance)
        db.session.commit()
        
        return jsonify(message="Yoklama başarıyla silindi."), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500 