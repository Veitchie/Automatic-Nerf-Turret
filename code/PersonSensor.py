# Example of accessing the Person Sensor from Useful Sensors on a Pi using
# Python. See https://usfl.ink/ps_dev for the full developer guide.

import io
import fcntl
import struct
import time
from threading import Thread


class PersonSensor:
    
    def __init__(self):

        # The person sensor has the I2C ID of hex 62, or decimal 98.
        PERSON_SENSOR_I2C_ADDRESS = 0x62

        # We will be reading raw bytes over I2C, and we'll need to decode them into
        # data structures. These strings define the format used for the decoding, and
        # are derived from the layouts defined in the developer guide.
        self.PERSON_SENSOR_I2C_HEADER_FORMAT = "BBH"
        self.PERSON_SENSOR_I2C_HEADER_BYTE_COUNT = struct.calcsize(self.PERSON_SENSOR_I2C_HEADER_FORMAT)

        self.PERSON_SENSOR_FACE_FORMAT = "BBBBBBbB"
        self.PERSON_SENSOR_FACE_BYTE_COUNT = struct.calcsize(self.PERSON_SENSOR_FACE_FORMAT)

        PERSON_SENSOR_FACE_MAX = 4
        PERSON_SENSOR_RESULT_FORMAT = self.PERSON_SENSOR_I2C_HEADER_FORMAT + "B" + self.PERSON_SENSOR_FACE_FORMAT * PERSON_SENSOR_FACE_MAX + "H"
        self.PERSON_SENSOR_RESULT_BYTE_COUNT = struct.calcsize(PERSON_SENSOR_RESULT_FORMAT)

        # I2C channel 1 is connected to the GPIO pins
        I2C_CHANNEL = 1
        I2C_PERIPHERAL = 0x703

        # How long to pause between sensor polls.
        self.PERSON_SENSOR_DELAY = 0.2 * 0.98

        self.i2c_handle = io.open("/dev/i2c-" + str(I2C_CHANNEL), "rb", buffering=0)
        fcntl.ioctl(self.i2c_handle, I2C_PERIPHERAL, PERSON_SENSOR_I2C_ADDRESS)
        
        
        # Custom variables
        self.continousEnabled = False
        self.fov = 110
        resolution = [1280,720]
        self.fovScale = [self.fov / 255, (self.fov * (resolution[1] / resolution[0])) / 255]
        self.faces = -1
        self.previousValue = [0,0]
        
        self.sensorCutoff = [[60,255],[60,255]]
        self.adjustedCentre = [self.sensorCutoff[0][0] + ((self.sensorCutoff[0][1] - self.sensorCutoff[0][0]) / 2), self.sensorCutoff[1][0] + ((self.sensorCutoff[1][1] - self.sensorCutoff[1][0]) / 2)]
        
    
    def start(self):
        self.continousEnabled = True
        Thread(target=self.continousUpdate, args=(), daemon=True).start()
    
    def stop(self):
        self.continousEnabled = False
    
    def continousUpdate(self):
        while self.continousEnabled:
            faces = self.update()
            if faces != -1:
                self.faces = faces
            #time.sleep(self.PERSON_SENSOR_DELAY)
            
    def update(self):
        """
        Grabs data and creates an array of faces (dictionaries), the array is saved to self.faces and returned by the function
        
        Parameters:
            NONE
        Returns:
            When faces are detected:
                Array of faces
            WHen no faces are detected:
                -1
        """
        attemptingConnection = True
        while attemptingConnection:
            try:
                read_bytes = self.i2c_handle.read(self.PERSON_SENSOR_RESULT_BYTE_COUNT)
                break
            except OSError as error:
                print("No person sensor data found")
                print(error)
                time.sleep(self.PERSON_SENSOR_DELAY)
        offset = 0
        (pad1, pad2, payload_bytes) = struct.unpack_from(self.PERSON_SENSOR_I2C_HEADER_FORMAT, read_bytes, offset)
        offset = offset + self.PERSON_SENSOR_I2C_HEADER_BYTE_COUNT

        (num_faces) = struct.unpack_from("B", read_bytes, offset)
        num_faces = int(num_faces[0])
        offset = offset + 1

        faces = []
        for i in range(num_faces):
            (box_confidence, box_left, box_top, box_right, box_bottom, id_confidence, id, is_facing) = struct.unpack_from(self.PERSON_SENSOR_FACE_FORMAT, read_bytes, offset)
            offset = offset + self.PERSON_SENSOR_FACE_BYTE_COUNT
            
            # Centre coordinates of the face boundary box
            x = box_left + (box_right - box_left)
            y = box_top + (box_bottom - box_top)
            # Coordinate offset of face centre
            x2 = x - (((self.sensorCutoff[0][1] - self.sensorCutoff[0][0]) / 2) + self.sensorCutoff[0][0])
            y2 = y - (((self.sensorCutoff[1][1] - self.sensorCutoff[1][0]) / 2) + self.sensorCutoff[1][0])
            face = {
                "box_confidence": box_confidence,
                "box_left": box_left,
                "box_top": box_top,
                "box_right": box_right,
                "box_bottom": box_bottom,
                "box_centre": [x, y],
                "from_centre": [x2, y2],
                "id_confidence": id_confidence,
                "id": id,
                "is_facing": is_facing,
            }
            faces.append(face)
        #print(faces)
            
        if (num_faces > 0):
            return faces#getFaceCoords(faces[0])
        return -1
        
        #checksum = struct.unpack_from("H", read_bytes, offset)
    
    def getFaces(self):
        if self.continousEnabled:
            faces = self.faces
            self.faces = -1
            return faces
            
        else:
            return self.update()
    
    def getLargestFace(self, confidence = -1, uniqueValues = False):
        faces = self.getFaces()
            
        if (faces == -1):
            if uniqueValues:
                return -1, False
            return -1
            
        value = self.getAngleEstimation(self.findLargestFace(faces, confidence))
        
        if uniqueValues:
            if (value != self.previousValue):
                self.previousValue = value
                return value, True
            self.previousValue = value
            return value, False
        return value
    
    def getMostConfident(self, confidence = -1, uniqueValues = False):
        faces = self.getFaces()
        
        if (faces == -1):
            if uniqueValues:
                return -1, False
            return -1
        
        for i in range(len(faces)):
            print()
            
    def findLargestFace(self, faces, confidence = -1):
        """
        Takes an array of faces and returns the face with the largest box area.
        
        Parameters:
            Array of faces
        Returns:
            When there are faces:
                The face with the largest box area
            When there are no faces:
                -1
        """
        max = -1
        index = -1
        for i in range(len(faces)):
            area = ( faces[i]["box_right"] - faces[i]["box_left"] ) * ( faces[i]["box_bottom"] -  faces[i]["box_top"])
            if (max < area):
                if (confidence != -1):
                    if (faces[i]["box_confidence"] >= confidence):
                        max = area
                        index = i
                else:
                    max = area
                    index = i
        if (index > -1): # Sanity check
            return faces[index]["from_centre"]
        return -1
    
    def getAngleEstimation(self, coords):
        # Estimated x/y angle offset of face centre
        if (coords == -1):
            return -1
        x = int (coords[0] * self.fovScale[0])
        y = int (coords[1] * self.fovScale[1])
        return [x,y]

def main():
    ps = PersonSensor()

    x = ""
    a = 10
    while not x == "c":
        face, unique = ps.getLargestFace(confidence = 95, uniqueValues = True)
        if (face != -1):
            if (unique):
                print(face)
        x = input()



if __name__ == '__main__':
    main()