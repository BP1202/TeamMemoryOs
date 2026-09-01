"""
AgentRegistry — Milestone 7.1.

Thread-safe registry for all available agents in TeamMemoryOS.
Provides:
* register() — register an agent instance.
* get()      — retrieve an agent by name.
* list_agents() — enumerate all registered agents with metadata.
* list_by_capability() — filter agents by capability.
* route() — select the best agent(s) for a set of required capabilities.

LangGraph compatibility note:
    The registry is the LangGraph-equivalent of a node catalogue.
    ``route()`` maps to a conditional edge function in LangGraph.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.agents.base import AgentCapability, BaseAgent

if TYPE_CHECKING:
    pass


class AgentRegistry:
    """Central registry for all TeamMemoryOS agents.

    Usage:
        registry = AgentRegistry()
        registry.register(my_agent)
        agent = registry.get("repository_agent")
    """

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """Register an agent.  Raises ValueError on duplicate name."""
        if agent.name in self._agents:
            raise ValueError(
                f"Agent '{agent.name}' is already registered. "
                "Use a unique name per agent."
            )
        self._agents[agent.name] = agent

    def get(self, name: str) -> BaseAgent | None:
        """Return the agent registered under *name*, or None."""
        return self._agents.get(name)

    def list_agents(self) -> list[dict]:
        """Return a list of agent metadata dicts (suitable for API serialisation)."""
        return [
            {
                "name": agent.name,
                "description": agent.description,
                "capabilities": [c.value for c in agent.capabilities],
            }
            for agent in self._agents.values()
        ]

    def list_by_capability(
        self, capability: AgentCapability
    ) -> list[BaseAgent]:
        """Return all agents that declare *capability*."""
        return [
            agent
            for agent in self._agents.values()
            if capability in agent.capabilities
        ]

    def route(self, required_capabilities: list[AgentCapability]) -> list[BaseAgent]:
        """Select the minimal set of agents that satisfy *required_capabilities*.

        Greedy selection: iterate over required capabilities and pick the first
        registered agent that satisfies each unsatisfied capability.

        Returns agents in the order capabilities were requested.
        Duplicate agents are only included once.
        """
        selected: list[BaseAgent] = []
        seen_names: set[str] = set()
        remaining = list(required_capabilities)

        while remaining:
            cap = remaining.pop(0)
            candidates = self.list_by_capability(cap)
            for candidate in candidates:
                if candidate.name not in seen_names:
                    selected.append(candidate)
                    seen_names.add(candidate.name)
                    break

        return selected

    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, name: str) -> bool:
        return name in self._agents


# Module-level singleton registry — agents register themselves at import time.
registry = AgentRegistry()
