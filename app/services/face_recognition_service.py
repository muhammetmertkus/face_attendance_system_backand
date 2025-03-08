import os
import json
import base64
import numpy as np
import face_recognition
from PIL import Image
from io import BytesIO
from flask import current_app
from werkzeug.utils import secure_filename

class FaceRecognitionService:
    """Yüz tanıma servisi"""
    
    @staticmethod
    def save_face_photo(student_id, photo_file):
        """
        Öğrencinin yüz fotoğrafını kaydet
        
        Args:
            student_id (int): Öğrenci ID
            photo_file (FileStorage): Yüklenen fotoğraf dosyası
            
        Returns:
            tuple: (başarı durumu, dosya yolu veya hata mesajı)
        """
        try:
            # Dosya adını güvenli hale getir
            filename = secure_filename(f"{student_id}.jpg")
            
            # Dosya yolunu oluştur
            upload_folder = current_app.config['UPLOAD_FOLDER']
            file_path = os.path.join(upload_folder, filename)
            
            # Fotoğrafı kaydet
            photo_file.save(file_path)
            
            # Fotoğrafta yüz olup olmadığını kontrol et
            image = face_recognition.load_image_file(file_path)
            face_locations = face_recognition.face_locations(image)
            
            if len(face_locations) == 0:
                # Yüz bulunamadı, dosyayı sil
                os.remove(file_path)
                return False, "Fotoğrafta yüz bulunamadı."
            
            if len(face_locations) > 1:
                # Birden fazla yüz bulundu, dosyayı sil
                os.remove(file_path)
                return False, "Fotoğrafta birden fazla yüz bulundu. Lütfen sadece bir yüz içeren fotoğraf yükleyin."
            
            # Yüz kodlamasını oluştur ve kaydet
            face_encoding = face_recognition.face_encodings(image)[0]
            
            # Statik URL'yi döndür
            photo_url = f"/static/faces/{filename}"
            
            return True, (photo_url, face_encoding)
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def encode_face_encoding(face_encoding):
        """
        Yüz kodlamasını JSON formatında saklanabilir hale getir
        
        Args:
            face_encoding (numpy.ndarray): Yüz kodlaması
            
        Returns:
            str: JSON formatında yüz kodlaması
        """
        if face_encoding is None:
            return None
        
        # NumPy dizisini listeye dönüştür
        encoding_list = face_encoding.tolist()
        
        # JSON formatına dönüştür
        return json.dumps(encoding_list)
    
    @staticmethod
    def decode_face_encoding(encoded_face):
        """
        JSON formatındaki yüz kodlamasını NumPy dizisine dönüştür
        
        Args:
            encoded_face (str): JSON formatında yüz kodlaması
            
        Returns:
            numpy.ndarray: Yüz kodlaması
        """
        if encoded_face is None:
            return None
        
        # JSON'dan listeye dönüştür
        encoding_list = json.loads(encoded_face)
        
        # Listeyi NumPy dizisine dönüştür
        return np.array(encoding_list)
    
    @staticmethod
    def recognize_faces(photo_file, students):
        """
        Fotoğraftaki yüzleri tanı ve öğrencileri eşleştir
        
        Args:
            photo_file (FileStorage): Yüklenen fotoğraf dosyası
            students (list): Öğrenci listesi
            
        Returns:
            tuple: (başarı durumu, tanınan öğrenciler listesi veya hata mesajı)
        """
        try:
            # Fotoğrafı yükle
            image = face_recognition.load_image_file(photo_file)
            
            # Yüzleri bul
            face_locations = face_recognition.face_locations(image)
            
            if len(face_locations) == 0:
                return False, "Fotoğrafta yüz bulunamadı."
            
            # Yüz kodlamalarını oluştur
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            # Tanınan öğrencileri sakla
            recognized_students = []
            
            # Öğrenci yüz kodlamalarını al
            student_encodings = []
            student_ids = []
            
            for student in students:
                if student.face_encoding:
                    # Kodlanmış yüzü çöz
                    student_encoding = FaceRecognitionService.decode_face_encoding(student.face_encoding)
                    student_encodings.append(student_encoding)
                    student_ids.append(student.id)
            
            # Her bir yüz için eşleşme ara
            for face_encoding in face_encodings:
                # Yüzleri karşılaştır
                matches = face_recognition.compare_faces(student_encodings, face_encoding, tolerance=0.6)
                
                # Eşleşme varsa
                if True in matches:
                    # İlk eşleşen öğrenciyi al
                    match_index = matches.index(True)
                    student_id = student_ids[match_index]
                    
                    # Öğrenciyi tanınan listeye ekle
                    if student_id not in recognized_students:
                        recognized_students.append(student_id)
            
            return True, recognized_students
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def save_attendance_photo(attendance_id, photo_file):
        """
        Yoklama fotoğrafını kaydet
        
        Args:
            attendance_id (int): Yoklama ID
            photo_file (FileStorage): Yüklenen fotoğraf dosyası
            
        Returns:
            tuple: (başarı durumu, dosya yolu veya hata mesajı)
        """
        try:
            # Dosya adını güvenli hale getir
            filename = secure_filename(f"attendance_{attendance_id}.jpg")
            
            # Dosya yolunu oluştur
            upload_folder = current_app.config['UPLOAD_FOLDER']
            file_path = os.path.join(upload_folder, filename)
            
            # Fotoğrafı kaydet
            photo_file.save(file_path)
            
            # Statik URL'yi döndür
            photo_url = f"/static/faces/{filename}"
            
            return True, photo_url
            
        except Exception as e:
            return False, str(e) 