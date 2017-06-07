import robots.sock
import robots.mock
import robots.nao
import robots.nao_mock

def robot_factory(robot, ip, port, protocol, verbose):
    if robot == "nao":
        session = robots.nao.Session(ip, port, protocol)
        return robots.nao.Robot(session)
    elif robot == "nao_ms":
        session = robots.nao_mock.Session()
        return robots.nao.Robot(session)
    elif robot == "sock":
        session = robots.sock.Session(ip, port, protocol, verbose)
        return robots.sock.Robot(session, verbose)
    else:
        session = robots.mock.Session(ip, port, protocol, verbose)
        return robots.mock.Robot(session, verbose)
