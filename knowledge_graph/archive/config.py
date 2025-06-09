# config.py
# Google Cloud Storage
# For development
STORAGE_CONFIG = {
    'storage_type': 'local',
    'base_path': './knowledge_graph/resource'
}

NEO4J_CONFIG = {
    'uri': "neo4j+s://025d7462.databases.neo4j.io",
    'user': "neo4j",
    'password': "D26smsX1j8nNNlAsf5jKANwlfcm0K94vh6dFY2o9dj0",
    'database': "neo4j"
}
# For production
STORAGE_CONFIG = {
    'storage_type': 's3',
    'bucket_name': 'design-sensei-kg-bucket',
    'access_key': 'GOOGQDLGHNQ5TEXL2SQ7WDGM',
    'secret_key': 'qgFy0XsLD3DcIX22SbHMvTGlSKtE0F474mVtJF+J',
    'region': ' asia-southeast1'
}