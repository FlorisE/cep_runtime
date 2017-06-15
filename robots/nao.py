from __future__ import print_function
from naoqi import *
from shared import *

from collections import defaultdict

memory = None
actuators = []
sensorStreams = defaultdict(list)


Module = ALModule
Proxy = ALProxy
Broker = ALBroker
qi = qi



class MemoryModule(Module):
    def __init__(self, name, event):
        Module.__init__(self, name)
        self.name = name
        self.event = event
        global memory
        self.memory = Proxy("ALMemory")
        self.subscribe_to_event()

    def subscribe_to_event(self):
        if self.name not in self.memory.getSubscribers(self.event):
            try:
                self.memory.subscribeToEvent(self.event, self.name, "publish")
            except RuntimeError:
                pass

    def unsubscribe_to_event(self):
        if self.name in self.memory.getSubscribers(self.event):
            try:
                self.memory.unsubscribeToEvent(self.event, self.name)
            except RuntimeError:
                pass

    def publish(self):
        """ required doc """
        #self.unsubscribe_to_event()
        self.concrete_publish() # should be implemented by children
        #self.subscribe_to_event()



# <editor-fold desc="Red ball">

class RedBall(object):
    def __init__(self, params):
        self.timestamp = params[0]
        self.ballInfo = params[1]
        self.cameraTorso = params[2]
        self.cameraRobot = params[3]
        self.cameraId = params[4]
        self.x = self.ballInfo[0]
        self.y = self.ballInfo[1]
        self.width = 2 * self.ballInfo[2] * 2
        self.height = 2 * self.ballInfo[3] * 2


class RedBallMemoryModule(MemoryModule):
    """ reacts to redballmemory events """
    def __init__(self, name):
        MemoryModule.__init__(self, name, "redBallDetected")

    def concrete_publish(self):
        value = self.memory.getData("redBallDetected")
        for detector in sensorStreams[self.name]:
            detector.publish(RedBall(value))


class RedBallSensor(SequentialSensor):
    def __init__(self, robot):
        SequentialSensor.__init__(self, robot)
        self.proxy = Proxy("ALRedBallDetection")
        self.memory = Proxy("ALMemory")



class RedBallSensorStream(SensorStream):
    def __init__(self, sensor):
        SensorStream.__init__(self, sensor)
        sensorStreams["RedBallMemory"].append(self)

# </editor-fold>

# <editor-fold desc="Joint position">

class JointPositionSensor(ParallelSensor):
    def __init__(self, robot):
        ParallelSensor.__init__(self, robot)


class JointPositionSensorStream(SensorStream):
    def __init__(self, sensor, joint):
        SensorStream.__init__(self, sensor)
        self.memory = Proxy("ALMemory")
        self.joint = joint
        self.latched = None
        sensorStreams["JointPositionSensor"].append(self)

    def tick(self):
        key = "Device/SubDeviceList/" + str(self.joint) + "/Position/Sensor/Value"
        data = self.memory.getData(key)
        if self.latched != data:
            self.latched = data
            self.publish(data)


# </editor-fold>

# <editor-fold desc="Blob detection">

class BlobMemoryModule(MemoryModule):
    """ reacts to blobmemory events """
    def __init__(self, name):
        MemoryModule.__init__(self, name, "ALTracker/ColorBlobDetected")
        self.proxy = Proxy("ALColorBlobDetection")

    def concrete_publish(self):
        for detector in sensorStreams[self.name]:
            circle = self.proxy.getCircle()
            if circle is not None:
                detector.publish(circle)


class BlobDetectorSensorStream(SensorStream):
    def __init__(self, sensor, red, green, blue, threshold):
        SensorStream.__init__(self, sensor)
        self.red = red
        self.green = green
        self.blue = blue
        self.threshold = threshold
        sensorStreams["BlobMemory"].append(self)

    def tick(self):
        self.sensor.set_color(self.red, self.green, self.blue, self.threshold)


