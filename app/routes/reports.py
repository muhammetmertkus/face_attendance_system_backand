from datetime import datetime, timedelta
import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.course import Course, CourseStudent
from app.models.student import Student
from app.models.attendance import Attendance, AttendanceRecord
from app.utils.helpers import admin_required, teacher_required, course_teacher_required, get_pagination_params, paginate_query

bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@bp.route('/attendance/daily', methods=['GET'])
@jwt_required()
def daily_attendance_report():
    """Günlük yoklama raporu"""
    try:
        # Kullanıcı kimliğini al
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Tarih parametresini al (varsayılan: bugün)
        date_str = request.args.get('date')
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify(error="Geçersiz tarih formatı. Doğru format: YYYY-MM-DD"), 400
        else:
            date = datetime.now().date()
        
        # Ders filtresi
        course_id = request.args.get('course_id', type=int)
        
        # Sorguyu oluştur
        query = Attendance.query.filter(Attendance.date == date)
        
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
        
        # Yoklamaları al
        attendances = query.all()
        
        # Rapor verilerini hazırla
        report_data = {
            'date': date.isoformat(),
            'total_attendances': len(attendances),
            'attendances': []
        }
        
        for attendance in attendances:
            # Ders bilgilerini al
            course = Course.query.get(attendance.course_id)
            
            # Yoklama kayıtlarını al
            records = AttendanceRecord.query.filter_by(attendance_id=attendance.id).all()
            
            # İstatistikleri hesapla
            total_students = len(records)
            present_count = sum(1 for r in records if r.status == 'PRESENT')
            absent_count = sum(1 for r in records if r.status == 'ABSENT')
            late_count = sum(1 for r in records if r.status == 'LATE')
            excused_count = sum(1 for r in records if r.status == 'EXCUSED')
            
            # Duygu analizi verilerini işle
            emotion_stats = None
            if attendance.emotion_data:
                try:
                    emotion_data = json.loads(attendance.emotion_data)
                    if 'class_result' in emotion_data:
                        emotion_stats = emotion_data['class_result']
                except:
                    pass
            
            # Yoklama verilerini ekle
            attendance_data = {
                'id': attendance.id,
                'course': course.to_dict() if course else None,
                'lesson_number': attendance.lesson_number,
                'statistics': {
                    'total_students': total_students,
                    'present_count': present_count,
                    'absent_count': absent_count,
                    'late_count': late_count,
                    'excused_count': excused_count,
                    'attendance_rate': round(present_count / total_students * 100, 2) if total_students > 0 else 0
                },
                'emotion_stats': emotion_stats
            }
            
            report_data['attendances'].append(attendance_data)
        
        return jsonify(report_data), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/emotions/course/<int:course_id>', methods=['GET'])
@jwt_required()
@course_teacher_required
def course_emotions_report(course_id):
    """Ders duygu analizi raporu"""
    try:
        # Dersi bul
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify(error="Ders bulunamadı."), 404
        
        # Tarih parametrelerini al
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Sorguyu oluştur
        query = Attendance.query.filter_by(course_id=course_id)
        
        # Tarih filtresi
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                query = query.filter(Attendance.date >= start_date)
            except ValueError:
                return jsonify(error="Geçersiz başlangıç tarihi formatı. Doğru format: YYYY-MM-DD"), 400
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                query = query.filter(Attendance.date <= end_date)
            except ValueError:
                return jsonify(error="Geçersiz bitiş tarihi formatı. Doğru format: YYYY-MM-DD"), 400
        
        # Yoklamaları al
        attendances = query.all()
        
        # Duygu analizi verilerini topla
        emotion_data = []
        emotion_totals = {
            'angry': 0,
            'disgust': 0,
            'fear': 0,
            'happy': 0,
            'sad': 0,
            'surprise': 0,
            'neutral': 0
        }
        total_attendances = 0
        
        for attendance in attendances:
            if attendance.emotion_data:
                try:
                    data = json.loads(attendance.emotion_data)
                    if 'class_result' in data and 'emotions' in data['class_result']:
                        emotions = data['class_result']['emotions']
                        
                        # Duyguları topla
                        for emotion, value in emotions.items():
                            if emotion in emotion_totals:
                                emotion_totals[emotion] += value
                        
                        # Yoklama verilerini ekle
                        emotion_data.append({
                            'attendance_id': attendance.id,
                            'date': attendance.date.isoformat(),
                            'lesson_number': attendance.lesson_number,
                            'emotions': emotions,
                            'dominant_emotion': data['class_result'].get('dominant_emotion'),
                            'dominant_emotion_score': data['class_result'].get('dominant_emotion_score')
                        })
                        
                        total_attendances += 1
                except:
                    pass
        
        # Ortalama duyguları hesapla
        average_emotions = {}
        if total_attendances > 0:
            for emotion, total in emotion_totals.items():
                average_emotions[emotion] = round(total / total_attendances, 4)
            
            # En yüksek ortalama duyguyu bul
            dominant_emotion = max(average_emotions.items(), key=lambda x: x[1])
            dominant_emotion_name = dominant_emotion[0]
            dominant_emotion_score = dominant_emotion[1]
        else:
            dominant_emotion_name = None
            dominant_emotion_score = 0
        
        # Rapor verilerini hazırla
        report_data = {
            'course': course.to_dict(),
            'total_attendances_analyzed': total_attendances,
            'average_emotions': average_emotions,
            'dominant_emotion': dominant_emotion_name,
            'dominant_emotion_score': dominant_emotion_score,
            'attendance_emotions': emotion_data
        }
        
        return jsonify(report_data), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/attendance/student/<int:student_id>', methods=['GET'])
