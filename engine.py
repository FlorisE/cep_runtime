from stream import Stream, ManyToOneOperation
from collections import *
from math import *  # noqa: F403,F401
import model


def engine_factory(engine, adapter, robot, verbose):
    if engine == "0.1":
        return Engine(adapter, robot, verbose)
    return TestEngine(adapter, robot, verbose)


def operation_factory(op_model, source, target, helpers):
    op_type = type(op_model)

    if op_type is model.MapOperation:
        operation = source.map(target, get_proc(op_model, helpers))
    elif op_type is model.FilterOperation:
        operation = source.filter(target, get_proc(op_model, helpers))
    elif op_type is model.SubscribeOperation:
        operation = source.subscribe(target)
    elif op_type is model.CombineOperation:
        operation = source.combine(op_model.uuid, target, get_proc(op_model, helpers))
    elif op_type is model.MergeOperation:
        operation = source.merge(op_model.uuid, target)
    elif op_type is model.TimestampOperation:
        operation = source.timestamp(target)
    elif op_type is model.SampleOperation:
        operation = source.sample(target, op_model.rate)
    elif op_type is model.ForgetAfterOperation:
        operation = source.forgetAfter(target, op_model.rate)
    else:
        raise(Exception("Unknown operation: {0}".format(op_model)))

    source.outsignal.connect(operation)

    return operation


def get_proc(op_model, helpers):
    if op_model.body:
        if op_model.numsources == "*":
            temp_parameters = []
            for stream in op_model.sources:
                temp_parameters.append(stream.name.replace(" ", "_").lower())
            parameters = ", ".join(temp_parameters)
        elif op_model.numsources == 1:
            parameters = op_model.source.name.replace(" ", "_").lower()
        expression = "lambda " + parameters + ": " + op_model.body
        return expression, eval(expression)
    if op_model.helper:
        return op_model.helper.name, helpers[op_model.helper.name]


class TestEngine(object):
    def __init__(self, adapter, robot, verbose=True):
        pass
    def load(self, program):
        pass
    def start(self):
        pass
    def stop(self):
        pass


    
class Engine(object):

    def __init__(self, adapter, robot, verbose=False):
        # Thread.__init__(self)
        self.adapter = adapter
        self.robot = robot
        self.roots = []
        self.stream_map = dict()
        self.verbose = verbose
        self.sensors = []
        self.actuators = []
        self.helpers = []
        self.helper_funcs = dict()
        self.streamInstances = {}
        self.operations = []
        self.repository = None

    def load(self, program):
        self.repository = self.adapter.repository(program)

        self.parameters = self.repository.parameters
        self.helpers = self.repository.helpers

    def start(self):
        self.init_program_parameters()
        self.init_helpers()

        for stream in self.start_streams:
            self.init_stream(stream)

        self.robot.start()

    @property
    def start_streams(self):
        return [stream for stream in self.repository.streams
                if stream.sensor is not None]

    def init_program_parameters(self):
        for parameter in self.parameters:
            exec("global {0}".format(parameter.name))
            exec("{0} = {1}".format(parameter.name, parameter.value))

    def init_helpers(self):
        for helper in self.helpers:
            print("Initializing helper {0}".format(helper.name))
            exec(helper.body)
            self.helper_funcs[helper.name] = eval(helper.name)

    def init_stream(self, stream, parent=None):
        sensor = None
        actuator = None

        if stream.sensor:
            sensor = self.robot.get_sensor(stream.sensor, stream.parameters)
            self.sensors.append(sensor)

        if stream.actuator:
            actuator = self.robot.get_actuator(stream.actuator, stream.parameters)
            self.actuators.append(actuator)

        streamInstance = Stream(stream.uuid, stream.name, sensor, actuator, self.verbose)
        self.streamInstances[stream.uuid] = streamInstance
        for operation in stream.targets:
            if operation.target.uuid not in self.streamInstances.keys():
                target = self.init_stream(operation.target, streamInstance)
                operation = operation_factory(operation, streamInstance,
                                              target, self.helper_funcs)
                self.operations.append((streamInstance, operation, target))
            else:
                operation = [o for s, o, t in self.operations if t == self.streamInstances[operation.target.uuid]][0]
                if issubclass(type(operation), ManyToOneOperation):
                    operation.add_source(streamInstance)
                streamInstance.outsignal.connect(operation)

        # if parent is not None:
        #     parent.append(streamInstance)
        # else:
        #    self.roots.append(streamInstance)

        return streamInstance

    def stop(self):
        for stream in self.streamInstances.values():
            stream.complete()
