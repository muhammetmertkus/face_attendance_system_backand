import json
import numpy as np
from fer import FER
import face_recognition
from PIL import Image
import cv2
from io import BytesIO

class EmotionRecognitionService:
    """Duygu analizi servisi"""
    
    @staticmethod
    def analyze_emotions(photo_file):
        """
        Fotoğraftaki yüzlerin duygularını analiz et
        
        Args:
            photo_file (FileStorage): Yüklenen fotoğraf dosyası
            
        Returns:
            tuple: (başarı durumu, duygu analizi sonuçları veya hata mesajı)
        """
        try:
            # FER modelini yükle
            emotion_detector = FER()
            
            # Fotoğrafı yükle
            image = face_recognition.load_image_file(photo_file)
            
            # OpenCV formatına dönüştür (BGR)
            image_cv = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # Duygu analizi yap
            emotions = emotion_detector.detect_emotions(image_cv)
            
            if not emotions:
                return False, "Fotoğrafta yüz bulunamadı veya duygular analiz edilemedi."
            
            # Sonuçları işle
            results = []
            for emotion_data in emotions:
                # Yüz konumu
                box = emotion_data['box']
                
                # Duygular
                emotions_dict = emotion_data['emotions']
                
                # En yüksek duyguyu bul
                dominant_emotion = max(emotions_dict.items(), key=lambda x: x[1])
                
                # Sonucu ekle
                results.append({
                    'box': box,
                    'emotions': emotions_dict,
                    'dominant_emotion': dominant_emotion[0],
                    'dominant_emotion_score': dominant_emotion[1]
                })
            
            # Sınıfın genel duygu durumunu hesapla
            if results:
                # Tüm duyguları topla
                all_emotions = {
                    'angry': 0,
                    'disgust': 0,
                    'fear': 0,
                    'happy': 0,
                    'sad': 0,
                    'surprise': 0,
                    'neutral': 0
                }
                
                for result in results:
                    for emotion, score in result['emotions'].items():
                        all_emotions[emotion] += score
                
                # Ortalama al
                for emotion in all_emotions:
                    all_emotions[emotion] /= len(results)
                
                # En yüksek ortalama duyguyu bul
                class_dominant_emotion = max(all_emotions.items(), key=lambda x: x[1])
                
                # Genel sonucu ekle
                class_result = {
                    'face_count': len(results),
                    'emotions': all_emotions,
                    'dominant_emotion': class_dominant_emotion[0],
                    'dominant_emotion_score': class_dominant_emotion[1]
                }
                
                # Sonuçları JSON formatına dönüştür
                emotion_data = json.dumps({
                    'individual_results': results,
                    'class_result': class_result
                })
                
                return True, emotion_data
            
            return False, "Duygu analizi sonuçları işlenemedi."
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_emotion_from_face(face_image):
        """
        Tek bir yüz için duygu analizi yap
        
        Args:
            face_image (numpy.ndarray): Yüz görüntüsü
            
        Returns:
            tuple: (başarı durumu, duygu veya hata mesajı)
        """
        try:
            # FER modelini yükle
            emotion_detector = FER()
            
            # OpenCV formatına dönüştür (BGR)
            face_image_cv = cv2.cvtColor(face_image, cv2.COLOR_RGB2BGR)
            
            # Duygu analizi yap
            emotions = emotion_detector.detect_emotions(face_image_cv)
            
            if not emotions:
                return False, "Yüzde duygu bulunamadı."
            
            # İlk yüzün duygularını al
            emotions_dict = emotions[0]['emotions']
            
            # En yüksek duyguyu bul
            dominant_emotion = max(emotions_dict.items(), key=lambda x: x[1])
            
            return True, dominant_emotion[0]
            
        except Exception as e:
            return False, str(e) 