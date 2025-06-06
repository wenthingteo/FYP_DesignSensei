# migrate_existing.py
# run it once to migrate existing resources to the new storage system
from file_storage import StorageAdapter
from resource_db import ResourceDB
from config import STORAGE_CONFIG
import os

def migrate_existing_resources(storage, db, base_path):
    for file_name in os.listdir(base_path):
        file_path = os.path.join(base_path, file_name)
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                storage.upload_file(file_name, f)
            resource_id = db.add_resource(file_name, file_name.split('.')[-1])
            print(f"Migrated {file_name} with ID {resource_id}")

if __name__ == "__main__":
    storage = StorageAdapter(STORAGE_CONFIG)
    db = ResourceDB()
    migrate_existing_resources(storage, db, './knowledge_graph/resource')