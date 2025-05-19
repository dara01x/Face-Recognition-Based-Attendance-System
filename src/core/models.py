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
        
        # Detect faces
        face_points = face_detector.detectMultiScale(
            gray, 
            scaleFactor=1.2,
            minNeighbors=4,
            minSize=(30, 30)
        )
        return face_points
    else:
        return []

def identify_face(facearray):
    """Identify a face using the trained ML model"""
    model = joblib.load('src/static/models/face_recognition_model.pkl')
    return model.predict(facearray)

def train_model():
    """Train the KNN model on all faces in the faces folder"""
    faces = []
    labels = []
    userlist = os.listdir('src/static/faces')
    for user in userlist:
        # Get all image paths for this user
        image_paths = [f'src/static/faces/{user}/{img}' for img in os.listdir(f'src/static/faces/{user}')]
        
        # If there are many samples, use only a subset for training
        if len(image_paths) > 30:
            # Use every other image to reduce training set size while maintaining variety
            image_paths = image_paths[::2]
            
        for img_path in image_paths:
            img = cv2.imread(img_path)
            resized_face = cv2.resize(img, (50, 50))
            faces.append(resized_face.ravel())
            labels.append(user)
            
    faces = np.array(faces)
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(faces, labels)
    joblib.dump(knn, 'src/static/models/face_recognition_model.pkl')

def totalreg():
    """Get the total number of registered users"""
    return len(os.listdir('src/static/faces'))