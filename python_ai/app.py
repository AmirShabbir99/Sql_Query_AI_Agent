from fastapi import FastAPI
from pydantic import BaseModel

from sql_agent import get_data_from_database

app = FastAPI()


class QueryRequest(BaseModel):
    question: str


@app.post("/query")
def query_database(request: QueryRequest):

    result = get_data_from_database(request.question)

    return {
        "question": request.question,
        "result": result
    }