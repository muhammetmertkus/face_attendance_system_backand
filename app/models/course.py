from datetime import datetime
from app import db

class Course(db.Model):
    """Ders modeli"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(20), nullable=False)  # Örn: "2023-BAHAR"
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    lesson_times = db.relationship('LessonTime', backref='course', lazy=True, cascade='all, delete-orphan')
    students = db.relationship('CourseStudent', backref='course', lazy=True, cascade='all, delete-orphan')
    attendances = db.relationship('Attendance', backref='course', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, code, name, semester, teacher_id):
        self.code = code
        self.name = name
        self.semester = semester
        self.teacher_id = teacher_id
    
    def to_dict(self):
        """Ders bilgilerini sözlük olarak döndür"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'semester': self.semester,
            'teacher_id': self.teacher_id,
            'lesson_times': [lt.to_dict() for lt in self.lesson_times],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Course {self.code}>'

class LessonTime(db.Model):
    """Ders saati modeli"""
    __tablename__ = 'lesson_times'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    lesson_number = db.Column(db.Integer, nullable=False)  # Dersin kaçıncı saati olduğu
    day = db.Column(db.String(10), nullable=False)  # Gün (MONDAY, TUESDAY, ...)
    start_time = db.Column(db.String(5), nullable=False)  # Başlangıç saati (HH:MM)
    end_time = db.Column(db.String(5), nullable=False)  # Bitiş saati (HH:MM)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, course_id, lesson_number, day, start_time, end_time):
        self.course_id = course_id
        self.lesson_number = lesson_number
        self.day = day
        self.start_time = start_time
        self.end_time = end_time
    
    def to_dict(self):
        """Ders saati bilgilerini sözlük olarak döndür"""
        return {
            'id': self.id,
            'course_id': self.course_id,
            'lesson_number': self.lesson_number,
            'day': self.day,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<LessonTime {self.day} {self.start_time}-{self.end_time}>'

class CourseStudent(db.Model):
    """Ders-Öğrenci ilişki modeli"""
    __tablename__ = 'course_students'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Benzersiz kısıtlama: Bir öğrenci bir derse yalnızca bir kez kaydolabilir
    __table_args__ = (db.UniqueConstraint('course_id', 'student_id', name='unique_course_student'),)
    
    def __init__(self, course_id, student_id):
        self.course_id = course_id
        self.student_id = student_id
    
    def to_dict(self):
        """Ders-Öğrenci ilişki bilgilerini sözlük olarak döndür"""
        return {
            'id': self.id,
            'course_id': self.course_id,
            'student_id': self.student_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<CourseStudent {self.course_id}-{self.student_id}>' 