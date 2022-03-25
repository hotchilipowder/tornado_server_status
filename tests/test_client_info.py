import pytest
import asyncio
import asyncssh

from tornado_server_status.client_info import run_cmdline_get_out

class TestClientInfo:
    hostname = '127.0.0.1'
    username = 'root'
    port = 22
    conn = None

    # @classmethod
    # @pytest.mark.asyncio
    # async def setup_class(cls):
    #     self.conn = await asyncssh.connect(self.hostname, username=self.username, \
    #                                 port=self.port, known_hosts=None)

    # @classmethod
    # @pytest.mark.asyncio
    # async def teardown_class(cls):
    #     await self.conn.close()

    # due to this issue, we cannt use cls.conn
    @pytest.mark.asyncio
    async def test_run_cmdline_get_out(self):
        # assert 1==0
        cmdline = 'echo 1'
        async with asyncssh.connect(self.hostname, username=self.username, \
                port=self.port, known_hosts=None) as conn:
            out = await run_cmdline_get_out(conn, cmdline)
            assert out.strip() == '1'
