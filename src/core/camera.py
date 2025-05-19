import cv2

# Global camera variables
camera = None
camera_source = 0  # Default: 0 for built-in webcam, 1 for iVCam

def check_camera_sources():
    """Check available camera sources and return a list of working camera indices"""
    # Optimized: Only check two most common camera indices (0=built-in, 1=external)
    available_cameras = []
    for i in range(2):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
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
    
    # Initialize the camera with the selected source
    camera = cv2.VideoCapture(camera_source)
    
    # Check if camera opened successfully
    if not camera.isOpened():
        # Try the alternative camera
        alt_source = 1 if camera_source == 0 else 0
        camera = cv2.VideoCapture(alt_source)
        
        if camera.isOpened():
            camera_source = alt_source
            message = f"Switched to camera {camera_source}"
            return True, message
        else:
            message = "No cameras available. Please connect a camera."
            return False, message
    
    message = f"Using camera {camera_source}"
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