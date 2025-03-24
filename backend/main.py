from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
from rag import RAG
import boto3


app = FastAPI()

origins = ["http://localhost:3000", "ws://localhost:3000", "sql-sense.vercel.app"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

s3_access_key = os.getenv('S3_ACCESS_KEY')
s3_secret_access_key = os.getenv('S3_SECRET_ACCESS_KEY')
bucket_name = os.getenv('S3_BUCKET_NAME')
file_key = os.getenv('S3_FILE_KEY')

s3_client = boto3.client('s3',
                         aws_access_key_id=s3_access_key,
                         aws_secret_access_key=s3_secret_access_key)

def get_urls_s3(bucket_name, file_key):
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    content = response['Body'].read().decode('utf-8')
    return content

urls_content = get_urls_s3(bucket_name, file_key)
lines = urls_content.split("\n")
MySQL_WEB_URLS = []
PostgreSQL_WEB_URLS = []
MongoDB_WEB_URLS = []

for line in lines:
    if line.startswith("MySQL_WEB_URLS="):
        MySQL_WEB_URLS = line.split("=", 1)[1].split(",")
    elif line.startswith("PostgreSQL_WEB_URLS="):
        PostgreSQL_WEB_URLS = line.split("=", 1)[1].split(",")
    elif line.startswith("MongoDB_WEB_URLS="):
        MongoDB_WEB_URLS = line.split("=", 1)[1].split(",")

WEB_URLS = MySQL_WEB_URLS + PostgreSQL_WEB_URLS + MongoDB_WEB_URLS
# print(WEB_URLS)

rag_instance = RAG(WEB_URLS)

class QueryRequest(BaseModel):
    user_input: str

class QueryResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {"message": "root"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("Accepting websocket connection")
    await websocket.accept()
    print("Websocket connection accepted")
    try:
        vectorstore_created = False
        while True:
            data = await websocket.receive_text()
            print("Query is", data)
            response, vectorstore_created = rag_instance.query_answer(data, vectorstore_created)
            await websocket.send_text(response)
            print("Sent response", response)
    except WebSocketDisconnect:
        print("WebSocket connection closed")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    uvicorn.run('main:app', host="localhost", port=8000, reload=True)