# wrapper for aldebaran blob detector
class BlobDetectorSensor(SequentialSensor):
    def __init__(self, robot):
        SequentialSensor.__init__(self, robot)
        self.proxy = Proxy("ALColorBlobDetection")
        self.memory = Proxy("ALMemory")

    def set_color(self, red, green, blue, threshold):
        self.proxy.setColor(red, green, blue, threshold)

# </editor-fold>


# <editor-fold desc="Word recognized">


class WordRecognizedMemoryModule(MemoryModule):
    """ reacts to blobmemory events """
    def __init__(self, name):
        MemoryModule.__init__(self, name, "WordRecognized")

    def concrete_publish(self):
        data = self.memory.getData("WordRecognized")
        print(data)
        for detector in sensorStreams[self.name]:
            if len(data) > 0 and detector.vocabulary.contains(data[0]):
                detector.publish(data[0])


class WordRecognizedSensor(SingletonSensor):
    def __init__(self, robot):
        SingletonSensor.__init__(self, robot)
        self.robot = robot
        self.proxy = Proxy("ALSpeechRecognition")
        self.memory = Proxy("ALMemory")
        self.proxy.setLanguage("English")
        self.vocabulary = set()

    def set_vocabulary(self, vocabulary):
        for item in vocabulary:
            if item not in self.vocabulary:
                self.vocabulary.add(item)

    def start(self):
        self.proxy.pause(True)
        self.proxy.setVocabulary(list(self.vocabulary), False)
        self.proxy.pause(False)
        self.proxy.subscribe("WordRecognized")



class WordRecognizedSensorStream(SensorStream):
    def __init__(self, sensor, vocabulary):
        SensorStream.__init__(self, sensor)
        self.vocabulary = set(vocabulary)
        sensorStreams["WordRecognized"].append(self)

    def start(self):
        self.sensor.set_vocabulary(self.vocabulary)


# </editor-fold>

# <editor-fold desc="Face detection">

class FaceDetectionMemoryModule(Module):
    """ reacts to face detected events """
    def __init__(self, name):
        Module.__init__(self, name)
        self.name = name
        global memory
        self.memory = Proxy("ALMemory")
        self.subscribeToEvent()

    def subscribeToEvent(self):
        if self.name not in self.memory.getSubscribers("FaceDetected"):
            try:
                self.memory.subscribeToEvent("FaceDetected", self.name, "publish")
            except RuntimeError:
                pass

    def unsubscribeToEvent(self):
        if self.name in self.memory.getSubscribers("FaceDetected"):
            try:
                self.memory.unsubscribeToEvent("FaceDetected", self.name)
            except RuntimeError:
                pass

    def publish(self):
        """ required doc """
        self.unsubscribeToEvent()
        data = self.memory.getData("FaceDetected", 0)
        for detector in sensorStreams["FaceDetector"]:
            detector.publish(len(data))
        self.subscribeToEvent()


class Face(object):
    def __init__(self, data):
        self.timestamp = data[0]
        self.faceAndRecoInfo = data[1]
        self.faceInfo = self.faceAndRecoInfo[0]
        self.recoInfo = self.faceAndRecoInfo[1]
        self.shapeInfo = self.faceInfo[0]
        self.extraInfo = self.faceInfo[1]
        self.cameraPoseInTorsoFrame = data[2]
        self.cameraPoseInRobotFrame = data[3]
        self.cameraId = data[4]

    @property
    def recognized_new_face(self):
        return self.recoInfo == [4]

    @property
    def is_new(self):
        return self.extraInfo[2] == ""


class FaceDetectionSensorStream(SensorStream):
    def __init__(self, sensor):
        SensorStream.__init__(self, sensor)
        sensorStreams["FaceDetector"].append(self)

    def tick(self):
        pass


