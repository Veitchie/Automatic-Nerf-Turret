class Face:
    def __init__(self, box_confidence, box_left, box_top, box_right, box_bottom, is_facing, device_id, yaw_offset, pitch_offset, fov_range, id_confidence = -1, id = -1):
        """
        Face object to store face data.
        Parameters:
            box_confidence (float): The confidence of the face detection.
            box_left (int): The left edge of the box.
            box_top (int): The top edge of the box.
            box_right (int): The right edge of the box.
            box_bottom (int): The bottom edge of the box.
            id_confidence (float): The confidence of the face identification.
            id (int): The id of the face.
            is_facing (bool): Whether the face is facing the camera.
            device_id (str): The device id of the sensor.
            yaw_offset (float): The yaw offset of the face from the centre of the frame.
            pitch_offset (float): The pitch offset of the face from the centre of the frame.
            fov_range (tuple): The field of view range of the face.
        """
        self.box_confidence = box_confidence
        self.box_left = box_left
        self.box_top = box_top
        self.box_right = box_right
        self.box_bottom = box_bottom
        self.box_width = box_right - box_left
        self.box_height = box_bottom - box_top
        self.box_area = self.box_width * self.box_height
        self.box_centre = [box_left + self.box_width // 2, box_top + self.box_height // 2]
        self.id_confidence = id_confidence
        self.id = id
        self.is_facing = is_facing
        self.device_id = device_id
        self.yaw_offset = yaw_offset
        self.pitch_offset = pitch_offset
        self.fov_range = fov_range

    def to_dict(self):
        return {
            "box_confidence": self.box_confidence,
            "box_left": self.box_left,
            "box_top": self.box_top,
            "box_right": self.box_right,
            "box_bottom": self.box_bottom,
            "box_width": self.box_width,
            "box_height": self.box_height,
            "box_area": self.box_area,
            "box_centre": self.box_centre,
            "id_confidence": self.id_confidence,
            "id": self.id,
            "is_facing": self.is_facing,
            "device_id": self.device_id,
            "yaw_offset": self.yaw_offset,
            "pitch_offset": self.pitch_offset,
            "fov_range": self.fov_range
        }