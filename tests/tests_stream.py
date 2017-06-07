from __future__ import print_function
import unittest
import stream


class Called:
    def __init__(self):
        self.called = False
        self.value = None
        self.calledCounter = 0


class TestMap(unittest.TestCase):

    @staticmethod
    def closure(called):
        def func(value):
            called.called = True
            called.value = value
            called.calledCounter += 1

        return func

    def setUp(self):
        self.stream = stream.Stream()

    def test_creates_stream(self):
        self.assertIsNotNone(self.stream)

    def test_map_without_args_raises_typerror(self):
        with self.assertRaises(TypeError):
            # noinspection PyArgumentList
            self.stream.map()

    def test_map_without_proc_raises_valueerror(self):
        with self.assertRaises(ValueError):
            # noinspection PyArgumentList
            self.stream.map(None)

    def test_map_with_helpershow_returns_stream(self):
        stream2 = self.stream.map(lambda a: a)
        self.assertIsInstance(stream2, stream.Stream)

    def test_map(self):
        stream2 = self.stream.map(lambda a: a + "test")

        called = Called()
        closure = self.closure(called)

        self.assertFalse(called.called)

        stream2.subscribe(closure)
        self.stream.out("test")

        self.assertTrue(called.called)
        self.assertEquals(called.value, "testtest")

    def test_filter(self):
        stream2 = self.stream.filter(lambda item: item is True)

        called = Called()
        closure = self.closure(called)

        self.assertFalse(called.called)

        stream2.subscribe(closure)

        self.stream.out(False)

        self.assertFalse(called.called)
        self.assertIsNone(called.value)

        self.stream.out(True)

        self.assertTrue(called.called)
        self.assertTrue(called.value)


class TestSignal(unittest.TestCase):

    def test_connect_single(self):
        signal = stream.Signal()
        operation = stream.NullOperation()
        signal.connect(operation)
        self.assertIn(operation, signal.subscribers)

    def test_connect_multiple(self):
        signal = stream.Signal()
        operations = [stream.NullOperation() for i in range(1, 5)]
        for operation in operations:
            signal.connect(operation)

        for operation in operations:
            self.assertIn(operation, signal.subscribers)

    def test_invoke_single(self):
        signal = stream.Signal()
        operation = stream.NullOperation()
        signal.connect(operation)
        signal("test")
        self.assertEquals(operation.value, "test")

    def test_invoke_multiple(self):
        signal = stream.Signal()
        operations = [stream.NullOperation() for _ in range(1, 5)]
        for operation in operations:
            signal.connect(operation)

        signal("test")

        for operation in operations:
            self.assertEquals(operation.value, "test")


if __name__ == '__main__':
    unittest.main()
