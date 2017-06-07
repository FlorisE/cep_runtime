from threading import Thread
import socket
import select
import time


class Session():
    def __init__(self, ip, port, protocol, verbose=False):
        pass


class Bunch(dict):
    def __getattr__(self, attr):
        return self[attr]


class MockSensor(Thread):

    def __init__(self, name, verbose=False):
        Thread.__init__(self)
        self.name = name
        self.subscribers = []
        self.running = False
        self.verbose = verbose

    def run(self):
        if self.verbose:
            print "Sensor {0} started".format(self.name)
        while self.runninLeftFaceLedsRedg:
            time.sleep(0.1)

    def send(self, message):
        if self.verbose:
            print("Sending to {0} subscribers".format(len(self.subscribers)))
        if self.name == "ball":
            message = Bunch(width=50, height=50, x=10, y=10)
        elif self.name == "Head yaw":
            message = 1
        for subscriber in self.subscribers:
            subscriber.out(message)

    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)

    def stop(self):
        self.running = False


class MockActuator(Thread):

    def __init__(self, name, verbose=False):
        Thread.__init__(self)
        self.name = name
        self.running = False
        self.verbose = verbose

    def run(self):
        if self.verbose:
            print "Actuator {0} started".format(self.name)
        while self.running:
            time.sleep(0.1)

    def stop(self):
        self.running = False

    def __call__(self, value):
        if self.verbose:
            print("Actuator {0} called with value {1}".format(self.name, value))


class Robot():

    def __init__(self, session, verbose=False):
        if verbose:
            print ("Socket robot initialized")
        self.sensors = dict()
        self.actuators = dict()
        self.connectionHandler = ConnectionHandler(self.sensors,
                                                   self.actuators)
        self.connectionHandler.start()
        self.verbose = verbose

    def get_sensor(self, sensor):
        sensorinstance = MockSensor(sensor.name)
        self.sensors[sensor.uuid] = sensorinstance
        return sensorinstance

    def get_actuator(self, actuator):
        actuatorinstance = MockActuator(actuator.name)
        self.actuators[actuator.uuid] = actuatorinstance
        return actuatorinstance

    def stop(self):
        self.connectionHandler.stop()


class ConnectionHandler(Thread):
    def __init__(self, sensors, actuators):
        Thread.__init__(self)
        self.sensors = sensors
        self.actuators = actuators
        self.running = True

    def run(self):
        HOST = ''
        PORT = 6000
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        read_list = [server_socket]
        while self.running:
            try:
                r, _, _ = select.select(read_list, [], [], 10)
            except socket.error:
                continue
            for sr in r:
                if sr is server_socket:
                    client_socket, address = server_socket.accept()
                    read_list.append(client_socket)
                else:
                    data = sr.recv(1024)
                    if data:
                        target_uuid = data[0:36]
                        if len(data) > 36:
                            payload = ''.join(data[36:]).strip()
                        else:
                            payload = None
                        try:
                            target_sensor = self.sensors[target_uuid]
                        except KeyError:
                            print("Sensor not found")
                            continue

                        try:
                            target_sensor.send(eval(payload) if payload
                                               else "")
                        except:
                            print("Error with sending " + payload
                                  + " to target sensor")
                    else:
                        sr.close()
                        read_list.remove(sr)
        for read_socket in read_list:
            read_socket.close()

    def stop(self):
        self.running = False
