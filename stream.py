from datetime import datetime, timedelta  # NOQA: F401
import time
from threading import Thread
from collections import *


BallDistance = namedtuple("BallDistance", ['ball', 'distance'])


class Bunch(dict):
    def __getattr__(self, attr):
        return self[attr]

naryoperations = dict()


def printError(sourceId, destinationId, operation, body, value, error):
    print("ERROR IN HELPER OR BODY")
    print("Source ID: " + sourceId)
    print("Destination ID: " + destinationId)
    print("Operation: " + operation)
    print("To execute: " + body)
    value_type = type(value)
    if value_type is dict:
        print("Parameters:")
        for k, v in value.iteritems():
            print(str(k) + ": " + str(value))
    elif value_type is list:
        print("Parameters:")
        for i, v in enumerate(value):
            print(str(i) + ": " + str(v))
    else:
        print("Parameter: " + str(value))
    print("Error:")
    print(error)


class Stream:
    def __init__(self, uuid, name, sensor=None, actuator=None, verbose=False):
        self.outsignal = Signal(self)
        self.uuid = uuid
        self.name = name
        self.connections = []
        self.sensor = sensor
        self.actuator = actuator
        self.verbose = verbose

        if self.verbose:
            print("Initializing stream")

        if self.sensor is not None:
            sensor.subscribe(self)

    def subscribe(self, destination):
        if self.verbose:
            print("Subscribe called")
        return SubscribeOperation(destination)

    def map(self, destination, proc):
        if proc is None:
            raise ValueError("proc")

        if destination is None:
            raise ValueError("destination")

        if self.verbose:
            print("map called")

        return MapOperation(proc, destination)

    def filter(self, destination, proc):
        if destination is None:
            raise ValueError("destination")

        if proc is None:
            raise ValueError("proc")

        if self.verbose:
            print("filter called")

        return FilterOperation(proc, destination)

    def combine(self, uuid, destination, proc):
        if destination is None:
            raise ValueError("destination")

        if proc is None:
            raise ValueError("proc")

        if self.verbose:
            print("Combine called")

        operation = naryoperations.setdefault(uuid,
                                              CombineOperation(proc,
                                                               destination))

        operation.add_source(self)

        return operation

    def merge(self, uuid, destination):
        if destination is None:
            raise ValueError("destination")

        if self.verbose:
            print("Merge called")

        if uuid not in naryoperations:
            naryoperations[uuid] = MergeOperation(destination)

        operation = naryoperations[uuid]

        return operation

    def timestamp(self, destination):
        if destination is None:
            raise ValueError("destination")

        if self.verbose:
            print("Timestamp called")

        return TimestampOperation(destination)

    def sample(self, destination, rate):
        if destination is None:
            raise ValueError("destination")

        if rate is None:
            raise ValueError("rate")

        if self.verbose:
            print("Sample called")

        return SampleOperation(destination, rate)

    def forgetAfter(self, destination, rate):
        if destination is None:
            raise ValueError("destination")

        if rate is None:
            raise ValueError("rate")

        if self.verbose:
            print("ForgetAfter called")

        return ForgetAfterOperation(destination, rate)

    def publish(self, value):
        if self.verbose:
            print("Out called")
        # a list of parameters can be posted at the same time
        self.outsignal(value)
        if self.actuator is not None:
            self.actuator(value)


    def complete(self):
        if self.actuator is not None:
            self.actuator.stop()
        if self.sensor is not None:
            self.sensor.stop()
        self.outsignal.complete()


class CompletableOperation(object):
    def complete(self):
        try:
            if self.target:
                self.target.complete()
        except AttributeError:
            try:
                if self.targets:
                    for target in self.targets:
                        target.complete()
            except AttributeError:
                pass


class ManyToOneOperation(CompletableOperation):
    def __init__(self):
        self.sources = []

    def add_source(self, stream):
        self.sources.append(stream)


class SubscribeOperation(CompletableOperation):
    def __init__(self, target):
        self.target = target

    def __call__(self, source, value):
        print("call invoked on " + type(self).__name__)
        self.target.publish(value)


class MapOperation(CompletableOperation):
    def __init__(self, body, target):
        self.body_text = body[0]
        self.body = body[1]
        self.target = target

    def __call__(self, source, value):
        print("call invoked on " + type(self).__name__)
        try:
            self.target.publish(self.body(value))
        except Exception as err:
            printError(source.uuid, self.target.uuid, "map",
                       self.body_text, value, err)


class FilterOperation(CompletableOperation):
    def __init__(self, body, target):
        self.body_text = body[0]
        self.body = body[1]
        self.target = target

    def __call__(self, source, value):
        print("call invoked on " + type(self).__name__)
        try:
            if self.body(value):
                self.target.publish(value)
        except Exception as err:
            printError(source.uuid, self.target.uuid, "filter",
                       self.body_text, value, err)


