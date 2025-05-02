import cv2
import os
import numpy as np
import joblib
from sklearn.neighbors import KNeighborsClassifier

# Face detector for all face-related operations
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def extract_faces(img):
    """Extract faces from an image using Haar cascade classifier"""
    if img.size != 0:  # Check if image is valid
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply image enhancements for better face detection
        # Histogram equalization to improve contrast
        gray = cv2.equalizeHist(gray)
        
        # Apply slight Gaussian blur to reduce noise
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Detect faces with slightly more sensitive parameters for lower quality cameras
        face_points = face_detector.detectMultiScale(
            gray, 
            scaleFactor=1.2,  # Reduced from 1.3 for better detection
            minNeighbors=4,   # Reduced from 5 to be less strict
            minSize=(30, 30)  # Minimum face size to detect
        )
        return face_points
    else:
        return []

def identify_face(facearray):
    """Identify a face using the trained ML model"""
    model = joblib.load('static/face_recognition_model.pkl')
    return model.predict(facearray)

def train_model():
    """Train the KNN model on all faces in the faces folder"""
    faces = []
    labels = []
    userlist = os.listdir('static/faces')
    for user in userlist:
        for imgname in os.listdir(f'static/faces/{user}'):
            img = cv2.imread(f'static/faces/{user}/{imgname}')
            resized_face = cv2.resize(img, (50, 50))
            faces.append(resized_face.ravel())
            labels.append(user)
    faces = np.array(faces)
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(faces, labels)
    joblib.dump(knn, 'static/face_recognition_model.pkl')

def totalreg():
    """Get the total number of registered users"""
    return len(os.listdir('static/faces'))