from flask import Flask
from flask import jsonify
from flask_restful import reqparse
from adapters.neo4jadapter import Neo4jAdapter
app = Flask(__name__)

adapter = Neo4jAdapter("neo4j", "rrp")


@app.route("/")
def index():
    pass


@app.route("/program/<id>")
def program(id):
    convertedId = int(id)

    return jsonify(adapter.streams(convertedId))


@app.route("/program/<id>/run", )
def run(id):
    convertedId = int(id)
    parser = reqparse.RequestParser()
    parser.add('id', type=int)
    parser.add('name', type=str)

    # args = parser.parse_args()
    program_ids = adapter.program_ids()
    if convertedId not in program_ids:
        raise("Not a valid program id")

    robot_factory()

@app.route("/sensor/<id>", methods=['POST'])
def sensor(id):
    pass

if __name__ == "__main__":
    app.run()

