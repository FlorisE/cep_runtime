def create_operation(name, params):
    if name is None:
        raise ValueError("name")

    name_str = name[0].upper() + name[1:]

    function = globals()[name_str + "Operation"]
    # functionInspect = inspect.getargspec(function.__init__)

    return function(**params)


class Repository:

    def __init__(
            self,
            streams=[],
            sensors=[],
            actuators=[],
            operations=[],
            helpers=[],
            operation_models={},
            parameters=[]
    ):
        self.streams = streams
        self.sensors = sensors
        self.actuators = actuators
        self.operations = operations
        self.helpers = helpers
        self.operation_models = operation_models
        self.parameters = parameters

    def add_parameter_if_new(self, parameter):
        params = [param for param in self.parameters
                  if parameter.name is not param.name]
        if len(params) == 0:
            self.parameters.append(parameter)

    def find_or_add_sensor(self, uuid, name):
        # find existing sensor
        sensor = None
        for item in self.sensors:
            if item.uuid == uuid:
                sensor = item

        # add sensor if it doesn't exist
        if sensor is None:
            sensor = Sensor(self, uuid, name)

        #if paramType == "integer":
        #    sensor.parameters[paramName] = int(paramValue)

        return sensor

    def find_or_add_actuator(self, uuid, name):
        # find existing actuator
        actuator = None
        for item in self.actuators:
            if item.uuid == uuid:
                actuator = item

        # add actuator if it doesn't exist
        if actuator is None:
            actuator = Actuator(self, uuid, name)

        return actuator

    def find_or_add_stream(self, uuid, name, sensor, actuator, parameter):
        stream = None
        for item in self.streams:
            if item.uuid == uuid:
                stream = item

        if stream is None:
            stream = Stream(self, uuid, name, sensor, actuator)
        if parameter:
            stream.parameters[parameter.name.lower()] = parameter.value

        return stream

    def add_operation_model(self, uuid, name, inc):
        self.operation_models[name] = OperationModel(self, uuid, name, inc)

    def find_or_add_helper(self, uuid, name, body):
        helper = None
        for item in self.helpers:
            if item.uuid == uuid:
                helper = item
                break

        if helper is None:
            helper = Helper(self, uuid, name, body)

        return helper

    def find_or_add_operation(self, uuid, stream, name, params):
        selected_operation = None
        for item in self.operations:
            if item.uuid == uuid:
                if self.operation_models[name].inc == u'*':
                    item.sources.append(stream)
                selected_operation = item
                break

        if selected_operation is None:
            selected_operation = create_operation(name, params)

        if selected_operation not in stream.targets:
            stream.targets.append(selected_operation)

        return selected_operation


class Stream:
    def __init__(
            self, repository, uuid, name,
            sensor, actuator, source=None, targets=None
    ):
        self.repository = repository
        self.uuid = uuid
        self.name = name
        self.sensor = sensor
        self.actuator = actuator
        self.source = source
        self.targets = targets or []
        self.parameters = {}

        repository.streams.append(self)


class RepOp(object):
    def __init__(self, repository, source, target):
        self.repository = repository

        if type(source) is list:
            for src in source:
                src.targets.append(self)
        else:
            source.targets.append(self)

        target.source = self
        repository.operations.append(self)


class ManyToOne(RepOp):
    def __init__(self, repository, source, target):
        RepOp.__init__(self, repository, source, target)
        self.numsources = '*'
        self.numtargets = 1


class OneToOne(RepOp):
    def __init__(self, repository, source, target):
        RepOp.__init__(self, repository, source, target)
        self.numsources = 1
        self.numtargets = 1



class OperationModel:
    def __init__(self, repository, uuid, name, inc):
        self.repository = repository
        self.uuid = uuid
        self.name = name
        self.inc = inc


class MapOperation(OneToOne):
    def __init__(self, repository, uuid, source, target,
                 body=None, helper=None):
        super(MapOperation, self).__init__(repository, source, target)
        self.uuid = uuid
        self.source = source
        self.target = target
        self.body = body
        self.helper = helper


class FilterOperation(OneToOne):
    def __init__(self, repository, uuid, source, target,
                 body=None, helper=None):
        super(FilterOperation, self).__init__(repository, source, target)
        self.uuid = uuid
        self.source = source
        self.target = target
        self.body = body
        self.helper = helper


class SampleOperation(OneToOne):
    def __init__(self, repository, uuid, source, target, rate):
        super(SampleOperation, self).__init__(repository, source, target)
        self.uuid = uuid
        self.source = source
        self.target = target
        self.rate = int(rate)


class ForgetAfterOperation(OneToOne):
    def __init__(self, repository, uuid, source, target, rate):
        super(ForgetAfterOperation, self).__init__(repository, source, target)
        self.uuid = uuid
        self.source = source
        self.target = target
        self.rate = int(rate)


class TimestampOperation(OneToOne):
    def __init__(self, repository, uuid, source, target):
        super(TimestampOperation, self).__init__(repository, source, target)
        self.uuid = uuid
        self.source = source
        self.target = target


class SubscribeOperation(OneToOne):
    def __init__(self, repository, uuid, source, target):
        super(SubscribeOperation, self).__init__(repository, source, target)
        self.uuid = uuid
        self.source = source
        self.target = target


class CombineOperation(ManyToOne):
    def __init__(
            self, repository, uuid, sources, target,
            body=None, helper=None
    ):
        super(CombineOperation, self).__init__(repository, sources, target)
        self.uuid = uuid
        self.sources = sources
        self.target = target
        self.body = body
        self.helper = helper


class MergeOperation(ManyToOne):
    def __init__(self, repository, uuid, sources, target):
        super(MergeOperation, self).__init__(repository, sources, target)
        self.uuid = uuid
        self.sources = sources
        self.target = target
        

class Actuator:
    def __init__(self, repository, uuid, name, parameters={}):
        self.repository = repository
        self.uuid = uuid
        self.name = name
        self.parameters = parameters

        repository.actuators.append(self)


class Sensor:
    def __init__(self, repository, uuid, name, parameters={}):
        self.repository = repository
        self.uuid = uuid
        self.name = name
        self.parameters = parameters

        repository.sensors.append(self)


class Helper:
    def __init__(self, repository, uuid, name, body):
        self.repository = repository
        self.uuid = uuid
        self.name = name
        self.body = body

        repository.helpers.append(self)


class Parameter:
    def __init__(self, name, value, type):
        if type == 'list':
            self.value = map(lambda i: str(i), value)
        elif type == 'string':
            self.value = str(value)
        elif type == 'integer':
            self.value = int(value)
        else:
            self.value = value

        self.name = name
        self.type = type
