# config.py
# Google Cloud Storage
# For development
STORAGE_CONFIG = {
    'storage_type': 'local',
    'base_path': './knowledge_graph/resource'
}

# For production
STORAGE_CONFIG = {
    'storage_type': 's3',
    'bucket_name': 'design-sensei-kg-bucket',
    'access_key': 'GOOGQDLGHNQ5TEXL2SQ7WDGM',
    'secret_key': 'qgFy0XsLD3DcIX22SbHMvTGlSKtE0F474mVtJF+J',
    'region': ' asia-southeast1'
}

NEO4J_CONFIG = {
    'uri': 'neo4j+s://4b96273b.databases.neo4j.io',
    'username': 'neo4j',
    'password': '6nPdHsszkli6ZKfc-6cWM1Nc_uUFrY3Karhx05pU2Hs',
    'database': 'neo4j',
    'keep_alive_interval_hours': 5
}

DATABASE_URL = 'postgresql://db_fyp_designsensei_user:PeEvhxGY10cT5N99238oeGculsKOvie4@dpg-d11i2i8dl3ps73cqlp00-a.oregon-postgres.render.com/db_fyp_designsensei'