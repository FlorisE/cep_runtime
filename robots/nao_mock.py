from threading import Thread


qi = None



class ALColorBlobDetection(object):
    def __init__(self):
        pass

    def setColor(self, r, g, b, threshold):
        self.r = r
        self.g = g
        self.b = b
        self.threshold = threshold


class ALFaceDetector():
    pass



        

# wrapper for aldebaran blob detector
class BlobDetector(Thread):
    def __init__(self, r, g, b, threshold):
        Thread.__init__(self)
        self.r = r
        self.g = g
        self.b = b
        self.threshold = threshold
        self.proxy = ALColorBlobDetection()
        self.proxy.setColor(r, g, b, threshold)

    def run(self):
        pass


class FaceDetector(Thread):
    def __init__(self):
        Thread.__init__(self)

        self.proxy = ALFaceDetector()

class LedBrightness(Thread):
    def __init__(self):
        pass


# wrapper around Aldebaran's qi session
class Session():
    def __init__(self):
        self.session = None


class Robot():

    def __init__(self, session):
        self.session = session

    def get_sensor(self, sensor):
        sensor_type = self.sensors[sensor.name]
        return sensor_type(**sensor.parameters)


    def get_actuator(self, actuator):
        actuator_type = self.actuators[actuator.name]
        return actuator_type(**actuator.parameters)