@jwt_required()
def student_attendance_report(student_id):
    """Öğrenci yoklama raporu"""
    try:
        # Kullanıcı kimliğini al
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Öğrenciyi bul
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify(error="Öğrenci bulunamadı."), 404
        
        # Yetki kontrolü
        if user.role == 'student' and user.student and user.student.id != student_id:
            return jsonify(error="Bu öğrencinin yoklama raporlarını görüntüleme yetkiniz yok."), 403
        
        # Parametreleri al
        course_id = request.args.get('course_id', type=int)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Sorguyu oluştur
        query = AttendanceRecord.query.filter_by(student_id=student_id)
        
        # Ders filtresi
        if course_id:
            query = query.join(Attendance).filter(Attendance.course_id == course_id)
            
            # Öğretmen ise, kendi dersi mi kontrol et
            if user.role == 'teacher' and user.teacher:
                course = Course.query.get(course_id)
                if not course or course.teacher_id != user.teacher.id:
                    return jsonify(error="Bu dersin yoklama raporlarını görüntüleme yetkiniz yok."), 403
        
        # Tarih filtresi
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                query = query.join(Attendance).filter(Attendance.date >= start_date)
            except ValueError:
                return jsonify(error="Geçersiz başlangıç tarihi formatı. Doğru format: YYYY-MM-DD"), 400
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                query = query.join(Attendance).filter(Attendance.date <= end_date)
            except ValueError:
                return jsonify(error="Geçersiz bitiş tarihi formatı. Doğru format: YYYY-MM-DD"), 400
        
        # Yoklama kayıtlarını al
        records = query.join(Attendance).order_by(Attendance.date.desc()).all()
        
        # İstatistikleri hesapla
        total_records = len(records)
        present_count = sum(1 for r in records if r.status == 'PRESENT')
        absent_count = sum(1 for r in records if r.status == 'ABSENT')
        late_count = sum(1 for r in records if r.status == 'LATE')
        excused_count = sum(1 for r in records if r.status == 'EXCUSED')
        
        # Ders bazında istatistikler
        course_stats = {}
        
        for record in records:
            attendance = Attendance.query.get(record.attendance_id)
            if not attendance:
                continue
            
            course_id = attendance.course_id
            
            if course_id not in course_stats:
                course = Course.query.get(course_id)
                course_stats[course_id] = {
                    'course': course.to_dict() if course else {'id': course_id, 'name': 'Bilinmeyen Ders'},
                    'total': 0,
                    'present': 0,
                    'absent': 0,
                    'late': 0,
                    'excused': 0
                }
            
            course_stats[course_id]['total'] += 1
            
            if record.status == 'PRESENT':
                course_stats[course_id]['present'] += 1
            elif record.status == 'ABSENT':
                course_stats[course_id]['absent'] += 1
            elif record.status == 'LATE':
                course_stats[course_id]['late'] += 1
            elif record.status == 'EXCUSED':
                course_stats[course_id]['excused'] += 1
        
        # Ders istatistiklerini liste haline getir
        course_stats_list = []
        for stats in course_stats.values():
            # Devam oranını hesapla
            attendance_rate = round((stats['present'] + stats['late']) / stats['total'] * 100, 2) if stats['total'] > 0 else 0
            stats['attendance_rate'] = attendance_rate
            course_stats_list.append(stats)
        
        # Rapor verilerini hazırla
        report_data = {
            'student': student.to_dict(),
            'statistics': {
                'total_records': total_records,
                'present_count': present_count,
                'absent_count': absent_count,
                'late_count': late_count,
                'excused_count': excused_count,
                'attendance_rate': round((present_count + late_count) / total_records * 100, 2) if total_records > 0 else 0
            },
            'course_statistics': course_stats_list,
            'records': [
                {
                    'id': record.id,
                    'attendance_id': record.attendance_id,
                    'status': record.status,
                    'date': Attendance.query.get(record.attendance_id).date.isoformat() if Attendance.query.get(record.attendance_id) else None,
                    'course_id': Attendance.query.get(record.attendance_id).course_id if Attendance.query.get(record.attendance_id) else None,
                    'lesson_number': Attendance.query.get(record.attendance_id).lesson_number if Attendance.query.get(record.attendance_id) else None,
                    'note': record.note
                }
                for record in records[:50]  # Son 50 kayıt
            ]
        }
        
        return jsonify(report_data), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/attendance/course/<int:course_id>', methods=['GET'])
