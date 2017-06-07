from neo4j.v1 import GraphDatabase, basic_auth, ResultError
from stream import *
import model

class Neo4jAdapter:
    def __init__(self, user, password, verbose=False):
        driver = GraphDatabase.driver("bolt://localhost",
                                      auth=basic_auth(user, password))
        self.session = driver.session()
        self.verbose = verbose

    def programs(self):
        result = self.session.run("MATCH (n:Program) "
                                  "RETURN id(n) as id, n.name as name")

        return [(record["id"], record["name"]) for record in result]

    def ids_from_programs(self, programs):
        return map(lambda program: program[0], programs)

    def program_ids(self):
        programs = self.programs()
        return self.ids_from_programs(programs)

    def streams(self, programId):
        cypher = "MATCH (n:Stream)-[:program]->(p:Program) " \
                 "WHERE ID(p) = {id} " \
                 "OPTIONAL MATCH (n)-[:sensor]->(s:Sensor) " \
                 "OPTIONAL MATCH (n)-[:actuator]->(a:Actuator) " \
                 "RETURN id(n) as id, n.name as name, " \
                 "       s.name as sensor, a.name as actuator"
        parameters = {'id': programId}
        result = self.session.run(cypher, parameters)
        return [
            (record["id"], record["name"],
             record["sensor"], record["actuator"]) for record in result]

    def ids_from_streams(self, streams):
        return map(lambda stream: stream[0], streams)

    def stream_ids(self, programId):
        streams = self.streams(programId)
        return self.ids_from_streams(streams)

    def start_streams(self, programId):
        cypher = "MATCH (n:Stream)-[:program]->(p:Program), " \
                 "      (n)-[:sensor]->(s:Sensor) " \
                 "WHERE ID(p) = {id} " \
                 "RETURN id(n) as id, n.name as name"
        parameters = {'id': programId}
        result = self.session.run(cypher, parameters)

        return [(record["id"], record["name"]) for record in result]

    @staticmethod
    def program_query():
        builder = CypherBuilder()
        builder.match(
            ["(stream:Stream)-[:program]->(program:Program)"],
            [
                "id(program) = {program}"
            ]
        ).optional_match(
            [
                "(program)-[:parameter]->(programParam:Parameter)",
                "(programParam)-[:type]->(programParamType:Type)"
             ]
        ).optional_match(
            ["(stream)-[relation]->(directlyRelatedStream:Stream)"]
        ).optional_match(
            [
                "(stream)-[:in]->(operation:Operation)",
                "(operation)-[:out]->(streamWithHelper:Stream)"
            ]
        ).optional_match(
            [
                "(operation)-[:helper]->(helper:Helper)"
            ]
        ).optional_match(
            ["(stream)-[:actuator]->(actuator:Actuator)"]
        ).optional_match(
            ["(stream)-[:sensor]->(sensor:Sensor)"]
        ).optional_match(
            ["(stream)-[:parameter]->(paramInstance:ParameterInstance)"]
        ).optional_match(
            ["(paramInstance)-[:instance_of]->(paramDef:ParameterDefinition)"]
        ).optional_match(
            ["(paramDef)-[:type]->(paramType:Type)"]
        ).return_part(
            [
                "programParam",
                "programParamType",
                "stream",
                "sensor",
                "type(relation) as relationType",
                "relation",
                "directlyRelatedStream",
                "operation",
                "helper",
                "streamWithHelper",
                "actuator",
                "paramInstance",
                "paramDef",
                "paramType"
            ]
        )

        return builder.build()

    def repository(self, program_id):
        repository = model.Repository()

        self.load_operators(repository)

        cypher = self.program_query()
        parameters = {'program': program_id}
        result = self.session.run(cypher, parameters)

        try:
            result.peek()
        except ResultError:
            return None

        for record in result:
            programParam = record["programParam"]
            programParamType = record["programParamType"]
            stream = record["stream"]
            rtype = record["relationType"]
            relation = record["relation"]
            related_stream = record["directlyRelatedStream"]
            operation = record["operation"]
            ophelper = record["helper"]
            stream_helper = record["streamWithHelper"]
            sensor = record["sensor"]
            actuator = record["actuator"]
            paramInstance = record["paramInstance"]
            paramDef = record["paramDef"]
            paramType = record["paramType"]

            if sensor is None:
                sensor_uuid = None
            else:
                sensor_uuid = repository.find_or_add_sensor(
                    str(stream["uuid"]), str(sensor["name"])
                )

            if actuator is None:
                actuator_uuid = None
            else:
                actuator_uuid = repository.find_or_add_actuator(
                    actuator["uuid"], actuator["name"]
                )

            # program parameters
            if programParam is not None:
                repository.add_parameter_if_new(
                    model.Parameter(programParam["name"],
                                    programParam["value"],
                                    programParamType["name"])
                )

            stream_parameter = None
            if paramInstance is not None:
                stream_parameter = model.Parameter(
                    str(paramDef["name"]), paramInstance["value"], str(paramType["name"])
                )

            stream_instance = repository.find_or_add_stream(
                stream["uuid"], stream["name"],
                sensor_uuid, actuator_uuid, stream_parameter
            )

            # direct relationship between two streams
            if rtype is not None:
                params = {
                    "source": stream_instance,
                    "target": repository.find_or_add_stream(
                        related_stream["uuid"], related_stream["name"],
                        None, None, None
                    ),
                    "repository": repository
                }
                for key, value in relation.properties.items():
                    if key == u'name':
                        continue
                    elif key == u'body':
                        params['body'] = value
                    else:
                        params[key] = value

                repository.find_or_add_operation(
                    relation["uuid"], stream_instance,
                    rtype, params
                )

            # relationship with intermediary node
            if operation is not None:
                params = {
                    "target": repository.find_or_add_stream(
                        stream_helper["uuid"],
                        stream_helper["name"],
                        None, None, None
                    ),
                    "repository": repository
                }

                if ophelper is not None:
                    params["helper"] = repository.find_or_add_helper(
                        ophelper["uuid"], ophelper["name"], ophelper["body"]
                    )

                if repository.operation_models[operation["name"]].inc == '1':
                    params["source"] = stream_instance
                else:
                    params["sources"] = [stream_instance]

                for key, value in operation.properties.items():
                    if key == u'name':
                        continue
                    else:
                        params[key] = value

                selected_operation = repository.find_or_add_operation(
                    operation["uuid"], stream_instance,
                    operation["name"], params
                )

        return repository

    def load_operators(self, repository):
        result = self.session.run("MATCH (n:OperationType) "
                                  "RETURN {"
                                  "  uuid: n.uuid, "
                                  "  name: n.name, "
                                  "  inc: n.in "
                                  "} as op")
        for record in result:
            operation = record["op"]
            repository.add_operation_model(**operation)


class CypherBuilder:
    def __init__(self):
        self.matches = []
        self.optional_matches = []
        self.returns = ""

    def match(self, parts, wheres=[]):
        parts_assembled = ", ".join(parts)
        self.matches.append("MATCH " + parts_assembled)
        if len(wheres) > 0:
            wheres_assembled = ", ".join(wheres)
            self.matches.append(" WHERE " + wheres_assembled)
        return self

    def optional_match(self, parts, wheres=[]):
        parts_assembled = ", ".join(parts)
        self.optional_matches.append("OPTIONAL MATCH " + parts_assembled)
        if len(wheres) > 0:
            wheres_assembled = " AND ".join(wheres)
            self.optional_matches.append(" WHERE " + wheres_assembled)
        return self

    def return_part(self, parts):
        parts_assembled = ", ".join(parts)
        self.returns = "RETURN " + parts_assembled
        return self

    def build(self):
        matches_assembled = " ".join(self.matches)
        optional_matches_assembled = " ".join(self.optional_matches)
        parts = [matches_assembled]
        parts.extend([optional_matches_assembled])
        parts.append(self.returns)
        return " ".join(parts)

