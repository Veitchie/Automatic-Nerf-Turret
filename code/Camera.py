import cv2
from picamera2 import Picamera2
from threading import Thread
from Sensor import Sensor
from Face import Face

class Camera(Sensor):

    def __init__(self, resolution = (3280,2464)):
        
        # Set the capture resolution if the camera
        resolutions = {
            (3280,2464) : 70,
            (640,480) : 30
        }

        super().__init__(resolution = resolution, fov = resolutions[resolution])
        self._clasifier = None

        # Setup Picamera2
        self.__picam = Picamera2()
        self.__picam.configure(self.__picam.create_video_configuration(main={"format": 'XRGB8888',"size": resolution}))
        self.__updateThread = Thread(target=self.__continousUpdateThread, args=(), daemon=True)
        self.__continousUpdate = False

        self.__picam.start()
        self._frame = self.__picam.capture_array()
        self._previousFrame = self._frame
        #self.start()

    def readData(self):
        return self.getFrame()

    def start(self):
        self.__continousUpdate = True
        self.__updateThread.start()

    def stop(self):
        self.__continousUpdate = False

    def __continousUpdateThread(self):
        while self.__continousUpdate:
            self._frame = self.__picam.capture_array()
            if self._frame is None:
                self._frame = self._previousFrame

    def detectFaces(self, image = None):
        if image is None:
            return []
        if self._clasifier is None:
            self._clasifier = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faceData, _, weightData = self._clasifier.detectMultiScale3(gray_image, 1.1, 5, minSize=(40, 40), outputRejectLevels = True)

        faces = []
        for (x, y, w, h), confidence in zip(faceData, weightData):
            coords = [x + (w//2), y + (h//2)]
            angle_offset = self.getAngleEstimationFromRaw(coords)
            angA = self.getAngleEstimationFromRaw((x + w, y + h))
            angB = self.getAngleEstimationFromRaw((x, y))
            angle_range = (abs(angA[0] - angB[0]), abs(angA[1] - angB[1]))
            face = Face(
                box_confidence=confidence,
                box_left=x,
                box_top=y,
                box_right=x + w,
                box_bottom=y + h,
                is_facing=True,
                device_id="camera",
                yaw_offset=angle_offset[0],
                pitch_offset=angle_offset[1],
                fov_range=angle_range
            )
            faces.append(face.to_dict())
        if len(faces) > 0:
            return faces
        return []
    
    # def getAngleEstimation(self, coordinates, fromCentre = True):
    #     if coordinates == -1:
    #         return -1
    #     x = self._fovScale[0] * coordinates[0]
    #     y = self._fovScale[1] * coordinates[1]

    #     if fromCentre:
    #         return (x - (self._fov // 2), (y - ((self._fov * (self._height / self._width))  // 2)) * -1)
    #     return (x,y * -1)
    
    def getFrame(self):
        if not self.__continousUpdate:
            self._frame = self.__picam.capture_array()
            self._previousFrame = self._frame
            return self._frame
        frame = self._frame
        self._previousFrame = self._frame
        self._frame = None
        return frame

if __name__ == "__main__":
    
    cam = Camera(resolution=(640,480))

    while True:
        image = cam.getFrame()
        #cv2.imwrite('test.png',image)
        #break
        faces = cam.detectFaces(image)
        if len(faces) > 0:
            #ang = cam.getAngleEstimationFromRaw(faces[0]['box_centre'])

            print("Faces: %s\t, Angle: %s" % (faces, (faces[0]['yaw_offset'], faces[0]['pitch_offset'])))