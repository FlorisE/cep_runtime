import argparse
from adapters.adapter_factory import adapter_factory
from robots.factory import robot_factory
from engine import engine_factory
from collections import *
from config import *
import sys
import robots.sock
import robots.nao
import robots.mock

parser = argparse.ArgumentParser(description="Load a CEP graph")
parser.add_argument('program_id', metavar='id', type=int)
parser.add_argument('--ip', metavar='ip', default="192.168.11.2")
parser.add_argument('--port', type=int, default=9559)
parser.add_argument('--protocol', default="tcp")
parser.add_argument('--robot', default="mock")
parser.add_argument('--adapter', default="neo4j")
parser.add_argument('--engine', default="0.1")
parser.add_argument('-v', '--verbose', action='store_const', const=True, default=False)
args = parser.parse_args()

running = True
reload = True
verbose = args.verbose

adapter = adapter_factory(args.adapter, user, password, verbose)

BlobMemory = None
FaceDetectionMemory = None
RedBallMemory = None
WordRecognizedMemory = None

BallDistance = namedtuple("BallDistance", ['ball', 'distance'])

while running:
    if reload:
        reload = False
        program_ids = adapter.program_ids()

        if args.program_id not in program_ids:
            print("Not a valid program id")
            exit()

        robot = robot_factory(args.robot, args.ip, args.port, args.protocol, 
                              verbose)
        BlobMemory = robot.BlobMemory
        FaceDetectionMemory = robot.FaceDetectionMemory
        RedBallMemory = robot.RedBallMemory
        WordRecognizedMemory = robot.WordRecognizedMemory
        engine = engine_factory(args.engine, adapter, robot, verbose)
        engine.load(args.program_id)
        engine.start()

    command = raw_input(
        "Type R<enter> to reload, Q<enter> to quit:\r\n" if args.verbose 
                                                     else "Ready\r\n"
    )
    if len(command) > 0:
        if command[0].upper() == 'R':
            reload = True
        if command[0].upper() == 'Q':
            print("Stopping")
            running = False
            robot.stop()
            engine.stop()