class CombineOperation(ManyToOneOperation):
    def __init__(self, body, target):
        ManyToOneOperation.__init__(self)
        self.body_text = body[0]
        self.body = body[1]
        self.target = target
        self.latestValue = {}
        self.start_publishing = False

    def __call__(self, source, value):
        print("call invoked on " + type(self).__name__)

        self.latestValue[source.name.replace(" ", "_").lower()] = value
        self.start_publishing = self.start_publishing or len(self.latestValue) == len(self.sources)

        if self.start_publishing:
            try:
                self.target.publish(self.body(**self.latestValue))
            except Exception as err:
                printError(source.uuid, self.target.uuid, "Combine",
                           self.body_text, self.latestValue, err)


class MergeOperation(ManyToOneOperation):
    def __init__(self, target):
        ManyToOneOperation.__init__(self)
        self.target = target

    def __call__(self, source, value):
        print("call invoked on " + type(self).__name__)
        self.target.publish(value)


class TimestampOperation(CompletableOperation):
    def __init__(self, target):
        self.target = target
        self.start_time = time.time()

    def __call__(self, source, value):
        #print("call invoked on " + type(self).__name__)
        self.target.publish((time.time() - self.start_time, value))


class NullLatest():
    def __init__(self):
        pass


class SampleOperationTimer(Thread):
    def __init__(self, rate, operation):
        Thread.__init__(self)
        self.running = False
        self.ms = self.get_microseconds()
        self.rate = rate
        self.operation = operation
        self.nullLatest = NullLatest()
        self.latest = self.nullLatest

    def run(self):
        self.running = True
        while self.running:
            if self.get_microseconds() > self.ms + self.rate * 1000:
                self.ms = self.get_microseconds()
                if self.latest.__class__.__name__ != "NullLatest":
                    self.operation.publish(self.latest)
                    self.latest = self.nullLatest
            time.sleep(0.01)

    def publish(self, value):
        self.latest = value

    def stop(self):
        self.running = False

    def get_microseconds(self):
        return ((datetime.now().hour * 60 + datetime.now().minute) * 60 + datetime.now().second) * 10 ** 6 + datetime.now().microsecond


class SampleOperation(CompletableOperation):
    def __init__(self, target, rate):
        self.target = target
        self.rate = rate
        self.latest = NullLatest()
        self.timer = SampleOperationTimer(rate, self)
        self.timer.start()

    def complete(self):
        super(SampleOperation, self).complete()
        self.timer.stop()

    def __call__(self, source, value):
        self.timer.publish(value)

    def publish(self, value):
        self.target.publish(value)


class ForgetAfterOperationTimer(Thread):
    def __init__(self, rate, operation):
        Thread.__init__(self)
        self.running = False
        self.ms = self.get_microseconds()
        self.rate = rate
        self.operation = operation

    def run(self):
        self.running = True
        while self.running:
            if self.get_microseconds() > self.ms + self.rate * 1000:
                self.stop()
                self.operation.internal_publish(None)
            time.sleep(0.01)

    def reset(self):
        self.ms = self.get_microseconds()

    def stop(self):
        self.running = False

    def get_microseconds(self):
        return ((datetime.now().hour * 60 + datetime.now().minute) * 60 + datetime.now().second) * 10 ** 6 + datetime.now().microsecond


class ForgetAfterOperation(CompletableOperation):
    def __init__(self, target, rate):
        self.target = target
        self.rate = rate
        self.timer = None

    def complete(self):
        super(ForgetAfterOperation, self).complete()
        self.timer.stop()

    def __call__(self, source, value):
        self.publish(value)

    def publish(self, value):
        self.internal_publish(value)
        if self.timer is None or not self.timer.running:
            self.timer = ForgetAfterOperationTimer(self.rate, self)
            self.timer.start()
        else:
            self.timer.reset()

    def internal_publish(self, value):
        self.target.publish(value)


class SimpleTimer(Thread):
    def __init__(self, operation):
        Thread.__init__(self)
        self.operation = operation
        self.curr_time = time.time()
        self.delta = self.operation.rate / 1000
        self.exec_time = self.curr_time
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            self.curr_time = time.time()
            if self.curr_time > self.exec_time:
                self.exec_time = self.get_next_time()
                if self.operation.current_value_changed:
                    self.operation.publish()
            time.sleep(0.1)

    def stop(self):
        self.running = False

    def get_next_time(self):
        return self.exec_time + self.delta

    def stop(self):
        self.running = False


class NullOperation(CompletableOperation):
    def __init__(self):
        self.invoked = False
        self.value = None

    def __call__(self, value):
        print("call invoked on " + type(self).__name__)
        self.invoked = True
        self.value = value


class Signal(object):
    def __init__(self, source):
        self.source = source
        self.subscribers = []

    def connect(self, operation):
        self.subscribers.append(operation)

    def __call__(self, value):
        for subscriber in self.subscribers:
            subscriber(self.source, value)

    def complete(self):
        for subscriber in self.subscribers:
            subscriber.complete()
