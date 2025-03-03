from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
from rag import RAG


app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the RAG class with web_urls
web_urls = [
    "https://www.w3schools.com/mysql/mysql_intro.asp",
    "https://www.w3schools.com/mysql/mysql_rdbms.asp",
    "https://www.w3schools.com/mysql/mysql_sql.asp",
    "https://www.w3schools.com/mysql/mysql_where.asp",
    "https://www.w3schools.com/mysql/mysql_and_or.asp",
    "https://www.w3schools.com/mysql/mysql_orderby.asp",
    "https://www.w3schools.com/mysql/mysql_insert.asp",
    "https://www.w3schools.com/mysql/mysql_null_values.asp",
    "https://www.w3schools.com/mysql/mysql_update.asp"
]

rag_instance = RAG(web_urls)

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

if __name__ == '__main__':
    uvicorn.run('main:app', host="localhost", port=8000, reload=True)