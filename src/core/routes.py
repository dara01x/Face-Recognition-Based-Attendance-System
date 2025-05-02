import os
import cv2
from flask import Blueprint, render_template, Response, request, jsonify
from datetime import datetime

# Import from our modules
from src.core.models import extract_faces, identify_face, train_model, totalreg
from src.core.camera import camera, camera_source, initialize_camera, get_camera, release_camera, check_camera_sources
from src.core.utils import datetoday, datetoday2, extract_attendance, add_attendance, SUCCESS_MESSAGE, ERROR_MESSAGE

# Blueprint for organizing routes
routes = Blueprint('routes', __name__)

# Processing state variables
processing_frame = False
register_face = False
current_username = ""
current_userid = ""
required_sample_count = 100
collected_samples = 0
# Store identified users temporarily
identified_users = set()

@routes.route('/progress')
def get_progress():
    global collected_samples, required_sample_count
    progress = int((collected_samples / required_sample_count) * 100)
    return jsonify({'progress': progress, 'samples': collected_samples})

def generate_frames():
    global processing_frame, register_face, current_username, current_userid, collected_samples, required_sample_count, identified_users
    
    camera = get_camera()
    
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
                    if 'face_recognition_model.pkl' in os.listdir('src/static/models'):
                        identified_person = identify_face(face.reshape(1, -1))[0]
                        user_name = identified_person.split('_')[0]
                        cv2.putText(frame, f"User: {user_name}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        # Store identified person in the set instead of adding attendance immediately
                        identified_users.add(identified_person)
        
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
                        userimagefolder = 'src/static/faces/'+current_username+'_'+str(current_userid)
                        
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

@routes.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@routes.route('/get_camera_source')
def get_camera_source():
    return jsonify({'camera_source': camera_source})

@routes.route('/switch_camera/<int:source>')
def switch_camera(source):
    # Only accept valid camera sources (0 or 1)
    if source not in [0, 1]:
        return jsonify({'status': ERROR_MESSAGE, 'message': 'Invalid camera source'})
    
    # Initialize the camera with the new source
    success, message = initialize_camera(source)
    
    if success:
        if source == 0:
            message = "Switched to built-in laptop camera"
        else:
            message = "Switched to iVCam"
    
    return jsonify({'status': SUCCESS_MESSAGE, 'message': message})

@routes.route('/')
def home():
    global processing_frame, register_face, identified_users
    
    # Reset camera state
    processing_frame = False
    register_face = False
    # Reset identified users when returning to home
    identified_users = set()
    
    names, rolls, times, l = extract_attendance()    
    return render_template('home.html', names=names, rolls=rolls, times=times, l=l, totalreg=totalreg(), datetoday2=datetoday2) 

@routes.route('/start', methods=['GET'])
def start():
    global processing_frame, register_face, identified_users
    
    if 'face_recognition_model.pkl' not in os.listdir('src/static/models'):
        return render_template('home.html', totalreg=totalreg(), datetoday2=datetoday2, 
                              mess='There is no trained model in the static folder. Please add a new face to continue.')

    # Set the processing mode
    processing_frame = True
    register_face = False
    # Reset identified users when starting attendance
    identified_users = set()
    
    # Return to a page that shows the camera feed
    return render_template('video.html', mode="attendance")

@routes.route('/add', methods=['GET', 'POST'])
def add():
    global processing_frame, register_face, current_username, current_userid, collected_samples
    
    current_username = request.form['newusername']
    current_userid = request.form['newuserid']
    
    # Reset counters
    collected_samples = 0
    
    # Set the processing mode
    processing_frame = False
    register_face = True
    
    # Return to a page that shows the camera feed
    return render_template('video.html', mode="registration", username=current_username)

@routes.route('/stop', methods=['GET'])
def stop():
    global processing_frame, register_face, identified_users
    
    # Stop processing
    processing_frame = False
    register_face = False
    
    # Add all identified users to attendance
    for user in identified_users:
        add_attendance(user)
    
    # Clear the set after processing
    identified_users = set()
    
    # Release camera
    release_camera()
    
    # Return to home page with updated attendance
    names, rolls, times, l = extract_attendance()
    return render_template('home.html', names=names, rolls=rolls, times=times, l=l, totalreg=totalreg(),
                        datetoday2=datetoday2, mess='Processing completed successfully')