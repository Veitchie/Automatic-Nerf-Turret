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
        self.continuousEnabled = False
        self.fov = 110
        resolution = [1280,720]
        self.fovScale = (self.fov / 255, (self.fov * (resolution[1] / resolution[0])) / 255)
        self.faces = -1
        self.previousValue = [0,0]
        
    def start(self):
        self.continuousEnabled = True
        Thread(target=self._continuousUpdate, args=(), daemon=True).start()
    
    def stop(self):
        self.continuousEnabled = False
    
    def _continuousUpdate(self):
        while self.continuousEnabled:
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

        # Read data from I2C, if there is none return -1
        try:
            read_bytes = self.i2c_handle.read(self.PERSON_SENSOR_RESULT_BYTE_COUNT)
        except OSError as error:
            print("No person sensor data found")
            print(error)
            return -1

        # unpack bytes and get number of faces detected
        offset = 0
        (pad1, pad2, payload_bytes) = struct.unpack_from(self.PERSON_SENSOR_I2C_HEADER_FORMAT, read_bytes, offset)
        offset = offset + self.PERSON_SENSOR_I2C_HEADER_BYTE_COUNT

        (num_faces) = struct.unpack_from("B", read_bytes, offset)
        num_faces = int(num_faces[0])
        offset = offset + 1

        # Create an array of faces (dictionaries containing face data)
        faces = []
        for i in range(num_faces):
            (box_confidence, box_left, box_top, box_right, box_bottom, id_confidence, id, is_facing) = struct.unpack_from(self.PERSON_SENSOR_FACE_FORMAT, read_bytes, offset)
            offset = offset + self.PERSON_SENSOR_FACE_BYTE_COUNT
            
            # Box width and height
            w = box_right - box_left
            h = box_bottom - box_top
            # Centre coordinates of the face boundary box
            x = box_left + w
            y = box_top + h

            # FOV information
            coords = (x,y)
            angle_offset = self.getAngleEstimation(coords)
            angA = self.getAngleEstimation((coords[0] - (w//2), coords[1] - (h//2)))
            angB = self.getAngleEstimation((coords[0] + (w//2), coords[1] + (h//2)))
            angle_range = (abs(angA[0] - angB[0]), abs(angA[1] - angB[1]))
        
            face = {
                "box_confidence": box_confidence,
                "box_left": box_left,
                "box_top": box_top,
                "box_right": box_right,
                "box_bottom": box_bottom,
                "box_width": w,
                "box_height": h,
                "box_area" : w * h,
                "box_centre": [x, y],
                "id_confidence": id_confidence,
                "id": id,
                "is_facing": is_facing,
                "device_id" : "person_sensor",
                "yaw_offset" : angle_offset[0],
                "pitch_offset" : angle_offset[1],
                "fov_range" : angle_range
            }
            faces.append(face)
        
        # Return faces or -1 if none
        if (num_faces > 0):
            return faces
        return -1
    
    def getFaces(self):
        '''
        Return the latest array of faces captured by the sensor
        
        Parameters:
            NONE
        Returns:
            When faces are detected:
                Array of faces
            WHen no faces are detected:
                -1
        '''
        if self.continuousEnabled:
            faces = self.faces
            self.faces = -1
            return faces
            
        else:
            return self.update()
        
    def _getUnique(self, face):
        if (face != self.previousValue):
            self.previousValue = face
            return face
        return -1
    
    def getLargestFace(self, confidence = -1, uniqueValues = False):
        """
        Get most recent faces and return the face with the largest box area.
        
        Parameters:
            Array of faces
        Returns:
            When there are faces:
                The face with the largest box area
            When there are no faces:
                -1
        """

        # Get all faces and return if there are none
        faces = self.getFaces()
        if (faces == -1):
            return -1

        # Get face from array with largest area
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
            face = faces[index]
            # Return largest face or -1 if location matches previous location
            if uniqueValues:
                return self._getUnique(face)
            return face
        return -1
    
    def getMostConfidentFace(self, confidence = -1, uniqueValues = False):
        """
        Get most recent faces and return the face with the largest confidence.
        
        Parameters:
            Array of faces
        Returns:
            When there are faces:
                The face with the largest confidence
            When there are no faces:
                -1
        """

        # Get all faces and return if there are none
        faces = self.getFaces()
        if (faces == -1):
            return -1

        # Get face from array with largest confidence
        max = -1
        index = -1
        for i in range(len(faces)):
            faceConfidence = faces[i]["box_confidence"]
            if (max < faceConfidence):
                if (confidence != -1):
                    if (faces[i]["box_confidence"] >= confidence):
                        max = faceConfidence
                        index = i
                else:
                    max = faceConfidence
                    index = i
        if (index > -1): # Sanity check
            face = faces[index]
            # Return largest face or -1 if location matches previous location
            if uniqueValues:
                return self._getUnique(face)
            return face
        return -1
    
    def getAngleEstimation(self, coordinates, fromCentre = True):
        """
        Returns the equivalent Yaw and Pitch angles from the Person Sensor for the given frame coordinates.
        
        Parameters:
            coordinates - Coordinates to convert (array or tuple)
        Returns:
            Yaw & Pitch (tuple)
        """
        # Estimated x/y angle offset of face centre
        if (coordinates == -1):
            return -1
        x = int (coordinates[0] * self.fovScale[0])
        y = int (coordinates[1] * self.fovScale[1])
        if fromCentre:
            return (x - self.fov/2, y - self.fov/2)
        return (x,y)

def main():
    ps = PersonSensor()

    x = ""
    while not x == "c":
        face = ps.getMostConfidentFace()
        if (face != -1):
            print(face)



if __name__ == '__main__':
    main()