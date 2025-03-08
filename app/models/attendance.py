from datetime import datetime
from app import db

class Attendance(db.Model):
    """Yoklama modeli"""
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    lesson_number = db.Column(db.Integer, nullable=False)  # Dersin kaçıncı saati olduğu
    photo_url = db.Column(db.String(255), nullable=True)  # Yoklama fotoğrafı URL'si
    emotion_data = db.Column(db.Text, nullable=True)  # Duygu analizi verileri (JSON formatında)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    records = db.relationship('AttendanceRecord', backref='attendance', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, course_id, date, lesson_number, photo_url=None, emotion_data=None):
        self.course_id = course_id
        self.date = date
        self.lesson_number = lesson_number
        self.photo_url = photo_url
        self.emotion_data = emotion_data
    
    def to_dict(self):
        """Yoklama bilgilerini sözlük olarak döndür"""
        return {
            'id': self.id,
            'course_id': self.course_id,
            'date': self.date.isoformat() if self.date else None,
            'lesson_number': self.lesson_number,
            'photo_url': self.photo_url,
            'emotion_data': self.emotion_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Attendance {self.course_id} {self.date} #{self.lesson_number}>'

class AttendanceRecord(db.Model):
    """Yoklama kaydı modeli"""
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    attendance_id = db.Column(db.Integer, db.ForeignKey('attendances.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # PRESENT, ABSENT, LATE, EXCUSED
    emotion = db.Column(db.String(20), nullable=True)  # Öğrencinin duygu durumu
    note = db.Column(db.Text, nullable=True)  # Ek not
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Benzersiz kısıtlama: Bir öğrenci bir yoklamada yalnızca bir kez kaydedilebilir
    __table_args__ = (db.UniqueConstraint('attendance_id', 'student_id', name='unique_attendance_student'),)
    
    def __init__(self, attendance_id, student_id, status, emotion=None, note=None):
        self.attendance_id = attendance_id
        self.student_id = student_id
        self.status = status
        self.emotion = emotion
        self.note = note
    
    def to_dict(self):
        """Yoklama kaydı bilgilerini sözlük olarak döndür"""
        return {
            'id': self.id,
            'attendance_id': self.attendance_id,
            'student_id': self.student_id,
            'status': self.status,
            'emotion': self.emotion,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<AttendanceRecord {self.attendance_id}-{self.student_id}: {self.status}>' 