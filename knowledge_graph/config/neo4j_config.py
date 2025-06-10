# knowledge_graph/config/neo4j_config.py
import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_CONFIG = {
    "uri": os.getenv("NEO4J_URI"),
    "username": os.getenv("NEO4J_USERNAME"), 
    "password": os.getenv("NEO4J_PASSWORD"),
    "database": os.getenv("NEO4J_DATABASE", "neo4j")
}