class FaceDetectionSensor(ParallelSensor):
    def __init__(self, robot):
        ParallelSensor.__init__(self, robot)
        self.proxy = Proxy("ALFaceDetection")
        self.memory = Proxy("ALMemory")
        self.proxy.setRecognitionEnabled(True)

# </editor-fold>

# actuators


class LedColor(Actuator):
    def __init__(self, robot, uuid):
        Actuator.__init__(self, uuid)
        self.robot = robot
        self.module = Proxy("ALLeds")
        self.module.off("FaceLeds")

    def __call__(self, value):
        Actuator.__call__(self, value)
        if value[0]:
            print("Changing color to red")
        if value[1]:
            print("Changing color to green")
        if value[2]:
            print("Changing color to blue")
        target = self.module.setIntensity
        target("RightFaceLedsRed", value[0])
        target("LeftFaceLedsRed", value[0])
        target("RightFaceLedsGreen", value[1])
        target("LeftFaceLedsGreen", value[1])
        target("RightFaceLedsBlue", value[2])
        target("LeftFaceLedsBlue", value[2])


def leds_for_group(group):
    if group == "Eyes":
        return {
            "red": [
                "LeftFaceLedsRed",
                "RightFaceLedsRed"
            ],
            "blue": [
                "LeftFaceLedsBlue",
                "RightFaceLedsBlue"
            ],
            "green": [
                "LeftFaceLedsGreen",
                "RightFaceLedsGreen"
            ]
        }


class LedColorParameters(Actuator):
    def __init__(self, robot, uuid, led, red, green, blue):
        Actuator.__init__(self, uuid)
        self.robot = robot
        self.module = Proxy("ALLeds")
        self.led = leds_for_group(led)
        self.red = red
        self.green = green
        self.blue = blue

    def __call__(self, value):
        Actuator.__call__(self, value)
        try:
            for led in self.led["red"]:
                self.module.setIntensity(led, self.red)
            for led in self.led["green"]:
                self.module.setIntensity(led, self.green)
            for led in self.led["blue"]:
                self.module.setIntensity(led, self.blue)
        except BaseException as e:
            print(e)


class Print(Actuator):
    def __init__(self, robot, uuid):
        Actuator.__init__(self, uuid)

    def __call__(self, value):
        Actuator.__call__(self, value)
        print(value)


class LedBrightness(Actuator):
    def __init__(self, robot, uuid):
        Actuator.__init__(self, uuid)
        self.robot = robot
        self.module = Proxy("ALLeds")
        self.module.off("FaceLeds")

    def __call__(self, value):
        Actuator.__call__(self, value)
        self.module.setIntensity("RightFaceLedsRed", value)
        self.module.setIntensity("LeftFaceLedsRed", value)
        self.module.setIntensity("RightFaceLedsGreen", 0)
        self.module.setIntensity("LeftFaceLedsGreen", 0)
        self.module.setIntensity("RightFaceLedsBlue", 0)
        self.module.setIntensity("LeftFaceLedsBlue", 0)


class RememberFace(Actuator):
    def __init__(self, robot, uuid):
        Actuator.__init__(self, uuid)
        self.robot = robot
        self.proxy = Proxy("ALFaceDetection")

    def __call__(self, value):
        Actuator.__call__(self, value)
        if not self.proxy.learnFace("face"):
            print("Failed to learn face")


class Say(Actuator):
    def __init__(self, robot, uuid):
        Actuator.__init__(self, uuid)
        self.robot = robot
        self.tts = Proxy("ALTextToSpeech")

    def __call__(self, value):
        Actuator.__call__(self, value)
        self.tts.say(value)


class SayParameter(Actuator):
    def __init__(self, robot, uuid, text):
        Actuator.__init__(self, uuid)
        self.robot = robot
        self.tts = Proxy("ALTextToSpeech")
        self.text = text

    def __call__(self, value):
        Actuator.__call__(self, value)
        self.tts.say(self.text)