@jwt_required()
@course_teacher_required
def course_attendance_report(course_id):
    """Ders bazlı devamsızlık raporu"""
    try:
        # Dersi bul
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify(error="Ders bulunamadı."), 404
        
        # Tarih parametrelerini al
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Tarih filtrelerini oluştur
        date_filters = []
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                date_filters.append(Attendance.date >= start_date)
            except ValueError:
                return jsonify(error="Geçersiz başlangıç tarihi formatı. Doğru format: YYYY-MM-DD"), 400
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                date_filters.append(Attendance.date <= end_date)
            except ValueError:
                return jsonify(error="Geçersiz bitiş tarihi formatı. Doğru format: YYYY-MM-DD"), 400
        
        # Yoklamaları al
        query = Attendance.query.filter_by(course_id=course_id)
        for date_filter in date_filters:
            query = query.filter(date_filter)
        attendances = query.all()
        
        # Derse kayıtlı öğrencileri al
        students = Student.query.join(CourseStudent).filter(CourseStudent.course_id == course_id).all()
        
        # Öğrenci bazında istatistikler
        student_stats = {}
        
        # Her bir yoklama için
        for attendance in attendances:
            # Yoklama kayıtlarını al
            records = AttendanceRecord.query.filter_by(attendance_id=attendance.id).all()
            
            # Her bir kayıt için
            for record in records:
                student_id = record.student_id
                
                # Öğrenci istatistiklerini başlat
                if student_id not in student_stats:
                    student = Student.query.get(student_id)
                    student_stats[student_id] = {
                        'student': student.to_dict() if student else {'id': student_id, 'student_number': 'Bilinmeyen'},
                        'total': 0,
                        'present': 0,
                        'absent': 0,
                        'late': 0,
                        'excused': 0
                    }
                
                # İstatistikleri güncelle
                student_stats[student_id]['total'] += 1
                
                if record.status == 'PRESENT':
                    student_stats[student_id]['present'] += 1
                elif record.status == 'ABSENT':
                    student_stats[student_id]['absent'] += 1
                elif record.status == 'LATE':
                    student_stats[student_id]['late'] += 1
                elif record.status == 'EXCUSED':
                    student_stats[student_id]['excused'] += 1
        
        # Öğrenci istatistiklerini liste haline getir
        student_stats_list = []
        for stats in student_stats.values():
            # Devam oranını hesapla
            attendance_rate = round((stats['present'] + stats['late']) / stats['total'] * 100, 2) if stats['total'] > 0 else 0
            stats['attendance_rate'] = attendance_rate
            student_stats_list.append(stats)
        
        # Öğrenci istatistiklerini devam oranına göre sırala (en düşük en üstte)
        student_stats_list.sort(key=lambda x: x['attendance_rate'])
        
        # Genel istatistikler
        total_attendances = len(attendances)
        total_students = len(students)
        total_records = sum(stats['total'] for stats in student_stats.values())
        present_count = sum(stats['present'] for stats in student_stats.values())
        absent_count = sum(stats['absent'] for stats in student_stats.values())
        late_count = sum(stats['late'] for stats in student_stats.values())
        excused_count = sum(stats['excused'] for stats in student_stats.values())
        
        # Rapor verilerini hazırla
        report_data = {
            'course': course.to_dict(),
            'date_range': {
                'start_date': start_date.isoformat() if 'start_date' in locals() else None,
                'end_date': end_date.isoformat() if 'end_date' in locals() else None
            },
            'statistics': {
                'total_attendances': total_attendances,
                'total_students': total_students,
                'total_records': total_records,
                'present_count': present_count,
                'absent_count': absent_count,
                'late_count': late_count,
                'excused_count': excused_count,
                'attendance_rate': round((present_count + late_count) / total_records * 100, 2) if total_records > 0 else 0
            },
            'student_statistics': student_stats_list,
            'attendances': [
                {
                    'id': attendance.id,
                    'date': attendance.date.isoformat(),
                    'lesson_number': attendance.lesson_number
                }
                for attendance in attendances
            ]
        }
        
        return jsonify(report_data), 200
    except Exception as e:
        return jsonify(error=str(e)), 500 