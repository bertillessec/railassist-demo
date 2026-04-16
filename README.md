# RailAssist — Multi-Agent AI for Railway Operations

A reference implementation of a production-grade multi-agent system built on **Azure AI Foundry Agent Service**. RailAssist demonstrates how specialised AI agents can collaborate to answer complex passenger questions — timetables, disruptions, regulations, compensation, and operational analytics — grounded in enterprise knowledge and real operational data.

> Built on top of the internal [Foundry Agent Service Starter Kit](https://github.com/NicoGrassetto/Foundry-Agent-Service-Starter-Kit) by Nico Grassetto.

## Scenario

A national railway operator wants to automate a significant share of passenger interactions. The system must:

- Answer routine questions 24/7 (timetables, fares, rules)
- Handle disruptions and propose alternatives in real time
- Process delay compensation claims per EU Regulation EC 1371/2007
- Ground responses in official regulatory documents
- Surface operational analytics (punctuality, delays, causes) in plain language
- Coordinate across multiple domains when passenger questions span several areas

## Architecture

```
                     ┌──────────────────────────┐
                     │   RailAssist Orchestrator │
                     │  (Connected Agents hub)   │
                     └───────────┬───────────────┘
                                 │
        ┌────────────────┬───────┴────────┬────────────────┐
        ▼                ▼                ▼                ▼
  ┌──────────┐    ┌──────────────┐   ┌──────────┐    ┌────────────┐
  │ Schedule │    │  Passenger   │   │ Incident │    │ Knowledge  │
  │  Agent   │    │ServiceAgent  │   │  Agent   │    │   Agent    │
  └────┬─────┘    └──────┬───────┘   └────┬─────┘    └─────┬──────┘
       │                 │                 │                │
       ▼                 ▼                 ▼                ▼
  Code Interp.    Code Interp.       Code Interp.   Azure AI Search
  (timetables)    (fare rules)       (disruptions)  (rail-knowledge)
```

Plus a separate **Fabric Data Agent** that queries a lakehouse for operational analytics.

### Agents

| Agent | Role | Tools |
|-------|------|-------|
| `RailAssist` | Orchestrator — routes questions to specialists | 4x ConnectedAgentTool |
| `ScheduleAgent` | Timetables, connections, real-time tracking | Code Interpreter |
| `PassengerServiceAgent` | Tickets, fares, delay compensation | Code Interpreter |
| `IncidentAgent` | Disruptions, planned works, alternatives | Code Interpreter |
| `KnowledgeAgent` | RAG over official documentation | Azure AI Search |
| `FabricAgent` (separate) | Operational analytics on lakehouse | Fabric Data Agent |

### Data layer

- **Azure AI Search** — 10 indexed regulatory documents (passenger rights, fare policies, safety rules, network info)
- **Microsoft Fabric Lakehouse** — operational punctuality dataset (`train_punctuality`)
- **Code Interpreter** — dynamic analysis and realistic data generation

## What's in the repo

```
railassist-demo/
├── src/
│   ├── agents/
│   │   └── registry.py          # Declarative agent registry
│   ├── prompts/
│   │   ├── railassist.prompty   # Orchestrator instructions
│   │   ├── schedule.prompty     # ScheduleAgent instructions
│   │   ├── passenger.prompty    # PassengerServiceAgent instructions
│   │   └── incident.prompty     # IncidentAgent instructions
│   ├── tools/
│   │   ├── schedule.py          # Schedule-related function tools
│   │   ├── passenger.py         # Passenger service function tools
│   │   └── incident.py          # Incident function tools
│   ├── setup.py                 # Factory: creates agents + wires ConnectedAgentTool
│   ├── main.py                  # CLI entry point
│   └── config.py                # Config loader (.env)
├── railassist-ui/               # React frontend (Vite) with live pipeline panel
│   └── src/App.jsx              # Main UI component
├── api.py                       # FastAPI backend — proxies to Foundry + extracts run_steps
├── create_index.py              # Creates Azure AI Search index + uploads 10 docs
├── rebuild_agents.py            # Recreates all 5 agents from scratch
├── train_punctuality.csv        # Fabric lakehouse seed data
├── connection.yml               # AI Search connection for Foundry
└── .env                         # Endpoint + agent IDs
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- Azure subscription with:
  - An Azure AI Foundry project
  - An Azure AI Search service (Basic or higher)
  - A Microsoft Fabric capacity (F2 or higher)
- Model deployment: `gpt-4.1-mini` in your Foundry project
- Azure CLI authenticated (`az login`)

## Setup

### 1. Clone and install

```powershell
git clone https://github.com/bertillessec/railassist-demo.git
cd railassist-demo

pip install -r requirements.txt
pip install fastapi uvicorn
```

### 2. Configure environment

Create `.env` at the repo root:

```
AZURE_AI_ENDPOINT=https://<your-resource>.services.ai.azure.com/api/projects/<your-project>
MODEL_NAME=gpt-4.1-mini
```

### 3. Create the AI Search index

```powershell
python create_index.py
```

Indexes 10 regulatory documents into the `rail-knowledge` index.

### 4. Create the Fabric lakehouse

1. In the Fabric portal, create a workspace `RailAssist-Analytics`
2. Create a Lakehouse named `rail_operations`
3. Upload `train_punctuality.csv` and load to a Delta table
4. Use **Add to data agent** to create a `RailAnalytics` data agent

### 5. Register the AI Search connection in Foundry

```powershell
az cognitiveservices account connection create `
  --file connection.yml `
  --connection-name railassist-search-conn `
  --resource-group <rg> `
  --name <foundry-resource>
```

### 6. Create the 5 agents

```powershell
python rebuild_agents.py
```

This writes the agent IDs to `.env`.

## Running the demo

### CLI mode (single agent or orchestrator)

```powershell
python -m src.main schedule      # Talk to ScheduleAgent directly
python -m src.main railassist    # Talk to the full orchestrator
```

### Web UI mode

**Terminal 1 — Backend:**

```powershell
python -m uvicorn api:app --port 8000
```

**Terminal 2 — Frontend:**

```powershell
cd railassist-ui
npm install
npm run dev
```

Open `http://localhost:5173`. Toggle the **Pipeline** panel to see which agent gets called and which tool is invoked in real time.

## Demo scenarios

| Question | Agent | Tool |
|----------|-------|------|
| Next departures from Brussels-Midi? | ScheduleAgent | Code Interpreter |
| What are the rules for bikes on trains? | KnowledgeAgent | Azure AI Search |
| Any disruptions right now? | IncidentAgent | Code Interpreter |
| My train was 45 min late, compensation? | PassengerServiceAgent | Code Interpreter |
| Punctuality rate by line? | Fabric Data Agent | Lakehouse SQL |
| Delay → alternatives + compensation? | Multi-agent | Multiple |

## How it works

### Factory pattern

Each agent is one entry in `src/agents/registry.py` plus a `.prompty` file. `src/setup.py` reads the registry, creates the agents via the Foundry SDK, and wires up `ConnectedAgentTool` references on the orchestrator. To add a new agent, add a registry entry and a prompt file — no orchestration code to write.

### Connected Agents

The orchestrator delegates via `ConnectedAgentTool`, native to Foundry Agent Service. The service handles routing based on agent descriptions — no custom router or LLM-as-judge. The orchestrator's prompt tells it which kind of question belongs to which agent.

### RAG with Azure AI Search

The `KnowledgeAgent` has access to the `rail-knowledge` index via the `AzureAISearchTool`. It searches, retrieves relevant documents, and cites them in its response.

### Operational analytics with Fabric

The `FabricAgent` (created in the Fabric portal) translates natural language to SQL against the lakehouse and returns results. Accessed in the demo through the Fabric UI alongside the main chat.

## Known limitations

**Connected Agents cannot call local Python function tools.** Sub-agents run server-side on Foundry, so they have no access to your local Python process. For this demo, we use Code Interpreter with detailed instructions to generate realistic data. For production, replace with:

- **Azure Functions** — for serverless function backends
- **OpenAPI tools** — for existing REST APIs
- **MCP servers** — for tool catalogs

## Client demo flow

1. **Open with the business problem** (30s) — why railway operators need this
2. **Slides 1–3** — architecture + scenario (2 min)
3. **Frontend demo** (6 min) — 6 scenarios, Pipeline ON
4. **Behind the scenes** (5 min) — Foundry portal, VS Code repo tour, Fabric data agent
5. **Why Agent Service** — slide 4, business benefits (3 min)
6. **Q&A** (3 min)

See `SCRIPT-PRESENTATION.md` for the full speaker notes.

## Resources

- [Azure AI Foundry Agent Service docs](https://learn.microsoft.com/en-us/azure/ai-services/agents/)
- [Connected Agents overview](https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/connected-agents)
- [Azure AI Search + Agents](https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/azure-ai-search)
- [Microsoft Fabric Data Agents](https://learn.microsoft.com/en-us/fabric/data-science/how-to-data-agent)
- Starter kit — [NicoGrassetto/Foundry-Agent-Service-Starter-Kit](https://github.com/NicoGrassetto/Foundry-Agent-Service-Starter-Kit)

## License

Demo code. Provided as-is for reference.
