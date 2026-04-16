from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import MessageRole
from azure.identity import DefaultAzureCredential
from src.config import AGENT_IDS, AZURE_AI_ENDPOINT
import traceback

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

client = AgentsClient(endpoint=AZURE_AI_ENDPOINT, credential=DefaultAzureCredential())
threads = {}

def agent_key(name):
    n = name.lower()
    if "schedule" in n: return "schedule"
    if "passenger" in n: return "passenger"
    if "incident" in n: return "incident"
    if "knowledge" in n: return "knowledge"
    if "fabric" in n: return "fabric"
    return "railassist"

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id", "default")

    agent_id = AGENT_IDS.get("railassist")

    if session_id not in threads:
        thread = client.threads.create()
        threads[session_id] = thread.id
    thread_id = threads[session_id]

    client.messages.create(thread_id=thread_id, role=MessageRole.USER, content=message)
    run = client.runs.create_and_process(thread_id=thread_id, agent_id=agent_id)

    response_text = "No response"
    messages = client.messages.list(thread_id=thread_id)
    for msg in messages:
        if msg.role == "assistant":
            for block in msg.content:
                if hasattr(block, "text"):
                    response_text = block.text.value
            break

    steps = []
    try:
        run_steps = client.run_steps.list(thread_id=thread_id, run_id=run.id)
        for step in run_steps:
            sd = step.step_details
            sd_dict = sd.as_dict() if hasattr(sd, "as_dict") else {}
            step_type = sd_dict.get("type", "")

            if step_type == "tool_calls":
                for tc in sd_dict.get("tool_calls", []):
                    tc_type = tc.get("type", "")
                    if tc_type == "connected_agent":
                        ca = tc.get("connected_agent", {})
                        name = ca.get("name", "unknown")
                        steps.append({"t": "route", "from": "railassist", "to": agent_key(name), "msg": "Delegated to " + name})
                    elif tc_type == "azure_ai_search":
                        steps.append({"t": "tool", "agent": "knowledge", "tool": "azure_ai_search", "msg": "Searching knowledge base"})
                        steps.append({"t": "ok", "tool": "azure_ai_search", "msg": "Results retrieved"})
                    elif tc_type == "code_interpreter":
                        last_agent = steps[-1]["to"] if steps and "to" in steps[-1] else "railassist"
                        steps.append({"t": "tool", "agent": last_agent, "tool": "code_interpreter", "msg": "Executing analysis"})
                        steps.append({"t": "ok", "tool": "code_interpreter", "msg": "Completed"})
                    else:
                        steps.append({"t": "tool", "agent": "railassist", "tool": tc_type, "msg": tc_type})
    except Exception as e:
        print(f"Steps error: {e}")
        traceback.print_exc()

    print(f"Query: {message} | Steps: {len(steps)} | Status: {run.status}")
    return {"response": response_text, "steps": steps, "status": str(run.status)}