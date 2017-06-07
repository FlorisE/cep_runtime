import unittest
from engine import Engine
from model import Repository, Sensor, Actuator, Stream
from tests_model import get_sensor, get_actuator, get_stream


class EngineTests(unittest.TestCase):

    def setUp(self):
        adapter = None
        robot = None
        self.engine = Engine(adapter, robot)

    def test_constructor(self):
        self.assertEqual(self.engine.streams, [])



if __name__ == '__main__':
   unittest.main()

