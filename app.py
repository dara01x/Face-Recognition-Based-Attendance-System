import cv2
import os
from flask import Flask, request, render_template, Response, jsonify
from datetime import date
from datetime import datetime
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
import pandas as pd
import joblib

#### Defining Flask App
app = Flask(__name__)   

# Global variables
camera = None
face_cascade = None
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
processing_frame = False
register_face = False
current_username = ""
current_userid = ""
required_sample_count = 100
collected_samples = 0
camera_source = 0  # Default: 0 for built-in webcam, 1 for iVCam

# Function to check available cameras and set appropriate source
def check_camera_sources():
    available_cameras = []
    for i in range(3):  # Check first 3 camera indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                available_cameras.append(i)
            cap.release()
    return available_cameras

# Check available cameras on startup
available_cameras = check_camera_sources()
if available_cameras:
    camera_source = available_cameras[0]  # Default to first available camera

#### Saving Date today in 2 different formats
datetoday = date.today().strftime("%m_%d_%y")
datetoday2 = date.today().strftime("%d-%B-%Y")

# Message status codes
SUCCESS_MESSAGE = "success"
ERROR_MESSAGE = "error"
WARNING_MESSAGE = "warning"


#### If these directories don't exist, create them
if not os.path.isdir('Attendance'):
    os.makedirs('Attendance')
if not os.path.isdir('static'):
    os.makedirs('static')
if not os.path.isdir('static/faces'):
    os.makedirs('static/faces')
if f'Attendance-{datetoday}.csv' not in os.listdir('Attendance'):
    with open(f'Attendance/Attendance-{datetoday}.csv','w') as f:
        f.write('Name,Roll,Time')


#### get a number of total registered users
def totalreg():
    return len(os.listdir('static/faces'))


#### extract the face from an image
def extract_faces(img):
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


#### Identify face using ML model
def identify_face(facearray):
    model = joblib.load('static/face_recognition_model.pkl')
    return model.predict(facearray)


#### A function which trains the model on all the faces available in faces folder
def train_model():
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
    knn.fit(faces,labels)
    joblib.dump(knn,'static/face_recognition_model.pkl')


#### Extract info from today's attendance file in attendance folder
def extract_attendance():
    df = pd.read_csv(f'Attendance/Attendance-{datetoday}.csv')
    names = df['Name']
    rolls = df['Roll']
    times = df['Time']
    l = len(df)
    return names,rolls,times,l


#### Add Attendance of a specific user
def add_attendance(name):
    username = name.split('_')[0]
    userid = name.split('_')[1]
    current_time = datetime.now().strftime("%H:%M:%S")
    
    df = pd.read_csv(f'Attendance/Attendance-{datetoday}.csv')
    if int(userid) not in list(df['Roll']):
        with open(f'Attendance/Attendance-{datetoday}.csv','a') as f:
            f.write(f'\n{username},{userid},{current_time}')


@app.route('/progress')
def get_progress():
    global collected_samples, required_sample_count
    progress = int((collected_samples / required_sample_count) * 100)
    return jsonify({'progress': progress, 'samples': collected_samples})


