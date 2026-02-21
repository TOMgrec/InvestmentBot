import chainlit as cl
from langserve.client import RemoteRunnable
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing import List, Optional


def preprocess_query(query:str):
    """Parse query for optional actions."""
    return query.strip(), []


@cl.on_chat_start
async def start():
    # Connect to the LangServe chain
    chain = RemoteRunnable("http://localhost:8001/rag/")
    cl.user_session.set("chain", chain)

    # Initialize history list
    history = []
    cl.user_session.set("history", history)

@cl.on_message
async def main(message: cl.Message):
    chain = cl.user_session.get("chain")
    history:list = cl.user_session.get("history")
    
    # Parse message for optional tags (simple parsing: look for 'tags:' at the end)
    content, actions = preprocess_query(message.content)
    
    
    # Input dict for the remote chain
    input_dict = {
        "question": content,
        "history": cl.user_session.get("history"),
        "actions": actions
    }

    # Invoke the remote chain asynchronously
    msg = cl.Message(content="")
    await msg.send()

    full_response = ""

    try:
        # Streaming via astream (plus fluide que astream_events pour du texte simple)
        async for chunk in chain.astream(input_dict):
            # chunk est une str (grâce à StrOutputParser)
            full_response += chunk
            await msg.stream_token(chunk)
        
        await msg.send()  # Finalise le message après streaming complet
    
    except Exception as e:
        await cl.ErrorMessage(content=f"Erreur lors du streaming : {str(e)}").send()
    
    # Ajouter message utilisateur à l'historique
    history.append(HumanMessage(content=content))
    
    # Ajouter réponse à l'historique
    history.append(AIMessage(content=full_response))
    cl.user_session.set("history", history)