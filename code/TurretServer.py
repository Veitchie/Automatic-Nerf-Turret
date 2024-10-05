from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO, emit
from threading import Thread
import cv2
import time
from Turret import Turret, _TurretMode

class TurretServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)
        self.turret = Turret()
        self.turret.setMode(_TurretMode.MANUAL)
        self.latest_frame = None

        # Start the frame capture thread
        self.capture_thread = Thread(target=self.capture_frames)
        self.capture_thread.daemon = True
        self.capture_thread.start()

        # Define routes and socket events
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/video_feed', 'video_feed', self.video_feed)
        self.app.add_url_rule('/click_coordinates', 'click_coordinates', self.click_coordinates, methods=['POST'])
        self.socketio.on_event('control_turret', self.handle_control_turret)

    def capture_frames(self):
        while True:
            frame = self.turret.get_frame()
            if frame is not None and frame.size != 0:
                self.latest_frame = frame
            time.sleep(0.01)  # Small delay to prevent excessive CPU usage

    def gen_frames(self):
        while True:
            if self.latest_frame is None:
                print("Error: No frame available")
                time.sleep(0.1)  # Add a delay to avoid requesting frames too quickly
                continue
            ret, buffer = cv2.imencode('.jpg', self.latest_frame)
            if not ret:
                print("Error: Failed to encode frame")
                time.sleep(0.1)  # Add a delay to avoid requesting frames too quickly
                continue
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.01)  # Small delay to control the frame rate

    def index(self):
        return render_template('index.html')

    def video_feed(self):
        return Response(self.gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    def click_coordinates(self):
        data = request.get_json()
        x = data['x']
        y = data['y']
        print(f"Received click coordinates: x={x}, y={y}")
        # Process the coordinates as needed
        # For example, you can move the turret based on the coordinates
        print("Received click coordinates: x=%s, y=%s" % (x, y))
        angles = self.turret._sensorHandler._camera.getAngleEstimation((x, y), fromCentre=False)
        self.turret._adjustTrack(angles)
        return jsonify(success=True)

    def handle_control_turret(self, data):
        # Implement turret control logic here
        print(f"Received control command: {data}")
        # Example: move turret based on received data
        match data['direction']:
            case 'up':
                self.turret._adjustTrack((0,10))
            case 'down':
                self.turret._adjustTrack((0,-10))
            case 'left':
                self.turret._adjustTrack((-10,0))
            case 'right':
                self.turret._adjustTrack((10,0))
            case 'stop':
                self.turret.stop()
            case _:
                print("Invalid direction command")

    def run(self):
        self.socketio.run(self.app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    server = TurretServer()
    server.run()