def generate_frames():
    global camera, processing_frame, register_face, current_username, current_userid, collected_samples, required_sample_count, camera_source
    
    if camera is None:
        camera = cv2.VideoCapture(camera_source)  # Use selected camera source
    
    while True:
        success, frame = camera.read()
        if not success:
            break
        
        # Process the frame based on current mode
        if processing_frame:
            faces = extract_faces(frame)
            if len(faces) > 0:
                for (x, y, w, h) in faces:
                    # Draw rectangle around face
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    face = cv2.resize(frame[y:y+h, x:x+w], (50, 50))
                    
                    # Identify the face and show the name
                    if 'face_recognition_model.pkl' in os.listdir('static'):
                        identified_person = identify_face(face.reshape(1, -1))[0]
                        user_name = identified_person.split('_')[0]
                        cv2.putText(frame, f"User: {user_name}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        add_attendance(identified_person)
        
        # Process registration
        if register_face:
            faces = extract_faces(frame)
            if len(faces) > 0:
                for (x, y, w, h) in faces:
                    # Draw rectangle around face
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    
                    # Save the face
                    if collected_samples < required_sample_count:
                        face_img = frame[y:y+h, x:x+w]
                        name = current_username + '_' + str(collected_samples) + '.jpg'
                        userimagefolder = 'static/faces/'+current_username+'_'+str(current_userid)
                        
                        if not os.path.isdir(userimagefolder):
                            os.makedirs(userimagefolder)
                            
                        cv2.imwrite(userimagefolder + '/' + name, face_img)
                        collected_samples += 1
                        
                    # Display progress
                    progress = int((collected_samples / required_sample_count) * 100)
                    cv2.putText(frame, f"Progress: {progress}%", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                    
                    if collected_samples >= required_sample_count:
                        register_face = False
                        train_model()
        
        # Encode the frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        # Yield the frame in byte format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_camera_source')
def get_camera_source():
    global camera_source
    return jsonify({'camera_source': camera_source})

@app.route('/switch_camera/<int:source>')
def switch_camera(source):
    global camera, camera_source
    
    # Only accept valid camera sources (0 or 1)
    if source not in [0, 1]:
        return jsonify({'status': ERROR_MESSAGE, 'message': 'Invalid camera source'})
    
    # Release existing camera if it exists
    if camera is not None:
        camera.release()
        camera = None
    
    # Set the new camera source
    camera_source = source
    
    # Immediately initialize the new camera to test it
    test_cam = cv2.VideoCapture(camera_source)
    if not test_cam.isOpened():
        # If requested camera is not available, try to find an available one
        available_cameras = check_camera_sources()
        if available_cameras:
            camera_source = available_cameras[0]
            message = f"Requested camera not available. Using camera {camera_source} instead."
        else:
            message = "No cameras available. Please connect a camera."
        test_cam.release()
    else:
        # Properly initialize the camera right away
        ret, frame = test_cam.read()
        test_cam.release()
        
        # Initialize our global camera with the new source
        camera = cv2.VideoCapture(camera_source)
        
        if camera_source == 0:
            message = "Switched to built-in laptop camera"
        else:
            message = "Switched to iVCam"
    
    return jsonify({'status': SUCCESS_MESSAGE, 'message': message})

#### Our main page
@app.route('/')
def home():
    global camera, processing_frame, register_face
    
    # Reset camera state
    processing_frame = False
    register_face = False
    
    names, rolls, times, l = extract_attendance()    
    return render_template('home.html', names=names, rolls=rolls, times=times, l=l, totalreg=totalreg(), datetoday2=datetoday2) 

#### This function will run when we click on Take Attendance Button
@app.route('/start', methods=['GET'])
def start():
    global camera, processing_frame, register_face
    
    if 'face_recognition_model.pkl' not in os.listdir('static'):
        return render_template('home.html', totalreg=totalreg(), datetoday2=datetoday2, 
                              mess='There is no trained model in the static folder. Please add a new face to continue.')

    # Set the processing mode
    processing_frame = True
    register_face = False
    
    # Return to a page that shows the camera feed
    return render_template('video.html', mode="attendance")

#### This function will run when we add a new user
@app.route('/add', methods=['GET', 'POST'])
def add():
    global camera, processing_frame, register_face, current_username, current_userid, collected_samples
    
    current_username = request.form['newusername']
    current_userid = request.form['newuserid']
    
    # Reset counters
    collected_samples = 0
    
    # Set the processing mode
    processing_frame = False
    register_face = True
    
    # Return to a page that shows the camera feed
    return render_template('video.html', mode="registration", username=current_username)

@app.route('/stop', methods=['GET'])
def stop():
    global camera, processing_frame, register_face
    
    # Stop processing
    processing_frame = False
    register_face = False
    
    # Release camera
    if camera is not None:
        camera.release()
        camera = None
    
    # Return to home page with updated attendance
    names, rolls, times, l = extract_attendance()
    return render_template('home.html', names=names, rolls=rolls, times=times, l=l, totalreg=totalreg(),
                        datetoday2=datetoday2, mess='Processing completed successfully')


#### Our main function which runs the Flask App
if __name__ == '__main__':
    app.run(debug=True)

from datetime import date

today = date.today()

