from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv

from groq import Groq

load_dotenv()
app = FastAPI()


class QueryRequest(BaseModel):
    user_input: str

class QueryResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {"message": "root"}

@app.post("/generate_sql")
async def generate_sql(request: QueryRequest):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY environment variable not set")
    
    client = Groq(api_key=api_key)
    content = """You are a database expert in SQL and you are helping a user with generating queries by converting natural language to SQL queries. \n\nUser says: """
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-specdec",
            messages=[
                {
                    "role": "user",
                    "content": content + request.user_input
                }
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )
        response = ""
        for chunk in completion:
            response += chunk.choices[0].delta.content or ""

        return QueryResponse(
            response=response
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    uvicorn.run('main:app', host="localhost", port=8000, reload=True)