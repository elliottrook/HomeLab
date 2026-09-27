"""Optional isolated PydanticAI preload-profile checks; run in candidate venv."""
import asyncio
import socket
import unittest
from unittest.mock import patch

from pydantic_ai import Agent, models
from pydantic_ai.exceptions import UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.usage import UsageLimits

models.ALLOW_MODEL_REQUESTS = False


class CandidateChecks(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.connections = patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden'))
        self.connections.start()
        self.addCleanup(self.connections.stop)

    async def test_no_tools_exposed_and_one_response(self):
        seen = []
        async def answer(messages, info):
            seen.append(info)
            return ModelResponse(parts=[TextPart('Synthetic answer')])
        agent = Agent(FunctionModel(answer), capabilities=[], retries=0)
        result = await agent.run('Fixture', usage_limits=UsageLimits(request_limit=1))
        self.assertEqual('Synthetic answer', result.output)
        self.assertEqual(1, len(seen))
        self.assertEqual([], seen[0].function_tools)

    async def test_unknown_effectful_tool_fails_closed(self):
        async def bad(messages, info):
            self.assertEqual([], info.function_tools)
            return ModelResponse(parts=[ToolCallPart('shell.execute', {'command': 'fixture-only'})])
        agent = Agent(FunctionModel(bad), capabilities=[], retries=0)
        with self.assertRaises((UnexpectedModelBehavior, UsageLimitExceeded)):
            await agent.run('Fixture', usage_limits=UsageLimits(request_limit=1))

    async def test_malformed_unavailable_tool_fails_closed(self):
        async def bad(messages, info):
            return ModelResponse(parts=[ToolCallPart('unknown', '{broken')])
        agent = Agent(FunctionModel(bad), capabilities=[], retries=0)
        with self.assertRaises((UnexpectedModelBehavior, UsageLimitExceeded)):
            await agent.run('Fixture', usage_limits=UsageLimits(request_limit=1))

    async def test_deadline_cancels_pending_script(self):
        cancelled = asyncio.Event()
        async def stalled(messages, info):
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()
        agent = Agent(FunctionModel(stalled), capabilities=[], retries=0)
        with self.assertRaises(TimeoutError):
            await asyncio.wait_for(agent.run('Fixture', usage_limits=UsageLimits(request_limit=1)), .02)
        self.assertTrue(cancelled.is_set())


if __name__ == '__main__':
    unittest.main()
