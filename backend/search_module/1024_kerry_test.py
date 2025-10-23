from neo4j import GraphDatabase

driver = GraphDatabase.driver("neo4j+s://784ccc48.databases.neo4j.io", auth=("neo4j", "ruMHEra7m986cqtHZUFJ7By6xcvyOKia46fK1pvkhwo"))
try:
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN COUNT(n) AS count")
        print(result.single()["count"])
finally:
    driver.close()  # <— ensures proper cleanup