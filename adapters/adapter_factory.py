def adapter_factory(adapter, username, password, verbose):
    if adapter == "neo4j":
        from adapters.neo4jadapter import Neo4jAdapter
        return Neo4jAdapter(username, password, verbose)
    elif adapter == "test":
        from adapters.testadapter import TestAdapter
        return TestAdapter(username, password, verbose)    
    else:
        raise("No suitable adapter has been found")
