from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from fastapi import FastAPI, Request
from langserve import add_routes
from pydantic import BaseModel
from agent.agent_db.utils import send_query
import json
import re

from agent.core.config import GOOGLE_API_KEY



with open("agent/agent_db/PROMPTS.md", "r") as f:
    SYSTEM_PROMPT = f.read()

with open("agent/agent_db/SUMMARIZE.md", "r") as f:
    SUMMARY_PROMPT = f.read()

with open("agent/agent_db/tags.json", "r") as f:
    tags_content = f.read()
    JSON_TAGS = json.loads(tags_content)
    TAGS_LIST = [item["tag"] for item in JSON_TAGS]
    SPECIAL_TAGS_LIST = [f"- {item['tag']} : {item['description']}" for item in JSON_TAGS if item["special"] == 1]



# Modèle d'entrée
class SQLInput(BaseModel):
    question: str



prompt = PromptTemplate.from_template(SYSTEM_PROMPT)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)



def extract_sql(response:str):
    # Pattern pour ```sql ... ```
    pattern = r'```sql\s*\n(.*?)\n```'
    match = re.search(pattern, response.content, re.DOTALL)
    if match:
        sql = match.group(1).strip()
        # Enlève les commentaires -- en haut
        sql = re.sub(r'^\s*--.*$\n?', '', sql, flags=re.MULTILINE)
        return sql.strip()
    return response.strip()



def handle_output(result: str):
    print(f"\n<LLM RAW RESPONSE>\n{result}\n</LLM RAW RESPONSE>\n")
    result = extract_sql(result)
    print(f"\n<SQL OUTPUT>\n{result}\n</SQL OUTPUT>\n")

    try:
        execution_result = send_query(result)
    except Exception as e:
        execution_result = f"Erreur d'exécution SQL: {str(e)}"

    print(f"\nRésultat de l'exécution : {execution_result}")

    return {
        "answer": str(execution_result),
        "sql_query": result
    }


sql_chain = prompt.partial(
        TAGS_LIST=", ".join(TAGS_LIST),
        SPECIAL_TAGS_LIST="\n".join(SPECIAL_TAGS_LIST)
    ) | llm | (lambda response: handle_output(response))



# Configure un server LangServe pour exposer ce chain à l'agent
# Par exemple, avec FastAPI :
app = FastAPI()
add_routes(
    app,
    sql_chain,
    input_type=SQLInput,
    path="/sql"  # Votre endpoint /sql
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) # Eviter la collision