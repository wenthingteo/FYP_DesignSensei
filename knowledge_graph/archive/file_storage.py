# file_storage.py
import os
import boto3
from azure.storage.blob import BlobServiceClient
from google.cloud import storage
from typing import BinaryIO, List

class StorageAdapter:
    def __init__(self, config: dict):
        self.config = config
        self.storage_type = config.get('storage_type', 'local')
        
        if self.storage_type == 's3':
            self.client = boto3.client(
                's3',
                aws_access_key_id=config['access_key'],
                aws_secret_access_key=config['secret_key'],
                region_name=config['region']
            )
        elif self.storage_type == 'azure':
            self.client = BlobServiceClient.from_connection_string(config['connection_string'])
        elif self.storage_type == 'gcp':
            self.client = storage.Client.from_service_account_json(config['credentials_path'])
        else:  # local
            self.base_path = config.get('base_path', './knowledge_graph/resource')
            os.makedirs(self.base_path, exist_ok=True)

    def upload_file(self, file_name: str, file_data: BinaryIO):
        if self.storage_type == 's3':
            self.client.upload_fileobj(file_data, self.config['bucket_name'], file_name)
        elif self.storage_type == 'azure':
            blob_client = self.client.get_blob_client(container=self.config['container_name'], blob=file_name)
            blob_client.upload_blob(file_data)
        elif self.storage_type == 'gcp':
            bucket = self.client.bucket(self.config['bucket_name'])
            blob = bucket.blob(file_name)
            blob.upload_from_file(file_data)
        else:  # local
            file_path = os.path.join(self.base_path, file_name)
            with open(file_path, 'wb') as f:
                f.write(file_data.read())

    def download_file(self, file_name: str) -> BinaryIO:
        if self.storage_type == 's3':
            response = self.client.get_object(Bucket=self.config['bucket_name'], Key=file_name)
            return response['Body']
        elif self.storage_type == 'azure':
            blob_client = self.client.get_blob_client(container=self.config['container_name'], blob=file_name)
            return blob_client.download_blob().readall()
        elif self.storage_type == 'gcp':
            bucket = self.client.bucket(self.config['bucket_name'])
            blob = bucket.blob(file_name)
            return blob.download_as_bytes()
        else:  # local
            file_path = os.path.join(self.base_path, file_name)
            with open(file_path, 'rb') as f:
                return f.read()

    def list_files(self) -> List[str]:
        if self.storage_type == 's3':
            response = self.client.list_objects_v2(Bucket=self.config['bucket_name'])
            return [obj['Key'] for obj in response.get('Contents', [])]
        elif self.storage_type == 'azure':
            container_client = self.client.get_container_client(self.config['container_name'])
            return [blob.name for blob in container_client.list_blobs()]
        elif self.storage_type == 'gcp':
            bucket = self.client.bucket(self.config['bucket_name'])
            return [blob.name for blob in bucket.list_blobs()]
        else:  # local
            return [f for f in os.listdir(self.base_path) 
                   if os.path.isfile(os.path.join(self.base_path, f))]