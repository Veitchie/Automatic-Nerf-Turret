from abc import ABC, abstractmethod

class Sensor(ABC):  # Derive from ABC so we can use @abstractmethod
    def __init__(self, resolution, fov):
        """
        Basic Sensor class to be inherited by other sensor classes.
        Parameters:
            resolution (tuple): The (x,y) values denoting WIDTH and HEIGHT of the sensor, these will function as the limit of the FOV.
            fov (tuple OR int): The field of view of the sensor, either (horizontally / vertically) or Horizontally.
        """
        if type(fov) is not tuple:
            fov = (fov, fov * (resolution[1] / resolution[0]))
        self._resolution = resolution
        self._fov = fov
        self._fovScale = (self._fov[0] / self._resolution[0], self._fov[1] / self._resolution[1])

    # Force the child class to implement this method
    @abstractmethod
    def readData(self):
        """
        Abstract method to be implemented by the child class.
        Return the data from the sensor.
        """
        pass
    
    def getResolution(self):
        """
        Returns the resolution of the sensor.
        Returns:
            tuple: The resolution of the sensor.
        """
        return self._resolution
    
    def getFOV(self):
        """
        Returns the field of view of the sensor.
        Returns:
            tuple: The field of view of the sensor.
        """
        return self._fov
    
    def getFOVScale(self):
        """
        Returns the scale of the FOV in relation to the resolution.
        Returns:
            tuple: The FOV scale.
        """
        return self._fovScale


    def getAngleEstimation(self, coordinates):
        """
        Returns the equivalent Yaw and Pitch angles from the Sensor for the given coordinate offsets (diff from centre frame).
        
        Parameters:
            coordinates (tuple): The coordinates of the target from the centre of the frame.
        Returns:
            tuple: The yaw and pitch angles from centre.
        """
        if coordinates == -1:
            return -1
        
        if coordinates[0] > self._resolution[0] // 2 or coordinates[1] > self._resolution[1] // 2:
            raise ValueError("""Coordinates are out of bounds, must be from centre and less than half the resolution.
                             Resolution: %s, Coordinates: %s, Range: %s""" % (self._resolution, coordinates, (self._resolution[0] // 2, self._resolution[1] // 2)))

        x = self._fovScale[0] * coordinates[0]
        y = self._fovScale[1] * coordinates[1]

        return (x, y)
    
    def getAngleEstimationFromRaw(self, coordinates):
        """
        Returns the equivalent Yaw and Pitch angles from the Sensor for the given frame coordinates.
        
        Parameters:
            coordinates (tuple): The raw coordinates of the target.
        Returns:
            tuple: The yaw and pitch angles from centre.
        """
        if coordinates == -1:
            return -1
        
        if coordinates[0] > self._resolution[0] or coordinates[1] > self._resolution[1]:
            raise ValueError("""Coordinates are out of bounds, must be less than the resolution.
                             Resolution: %s, Coordinates: %s""" % (self._resolution, coordinates))

        x = self._fovScale[0] * (coordinates[0] - (self._resolution[0] // 2))
        y = self._fovScale[1] * (coordinates[1] - (self._resolution[1] // 2))

        return (x, y)
    
if __name__ == "__main__":
    
    cam = Sensor(resolution=(640,480), fov=30)
    ps = Sensor(resolution=(255,255), fov=(110, 110 * (720/1280)))

    angles = ps.getAngleEstimation((125, 125))
    print(angles)