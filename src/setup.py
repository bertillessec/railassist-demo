"""Setup - create all RailAssist agents with multi-agent orchestration (Factory pattern)."""

import json
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import ConnectedAgentTool
from azure.identity import DefaultAzureCredential
from src.config import AGENT_IDS, AZURE_AI_ENDPOINT, ROOT_DIR, MODEL_NAME
from src.agents import AGENT_REGISTRY, build_toolset, create_agent
from src.agents.agent import load_system_prompt


def _save_agent_ids(agent_ids: dict) -> None:
    env_path = ROOT_DIR / ".env"
    lines = env_path.read_text().splitlines() if env_path.exists() else []
    new_lines = [l for l in lines if not l.startswith("AGENT_IDS=")]
    new_lines.append(f"AGENT_IDS={json.dumps(agent_ids)}")
    env_path.write_text("\n".join(new_lines) + "\n")


class AgentFactory:
    def __init__(self, client: AgentsClient):
        self.client = client
        self._created_agents: dict = {}

    def create_sub_agent(self, key: str, cfg: dict):
        toolset = build_toolset(self.client, cfg)
        agent = create_agent(self.client, cfg, toolset)
        self._created_agents[key] = (agent, cfg)
        return agent

    def create_orchestrator(self, key: str, cfg: dict):
        connected_tools = []
        for sub_key, (sub_agent, sub_cfg) in self._created_agents.items():
            connected_tools.append(ConnectedAgentTool(
                id=sub_agent.id, name=sub_cfg["name"],
                description=sub_cfg.get("description", f"Sub-agent: {sub_cfg['name']}"),
            ))
        toolset = build_toolset(self.client, cfg)
        model = cfg.get("model") or MODEL_NAME
        agent = self.client.create_agent(
            model=model, name=cfg["name"],
            instructions=load_system_prompt(cfg["prompt"]),
            toolset=toolset,
            tools=[ct.definitions[0] for ct in connected_tools],
        )
        self._created_agents[key] = (agent, cfg)
        return agent

    def get_agent_ids(self) -> dict:
        return {key: agent.id for key, (agent, _) in self._created_agents.items()}


def main() -> None:
    client = AgentsClient(endpoint=AZURE_AI_ENDPOINT, credential=DefaultAzureCredential())

    for key, old_id in AGENT_IDS.items():
        try:
            client.delete_agent(agent_id=old_id)
            print(f"  Deleted previous '{key}' agent: {old_id}")
        except Exception:
            pass

    factory = AgentFactory(client)

    print("\n  -- Phase 1: Creating sub-agents --")
    sub_agents = {k: v for k, v in AGENT_REGISTRY.items() if v.get("is_sub", False)}
    for key, cfg in sub_agents.items():
        agent = factory.create_sub_agent(key, cfg)
        print(f"  Created sub-agent '{key}': {agent.id} ({cfg['name']})")

    print("\n  -- Phase 2: Creating orchestrator --")
    orchestrators = {k: v for k, v in AGENT_REGISTRY.items() if not v.get("is_sub", False)}
    for key, cfg in orchestrators.items():
        agent = factory.create_orchestrator(key, cfg)
        print(f"  Created orchestrator '{key}': {agent.id} ({cfg['name']})")
        print(f"    Connected to: {', '.join(v['name'] for v in sub_agents.values())}")

    new_ids = factory.get_agent_ids()
    _save_agent_ids(new_ids)
    print(f"\n  AGENT_IDS written to .env")
    print(f"  Registered agents: {', '.join(new_ids.keys())}")
    print(f"\n  Run with:  python -m src.main railassist\n")


if __name__ == "__main__":
    main()
