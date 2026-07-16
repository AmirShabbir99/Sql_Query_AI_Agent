#Step1: Extract Schema
from sqlalchemy import create_engine, inspect
import json
import re
import sqlite3
from langchain_mistralai import ChatMistralAI
from dotenv import load_dotenv
import os
load_dotenv()

key = os.getenv("MISTRAL_API_KEY")

print("Key exists:", key is not None)
print("Length:", len(key) if key else 0)
print("Value:", key)
db_url = "sqlite:///amazon.db"

def extract_schema(db_url):
    engine = create_engine(db_url)
    inspector = inspect(engine)
    schema = {}

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        schema[table_name] = [col['name'] for col in columns]
    return json.dumps(schema)


#Step2: Text to SQL (DeepSeek with Ollama)
from langchain_core.prompts import ChatPromptTemplate



def text_to_sql(schema, prompt):
    SYSTEM_PROMPT = """
    You are an expert SQL generator. Given a database schema and a user prompt, generate a valid SQL query that answers the prompt. 
    Only use the tables and columns provided in the schema. ALWAYS ensure the SQL syntax is correct and avoid using any unsupported features. 
    Output only the SQL as your response will be directly used to query data from the database. No preamble please. Do not use <think> tags.
    """

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", "Schema:\n{schema}\n\nQuestion: {user_prompt}\n\nSQL Query:")
    ])

    # model = Mistral(model="deepseek-r1:8b", temperature=0) #Use any other model if you want
    model = ChatMistralAI(
        model="mistral-small-latest",
        temperature=0
    )
    chain = prompt_template | model
    response = chain.invoke({
        "schema": schema,
        "user_prompt": prompt
    })

    sql_query = response.content

    # Remove <think> tags
    sql_query = re.sub(
        r"<think>.*?</think>",
        "",
        sql_query,
        flags=re.DOTALL
    )

    # Remove Markdown code fences
    sql_query = re.sub(r"```sql\s*", "", sql_query, flags=re.IGNORECASE)
    sql_query = re.sub(r"```", "", sql_query)

    sql_query = sql_query.strip()

    print("Generated SQL:")
    print(sql_query)

    return sql_query



def get_data_from_database(prompt):
    schema = extract_schema(db_url)
    sql_query = text_to_sql(schema, prompt)
    conn = sqlite3.connect("amazon.db")
    cursor = conn.cursor()
    res = cursor.execute(sql_query)
    results = res.fetchall()
    conn.close()
    return results

