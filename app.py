from flask import Flask
from routes import routes
from utils import ensure_directories
from camera import check_camera_sources, initialize_camera

# Create the Flask application
app = Flask(__name__)

# Register the routes blueprint
app.register_blueprint(routes)

# Initialize the application
def init_app():
    # Ensure all necessary directories exist
    ensure_directories()
    
    # Check available cameras on startup
    available_cameras = check_camera_sources()
    if available_cameras:
        # Initialize with the first available camera
        initialize_camera(available_cameras[0])

# Our main function which runs the Flask App
if __name__ == '__main__':
    init_app()
    app.run(debug=True)

