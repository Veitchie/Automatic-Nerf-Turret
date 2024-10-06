import cv2
import time
from threading import Thread
from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit
from SensorHandler import SensorHandler

app = Flask(__name__)
socketio = SocketIO(app)

# Initialize the SensorHandler
sensor_handler = SensorHandler()
#sensor_handler.start()

# Global variable to store the latest frame
latest_frame = None

def capture_frames():
    global latest_frame
    while True:
        frame = sensor_handler._camera.getFrame()
        if frame is not None and frame.size != 0:
            latest_frame = frame
        time.sleep(0.01)  # Small delay to prevent excessive CPU usage

# Start the frame capture thread
capture_thread = Thread(target=capture_frames)
capture_thread.daemon = True
capture_thread.start()

def gen_frames():
    global latest_frame
    while True:
        if latest_frame is None:
            print("Error: No frame available")
            time.sleep(0.1)  # Add a delay to avoid requesting frames too quickly
            continue
        ret, buffer = cv2.imencode('.jpg', latest_frame)
        if not ret:
            print("Error: Failed to encode frame")
            time.sleep(0.1)  # Add a delay to avoid requesting frames too quickly
            continue
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.01)  # Small delay to control the frame rate

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('control_turret')
def handle_control_turret(data):
    # Implement turret control logic here
    print(f"Received control command: {data}")
    # Example: move turret based on received data
    # turret.move(data['direction'])

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)