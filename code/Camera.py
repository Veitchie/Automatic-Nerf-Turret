import cv2
from picamera2 import Picamera2
from threading import Thread

class Camera:

    def __init__(self, resolution = (3280,2464)):
        
        # Set the capture resolution if the camera
        resolutions = {
            (3280,2464) : 70,
            (640,480) : 30
        }

        # Setup attributes
        self._width = resolution[0]
        self._height = resolution[1]
        self._fov = resolutions[resolution]
        self._fovScale = (self._fov / self._width, (self._fov * (self._height / self._width)) / self._height)
        self._clasifier = None

        # Setup Picamera2
        self.__picam = Picamera2()
        self.__picam.configure(self.__picam.create_video_configuration(main={"format": 'XRGB8888',"size": (self._width, self._height)}))
        self.__updateThread = Thread(target=self.__continousUpdateThread, args=(), daemon=True)
        self.__continousUpdate = False

        self.__picam.start()
        self._frame = self.__picam.capture_array()
        #self.start()

    def start(self):
        self.__continousUpdate = True
        self.__updateThread.start()

    def stop(self):
        self.__continousUpdate = False

    def __continousUpdateThread(self):
        while self.__continousUpdate:
            self._frame = self.__picam.capture_array()

    def detectFaces(self, image = None):
        if image is None:
            image = self._frame
        if self._clasifier is None:
            self._clasifier = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faceData, _, weightData = self._clasifier.detectMultiScale3(gray_image, 1.1, 5, minSize=(40, 40), outputRejectLevels = True)

        faces = []
        for (x, y, w, h), confidence in zip(faceData, weightData):
            coords = [x + (w//2), y + (h//2)]
            angle_offset = self.getAngleEstimation(coords, fromCentre = True)
            angA = self.getAngleEstimation((coords[0] - (w//2), coords[1] - (h//2)))
            angB = self.getAngleEstimation((coords[0] + (w//2), coords[1] + (h//2)))
            angle_range = (abs(angA[0] - angB[0]), abs(angA[1] - angB[1]))
            face = {
                "box_confidence" : confidence,
                "box_left": x,
                "box_top": y,
                "box_width": w,
                "box_height": h,
                "box_area" : w * h,
                "box_centre": coords,
                "is_facing": True,
                "device_id" : "camera",
                "yaw_offset" : angle_offset[0],
                "pitch_offset" : angle_offset[1],
                "fov_range" : angle_range
            }
            faces.append(face)
        if len(faces) > 0:
            return faces
        return []
    
    def getAngleEstimation(self, coordinates, fromCentre = True):
        if coordinates == -1:
            return -1
        x = self._fovScale[0] * coordinates[0]
        y = self._fovScale[1] * coordinates[1]

        if fromCentre:
            return (x - (self._fov // 2), (y - ((self._fov * (self._height / self._width))  // 2)) * -1)
        return (x,y * -1)
    
    def getFrame(self):
        if not self.__continousUpdate:
            self._frame = self.__picam.capture_array()
            return self._frame
        return self._frame

if __name__ == "__main__":
    
    cam = Camera(resolution=(640,480))

    while True:
        image = cam.getFrame()
        #cv2.imwrite('test.png',image)
        #break
        faces = cam.detectFaces(image)
        if len(faces) > 0:
            ang = cam.getAngleEstimation(faces[0]['box_centre'], fromCentre = True)

            print("Faces: %s\t, Angle: %s" % (faces, ang))
        else:
            print()