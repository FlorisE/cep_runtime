#import naoqi #import qi
from adapters.neo4jadapter import *
from stream import *
from threading import Thread
import socket
import time
import sys


class Connection(Thread):
    def __init__(self, host, port=6000):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.running = True
        self.send = None

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        while self.running:
            if self.send != None:
                s.sendall(self.send)
                self.send = None
            time.sleep(0.1)
        s.close()

# forward compatibility
try: input = raw_input
except NameError: pass

#app = qi.Application()
#app.start()
#session = app.session/

adapter = Neo4jAdapter("neo4j", "rrp")

command = ""
repository = None
programs = adapter.programs()
program_ids = adapter.ids_from_programs(programs)
program_id = None
stream_ids = None
stream_id = None

print "Use SHOW COMMANDS to get a list of commands"

CMD_CONNECT = "CONNECT"
CMD_DISCONNECT = "DISCONNECT"
CMD_STIM = "STIMULATE"
CMD_SHOW_PROGS = "SHOW PROGRAMS"
CMD_LOAD_PROG = "LOAD PROGRAM"
CMD_SHOW_STREAMS = "SHOW STREAMS"
CMD_SHOW_OUT_STREAMS = "SHOW OUT STREAMS"
CMD_SHOW_IN_STREAMS = "SHOW IN STREAMS"
CMD_SHOW_OUT_OPS = "SHOW OUT OPS"
CMD_SHOW_IN_OPS = "SHOW IN OPS"
CMD_SHOW_START_STREAMS = "SHOW START STREAMS"
CMD_LOAD_STREAM = "LOAD STREAM"
CMD_SHOW_COMMANDS = "SHOW COMMANDS"
CMD_EXIT = "EXIT"


def read_or_request(command_def, command, prompt):
    destination = -1
    if len(command_def) < len(command):
        destination = command[len(command_def):].strip()
    else:
        destination = input(prompt)
    return destination


def read_or_request_id(command_def, command):
    destination = -1
    if len(command_def) < len(command):
        destination = int(command[len(command_def):])
    else:
        while True:
            try:
                destination = int(input("Load id: "))
                break
            except ValueError:
                print("Not a number")
    return destination

connection = None

while True:
    command = input("Enter command: ").strip()
    command_upper = command.upper()
    if command_upper.startswith(CMD_CONNECT):
        if connection is not None:
            print("Please first disconnect")
            continue
        target = read_or_request(CMD_CONNECT, command, "Target HOST:PORT")
        target_split = target.split(':')
        HOST = None
        PORT = 6000
        if len(target_split) > 0:
            HOST = target_split[0]
        if len(target_split) > 1:
            PORT = int(target_split[1])
        connection = Connection(HOST, PORT)
        connection.start()
    elif command_upper.startswith(CMD_STIM):
        if connection is None:
            print("Not currently connected")
        else:
            target = read_or_request(CMD_STIM, command, "Target UUID: ")
            connection.send = target
    elif command_upper.startswith(CMD_DISCONNECT):
        if connection is None:
            print("Not currently connected")
        else:
            connection.running = False
            print("Connection will be terminated")
            connection = None
    elif command_upper.startswith(CMD_SHOW_PROGS):
        print("Available programs:")
        for id, name in programs:
            print('{:^4} | {:15}'.format(id, name))
    elif command_upper.startswith(CMD_LOAD_PROG):
        program_id = read_or_request_id(CMD_LOAD_PROG, command)
        if program_id in program_ids:
            repository = adapter.repository(program_id)
            stream_ids = adapter.stream_ids(program_id)
        else:
            print("Not a valid program id")
            program_id = None 
    elif command_upper.startswith(CMD_SHOW_STREAMS):
        if program_id is None:
            print("A program has to be loaded before executing this command")
            continue
        for id, name, sensor, actuator in adapter.streams(program_id):
            print('{:^4} | {:40} | {:10} | {:10}'.format(id,
                                                         name,
                                                         sensor,
                                                         actuator))
    elif command_upper.startswith(CMD_SHOW_START_STREAMS):
        if program_id is None:
            print("A program has to be loaded before executing this command")
            continue
        start_streams = adapter.start_streams(program_id)
        for stream in start_streams:
            print(stream)
    elif command_upper.startswith(CMD_SHOW_OUT_STREAMS):
        stream_id = read_or_request_id(CMD_SHOW_OUT_STREAMS, command)
        if stream_id in stream_ids:
            pass
    elif command_upper.startswith(CMD_SHOW_COMMANDS):
        print """ 
SHOW [ PROGRAMS | ( START | IN | OUT ) STREAMS | [ IN | OUT ] OPS] 
LOAD [ PROGRAM | STREAM ]
SELECT [ PROGRAM | STREAM ]
(DIS)CONNECT
STIMULATE
EXIT 
"""
    elif command_upper.startswith(CMD_EXIT):
        break
    else:
        print "Unrecognized command";

if connection:
    connection.running = False

def construct_sensor(sensor):
    pass


def construct_graph(stream):
    if stream.sensor is not None:
        construct_sensor(stream.sensor)


