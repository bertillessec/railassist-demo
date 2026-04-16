import json
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import ConnectedAgentTool, AzureAISearchTool
from azure.identity import DefaultAzureCredential
from pathlib import Path

ENDPOINT = 'https://t-bmathieu-aitour-resource.services.ai.azure.com/api/projects/t-bmathieu-aitour'
MODEL = 'gpt-4.1-mini'
SEARCH_CONN = '/subscriptions/e5f60af0-2f16-4745-8a8e-d58d71689437/resourceGroups/rg-t-bmathieu-1283/providers/Microsoft.CognitiveServices/accounts/t-bmathieu-aitour-resource/connections/railassist-search-conn'

client = AgentsClient(endpoint=ENDPOINT, credential=DefaultAzureCredential())

# Delete old agents
env_path = Path('.env')
try:
    old_ids = json.loads([l.split('=',1)[1] for l in env_path.read_text().splitlines() if l.startswith('AGENT_IDS=')][0])
    for key, aid in old_ids.items():
        try:
            client.delete_agent(agent_id=aid)
            print(f'Deleted {key}: {aid}')
        except: pass
except: pass

# --- Instructions ---
schedule_instr = 'You are TrainScheduleAgent for Belgian railways. Generate REALISTIC simulated departure data. Include train number (IC/S/L/Thalys+number), destination, time, platform (1-14), status. Stations: Bruxelles-Midi, Bruxelles-Central, Liege-Guillemins, Namur, Charleroi-Sud, Anvers-Central, Gand-Saint-Pierre, Bruges, Mons, Louvain, Ottignies, Luxembourg, Arlon, Ostende, Mechelen. For connections give 2-3 options with price (standard 8-35 EUR, comfort 15-55 EUR). Use code interpreter for random data. Respond in passenger language.'

passenger_instr = 'You are PassengerServiceAgent for Belgian railways. Handle tickets, subscriptions, fares, compensation. Fare rules: standard 8-35 EUR, comfort +50%, return x1.8, Weekend Ticket 50% off (Sat-Sun), Go Pass 10 at 60%, children under 12 FREE, seniors/students 50% off. Compensation (EC 1371/2007): under 15min=nothing, 15-29min=25%, 30-59min=50%, 60+min=100%. Generate claim ref CLM-YYYYMMDD-NNNN. Use code interpreter. Respond in passenger language.'

incident_instr = 'You are IncidentAgent for Belgian railways. Handle disruptions, planned works, incident reports. Lines: L1 Bxl-Anvers, L25 Bxl-Liege, L96 Bxl-Namur, L50A Bxl-Gand, L161 Namur-Lux, L130 Namur-Charleroi, L51 Bxl-Bruges-Ostende. Generate 1-3 realistic incidents with ID, severity (CRITICAL/HIGH/MEDIUM/LOW), affected line, description, times, alternatives. Use code interpreter. Be calm and solution-oriented. Respond in passenger language.'

knowledge_instr = 'You are KnowledgeAgent, the documentation specialist for Belgian railways. You have access to Azure AI Search containing official railway documents: regulations, fare policies, safety rules, accessibility guidelines, network information, and international connections. When asked a question, ALWAYS search the knowledge base first using your Azure AI Search tool. Base your answers strictly on the documents found. Cite the document title when answering. If the information is not in the knowledge base, say so clearly. Respond in the passenger language.'

orch_instr = 'You are RailAssist, central AI assistant for Belgian railways. You MUST delegate EVERY question to the appropriate connected agent - NEVER answer directly. Rules: Timetables/departures/connections -> TrainScheduleAgent. Tickets/fares/compensation -> PassengerServiceAgent. Disruptions/works/incidents -> IncidentAgent. Regulations/rules/policies/safety/accessibility/network info -> KnowledgeAgent. If multi-domain, delegate sequentially. Present responses clearly. Match passenger language.'

# --- Create sub-agents ---
print('\n-- Creating sub-agents --')

s = client.create_agent(model=MODEL, name='TrainScheduleAgent', instructions=schedule_instr, tools=[{'type':'code_interpreter'}])
print(f'  schedule: {s.id}')

p = client.create_agent(model=MODEL, name='PassengerServiceAgent', instructions=passenger_instr, tools=[{'type':'code_interpreter'}])
print(f'  passenger: {p.id}')

i = client.create_agent(model=MODEL, name='IncidentAgent', instructions=incident_instr, tools=[{'type':'code_interpreter'}])
print(f'  incident: {i.id}')

# KnowledgeAgent with Azure AI Search
ai_search = AzureAISearchTool(index_connection_id=SEARCH_CONN, index_name='rail-knowledge')
k = client.create_agent(model=MODEL, name='KnowledgeAgent', instructions=knowledge_instr, tools=ai_search.definitions)
print(f'  knowledge: {k.id}')

# --- Create orchestrator ---
print('\n-- Creating orchestrator --')

ct_list = []
for aid, nm, ds in [
    (s.id, 'TrainScheduleAgent', 'Train timetables, departures, connections, real-time tracking'),
    (p.id, 'PassengerServiceAgent', 'Tickets, subscriptions, fares, delay compensation'),
    (i.id, 'IncidentAgent', 'Disruptions, planned works, incident reports, alternatives'),
    (k.id, 'KnowledgeAgent', 'Railway regulations, safety rules, fare policies, accessibility guidelines, network information'),
]:
    ct_list.extend(ConnectedAgentTool(id=aid, name=nm, description=ds).definitions)

o = client.create_agent(model=MODEL, name='RailAssist', instructions=orch_instr, tools=ct_list)
print(f'  orchestrator: {o.id}')
print(f'  connected agents: {len(o.tools)}')

# --- Save IDs ---
new_ids = {'schedule':s.id, 'passenger':p.id, 'incident':i.id, 'knowledge':k.id, 'railassist':o.id}
lines = [l for l in env_path.read_text().splitlines() if not l.startswith('AGENT_IDS=')]
lines.append(f'AGENT_IDS={json.dumps(new_ids)}')
env_path.write_text(chr(10).join(lines) + chr(10))
print(f'\nSaved 5 agents. Done!')