from __future__ import print_function
from threading import Thread
import time


def pascal_case(value):
    """
    >>> pascal_case("just testing_this")
    "JustTestingThis"
    """
    retval = ""
    capitalize = True
    for c in value:
        if capitalize:
            retval += c.upper()
            capitalize = False
        elif c == ' ' or c == '_':
            capitalize = True
        else:
            retval += c
    return retval


class Actuator(object):
    def __init__(self, uuid):
        self.uuid = uuid

    def __call__(self, value):
        print("ACTUATOR CALLED: ", self.uuid)


# implementing classes need to have a sense method
class Sensor():
    def __init__(self, robot):
        self.robot = robot
        self.sensor_streams = []

    def tick(self):
        pass

    def register(self, stream):
        self.sensor_streams.append(stream)

    # can be overwritten by children to perform some initialization
    def start(self):
        pass

    def stop(self):
        pass


class SensorStream():
    def __init__(self, sensor):
        self.sensor = sensor
        self.sensor.register(self)
        self.subscribers = []
        self.active = False

    # can be overriden by children to perform some initialization
    def start(self):
        pass

    def deactivate(self):
        self.active = False

    def activate(self):
        self.active = True

    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)

    def publish(self, *_args):
        if self.active:
            for subscriber in self.subscribers:
                subscriber.publish(*_args)

    def tick(self):
        pass

    def stop(self):
        pass


class SequentialSensor(Sensor):
    def __init__(self, robot):
        Sensor.__init__(self, robot)
        self.lastTickIndex = 0

    def tick(self):
        if self.lastTickIndex > len(self.sensor_streams) -1:
            self.lastTickIndex = 0

        target = None
        for i, stream in enumerate(self.sensor_streams):
            if i == self.lastTickIndex:
                target = stream
            else:
                stream.deactivate()
        target.activate()
        target.tick()

        self.lastTickIndex += 1


class ParallelSensor(Sensor):
    def __init__(self, robot):
        Sensor.__init__(self, robot)

    def tick(self):
        for sensor_stream in self.sensor_streams:
            sensor_stream.activate()
            sensor_stream.tick()


class SingletonSensor(Sensor):
    def __init__(self, robot):
        Sensor.__init__(self, robot)

    def tick(self):
        for sensor_stream in self.sensor_streams:
            sensor_stream.tick()
