import pytest
from unittest.mock import MagicMock, patch
from agents.scoring_agent import ScoringAgent
from agents.agent1 import Agent1
from agents.agent2 import Agent2
from agents.agent3 import Agent3


def make_mock_response(content: str):
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


def test_scoring_agent_parses_valid_json():
    with patch("agents.scoring_agent.OpenAI"):
        agent = ScoringAgent(system_prompt="test")
        agent._client.chat.completions.create.return_value = make_mock_response(
            '{"score": 18, "reasoning": "Good match"}'
        )
        result = agent._call_llm("test resume")
    assert result["score"] == 18


def test_scoring_agent_enables_reasoning_and_temperature():
    with patch("agents.scoring_agent.OpenAI"):
        agent = ScoringAgent(system_prompt="test")
        agent._client.chat.completions.create.return_value = make_mock_response(
            '{"score": 18, "reasoning": "Good match"}'
        )
        agent._call_llm("test resume")

    kwargs = agent._client.chat.completions.create.call_args.kwargs
    assert kwargs["temperature"] >= 0.7
    assert kwargs["extra_body"] == {"reasoning": {"enabled": True}}


def test_scoring_agent_regex_fallback():
    with patch("agents.scoring_agent.OpenAI"):
        agent = ScoringAgent(system_prompt="test")
        agent._client.chat.completions.create.return_value = make_mock_response(
            'Some preamble {"score": 15, "reasoning": "Partial match"} trailing text'
        )
        result = agent._call_llm("test resume")
    assert result["score"] == 15


def test_scoring_agent_returns_zero_on_failure():
    with patch("agents.scoring_agent.OpenAI"):
        agent = ScoringAgent(system_prompt="test")
        agent._client.chat.completions.create.side_effect = Exception("API error")
        result = agent._call_llm("test resume")
    assert result["score"] == 0


def test_agent1_score_resume():
    with patch("agents.scoring_agent.OpenAI"), \
         patch("agents.agent1.ScoringAgent._call_llm") as mock_call:
        mock_call.return_value = {"score_q1": 16, "score_q2": 18}
        agent = Agent1("ideal profile", "deal breakers")
        q1, q2 = agent.score_resume("resume text")
    assert q1 == 16
    assert q2 == 18


def test_agent1_score_clamps_to_range():
    with patch("agents.scoring_agent.OpenAI"), \
         patch("agents.agent1.ScoringAgent._call_llm") as mock_call:
        mock_call.return_value = {"score_q1": 99, "score_q2": -5}
        agent = Agent1("ideal profile", "deal breakers")
        q1, q2 = agent.score_resume("resume text")
    assert q1 == 20   # clamped from 99 to max 20
    assert q2 == 0


def test_agent2_score_resume():
    with patch("agents.scoring_agent.OpenAI"), \
         patch("agents.agent2.ScoringAgent._call_llm") as mock_call:
        mock_call.return_value = {"score_q3": 14, "score_q4": 17}
        agent = Agent2("experience signals", "required tools")
        q3, q4 = agent.score_resume("resume text")
    assert q3 == 14
    assert q4 == 17


def test_agent3_returns_zero_when_jd_missing():
    with patch("agents.scoring_agent.OpenAI"):
        agent = Agent3("")
        q5 = agent.score_resume("resume text")
    assert q5 == 0
