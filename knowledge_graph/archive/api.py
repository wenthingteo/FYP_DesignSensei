# api.py
# for Django
from fastapi import FastAPI, UploadFile, File, HTTPException
from knowledge_graph.archive.text_extraction import ResourceProcessor
from config import STORAGE_CONFIG, DB_PATH

app = FastAPI()
processor = ResourceProcessor(STORAGE_CONFIG, DB_PATH)

@app.post("/resources/")
async def upload_resource(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pdf', '.pptx')):
            raise HTTPException(400, "Unsupported file type")
        
        # Process upload
        resource_id = processor.add_new_resource(
            file.filename,
            file.filename.split('.')[-1],
            file.file
        )
        
        return {"id": resource_id, "filename": file.filename}
    
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/process/")
async def process_resources():
    try:
        processor.process_new_resources()
        return {"status": "processing_started"}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/status/{resource_id}")
async def get_status(resource_id: int):
    # Implementation to get status from DB
    return {"status": "processed"}

# Add more endpoints as needed