class Tracker(Actuator):
    def __init__(self, robot, uuid, tracking_mode, effector):
        Actuator.__init__(self, uuid)
        self.robot = robot
        self.tracking_mode = str(tracking_mode)
        self.tracker = Proxy("ALTracker")
        self.motion = Proxy("ALMotion")
        self.effectorMap = {
            "Left arm": "LArm",
            "Right arm": "RArm",
            "Both arms": "Arms",
            "None": "None"
        }
        self.effector = self.effectorMap[effector]
        self.tracker.registerTarget("RedBall", 0.06)
        self.tracker.track("RedBall")
        self.arm_rest_left = self.motion.getAngles("LArm", True)
        self.arm_rest_right = self.motion.getAngles("RArm", True)

    def __call__(self, value):
        Actuator.__call__(self, value)
        self.tracker.setMode(self.tracking_mode)
        self.tracker.setEffector(self.effector)
        if self.effector != "LArm":
            self.motion.setAngles("LArm", self.arm_rest_left, 0.5)
        elif self.effector != "RArm":
            self.motion.setAngles("RArm", self.arm_rest_right, 0.5)


# wrapper around Aldebaran's qi session
class Session():
    def __init__(self, ip, port=9559, protocol="tcp"):
        self.session = qi.Session('{0}://{1}:{2}'.format(protocol, ip, port))
        self.ip = ip
        self.port = port
        self.broker = Broker("broker", "0.0.0.0", 0, ip, port)


class Robot(Thread):
    def __init__(self, session):
        Thread.__init__(self)
        self.session = session
        self.running = False

        self.availableSensors = {
            "blob": BlobDetectorSensor,
            "FaceDetection": FaceDetectionSensor,
            "JointPositionSensor": JointPositionSensor,
            "RedBall": RedBallSensor,
            "WordRecognized": WordRecognizedSensor
        }

        self.activeSensors = {}

        self.availableSensorStreams = {
            "blob": BlobDetectorSensorStream,
            "FaceDetection": FaceDetectionSensorStream,
            "JointPositionSensor": JointPositionSensorStream,
            "RedBall": RedBallSensorStream,
            "WordRecognized": WordRecognizedSensorStream
        }

        self.activeSensorStreams = []

        self.availableActuators = {
            "RememberFace": RememberFace,
            "Say": Say,
            "led_brightness": LedBrightness,
            "LedColor": LedColor,
            "LedColorParameters": LedColorParameters,
            "Tracker": Tracker,
            "Print": Print,
            "SayParameter": SayParameter
        }

        self.activeActuators = {}

        self.BlobMemory = BlobMemoryModule("BlobMemory")
        self.RedBallMemory = RedBallMemoryModule("RedBallMemory")
        self.FaceDetectionMemory = FaceDetectionMemoryModule("FaceDetectionMemory")
        self.WordRecognizedMemory = FaceDetectionMemoryModule("WordRecognizedMemory")

    def get_sensor(self, sensor, parameters):
        sensordef = self.activeSensors.setdefault(sensor.name, self.availableSensors[sensor.name](self))

        retsensorStream = self.availableSensorStreams[sensor.name](sensordef, **parameters)
        self.activeSensorStreams.append(retsensorStream)
        return retsensorStream

    def get_actuator(self, actuator, parameters):
        actuator_type = self.availableActuators[actuator.name]
        parameter_dict_pythonic = {k.replace(" ", "_").lower(): v for k, v in parameters.items()}
        return actuator_type(self, actuator.uuid, **parameter_dict_pythonic)

    def stop(self):
        self.running = False

    def run(self):
        self.running = True

        for sensorStream in self.activeSensorStreams:
            sensorStream.start()

        for sensor in self.activeSensors.values():
            sensor.start()

        while self.running:
            for sensor in self.activeSensors.values():
                sensor.tick()
                time.sleep(0.5)
        #for actuatorStream in self.actuatorStreams:
        #    actuatorStream.tick()

