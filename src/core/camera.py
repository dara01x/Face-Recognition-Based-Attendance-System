import cv2

# Global camera variables
camera = None
camera_source = 0  # Default: 0 for built-in webcam, 1 for iVCam

def check_camera_sources():
    """Check available camera sources and return a list of working camera indices"""
    available_cameras = []
    for i in range(3):  # Check first 3 camera indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                available_cameras.append(i)
            cap.release()
    return available_cameras

def initialize_camera(source=None):
    """Initialize the camera with the given source or find an available one"""
    global camera, camera_source
    
    # If source is provided, use it; otherwise use the current camera_source
    if source is not None:
        camera_source = source
    
    # Release existing camera if it exists
    if camera is not None:
        camera.release()
        camera = None
    
    # Check if the requested camera is available
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
            return False, message
    
    test_cam.release()
    
    # Initialize the camera with the selected source
    camera = cv2.VideoCapture(camera_source)
    
    if camera_source == 0:
        message = "Using built-in laptop camera"
    else:
        message = "Using iVCam"
    
    return True, message

def get_camera():
    """Get the current camera object"""
    global camera, camera_source
    
    if camera is None:
        initialize_camera()
    
    return camera

def release_camera():
    """Release the camera resources"""
    global camera
    
    if camera is not None:
        camera.release()
        camera = None