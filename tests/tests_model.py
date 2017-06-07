import unittest
from uuid import uuid4
from model import Sensor, Actuator, Stream

def get_sensor(repository, name):
    return Sensor(repository, uuid4(), name)

def get_actuator(repository, name):
    return Actuator(repository, uuid4(), name)

def get_stream(repository, name, sensor, actuator, source=None, targets=None):
    return Stream(repository, uuid4(), name, sensor, actuator, source, targets)

class SensorTests(unittest.TestCase):

    def test_(self):
        pass
