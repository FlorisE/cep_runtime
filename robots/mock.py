from threading import Thread
import time


class Session():
    def __init__(self, ip, port, protocol, verbose):
        pass


class MockSensor(Thread):
    def __init__(self, name, verbose=True):
        Thread.__init__(self)
        self.name = name
        self.subscribers = []
        self.running = False

    def run(self):
        self.running = True
        print("{0} called".format(self.name))
        while self.running:
            time.sleep(0.1)

    def stop(self):
        self.running = False

    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)


class MockActuator(Thread):
    def __init__(self, name, verbose=True):
        Thread.__init__(self)
        self.name = name
        self.running = False
        self.verbose = verbose

    def run(self):
        self.running = True
        print("{0} called".format(self.name))
        while self.running:
            time.sleep(0.1)

    def stop(self):
        self.running = False

    def __call__(self, value):
        if self.verbose:
            print("Actuator {0} called with value {1}".format(self.name, value))


class Robot():
    def __init__(self, session, verbose=True):
        self.sensors = dict()
        self.actuators = dict()

    def get_sensor(self, stream):
        sensorinstance = MockSensor(stream.sensor.name)
        self.sensors[stream.uuid] = sensorinstance
        return sensorinstance

    def get_actuator(self, stream):
        actuatorinstance = MockActuator(stream.actuator.name)
        self.actuators[stream.uuid] = actuatorinstance
        return actuatorinstance

    def stop(self):
        for sensorId, sensor in self.sensors.iteritems():
            sensor.running = False
        for actuatorId, actuator in self.actuators.iteritems():
            actuator.running = False

