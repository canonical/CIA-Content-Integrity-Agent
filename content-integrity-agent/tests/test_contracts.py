"""
Contract tests: verify all agents have required interface.
Run before implementing agents to ensure consistency.
"""

import pytest
from models.schemas import PipelineState


def test_base_agent_exists():
    from agents.base import BaseAgent
    assert BaseAgent is not None


def test_discovery_agent_has_run_method():
    from agents.discovery import DiscoveryAgent
    agent = DiscoveryAgent.__new__(DiscoveryAgent)
    assert hasattr(agent, 'run')


def test_resolver_agent_has_run_method():
    from agents.resolver import ResolverAgent
    agent = ResolverAgent.__new__(ResolverAgent)
    assert hasattr(agent, 'run')


def test_owner_resolver_has_run_method():
    from agents.owner_resolver import OwnerResolverAgent
    agent = OwnerResolverAgent.__new__(OwnerResolverAgent)
    assert hasattr(agent, 'run')


def test_suggestion_agent_has_run_method():
    from agents.suggestion import SuggestionAgent
    agent = SuggestionAgent.__new__(SuggestionAgent)
    assert hasattr(agent, 'run')


def test_router_agent_has_run_method():
    from agents.confidence_router import RouterAgent
    agent = RouterAgent.__new__(RouterAgent)
    assert hasattr(agent, 'run')


def test_notifier_agent_has_run_method():
    from agents.notifier import NotifierAgent
    agent = NotifierAgent.__new__(NotifierAgent)
    assert hasattr(agent, 'run')


def test_orchestrator_agent_exists():
    from agents.orchestrator import OrchestratorAgent
    assert OrchestratorAgent is not None


def test_schemas_are_importable():
    from models.schemas import (
        LinkFailure, PageMeta, Owner, FixSuggestion,
        Notification, PipelineState, FailureSeverity, RouterAction
    )
    assert LinkFailure is not None
    assert PipelineState is not None