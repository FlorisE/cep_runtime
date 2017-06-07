from neo4j.v1 import GraphDatabase, basic_auth
import uuid

driver = GraphDatabase.driver("bolt://localhost",
                              auth=basic_auth("neo4j", "neo4j"))
session = driver.session()

result = session.run("MATCH (n) "
                     "OPTIONAL MATCH (n)-[r]-(n2) "
                     "RETURN ID(n) as nodeId, ID(r) as relationId")

for record in result:
    node_id = record["nodeId"]
    relation_id = record["relationId"]

    result2 = session.run(
        "MATCH (n) "
        "WHERE ID(n) = {id} "
        "SET n.uuid = {uuid}",
        {
            "id": node_id,
            "uuid": str(uuid.uuid4())
        }
    )

    if relation_id is not None:
        result3 = session.run(
            "MATCH (n)-[r]-(n2) "
            "WHERE ID(r) = {id} "
            "SET r.uuid = {uuid}",
            {
                "id": relation_id,
                "uuid": str(uuid.uuid4())
            }
        )

        print(result3)


raw_input("wait a bit for queries to finish")