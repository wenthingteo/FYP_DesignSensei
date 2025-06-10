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