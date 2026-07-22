import asyncio
import unittest
from unittest.mock import AsyncMock

from airtouch2.common.NetClient import NetClient


class TestNetClientLifecycle(unittest.IsolatedAsyncioTestCase):
    """Ports of upstream's handle-disconnect-exceptions hardening.

    1. If the main read loop ever dies with an escaped exception, that must be
       ERROR-logged - previously the task died silently, which is how the
       zombie-client bug stayed invisible.
    2. stop() must be safe even if the client was never started, and run()
       must be callable again after a stop.
    """

    def _client(self) -> NetClient:
        return NetClient("localhost", 9200, AsyncMock(), AsyncMock())

    async def test_escaped_main_loop_exception_is_logged(self):
        client = self._client()

        async def boom():
            raise ValueError("kaboom")

        client._main = boom
        with self.assertLogs("airtouch2.common.NetClient", level="ERROR") as logs:
            client.run()
            await asyncio.wait([client._main_loop_task])
            await asyncio.sleep(0)  # let the done-callback fire
        self.assertTrue(any("kaboom" in line for line in logs.output))

    async def test_stop_before_run_does_not_raise(self):
        client = self._client()
        await client.stop()  # previously raised RuntimeError
