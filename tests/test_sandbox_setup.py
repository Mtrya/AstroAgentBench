"""Exercise prepared workspaces and their real MCP subprocesses without a model."""

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from benchmark.run_benchmark import setup_sandbox as setup_orbital
from satnet_agent.run_benchmark import setup_sandbox as setup_satnet


@pytest.mark.parametrize("kind", ["orbital", "satnet"])
def test_prepared_sandbox_serves_local_queries(tmp_path, kind):
    if kind == "orbital":
        sandbox = setup_orbital("revisit-optimization", "case_0001", tmp_path)
        env = {
            "CASE_PATH": str(sandbox / "data"),
            "ASTROX_CASE_PATH": str(sandbox / "data"),
            "ASTROX_STATE_PATH": str(sandbox / "state/scenario.json"),
        }
        tool_name = "query_satellites"
    else:
        sandbox = setup_satnet(40, 2018, tmp_path)
        env = {
            "SATNET_PROBLEMS_PATH": str(sandbox / "data/problems.json"),
            "SATNET_MAINTENANCE_PATH": str(sandbox / "data/maintenance.csv"),
            "SATNET_STATE_PATH": str(sandbox / "state/scenario.json"),
            "SATNET_WEEK": "40",
            "SATNET_YEAR": "2018",
        }
        tool_name = "list_unsatisfied_requests"

    assert (sandbox / ".local").readlink() == Path.home() / ".local"
    assert (sandbox / ".claude").is_dir()
    assert (sandbox / "data").is_dir()
    assert (sandbox / "workspace/mission_brief.md").is_file()
    config = json.loads((sandbox / "workspace/.mcp.json").read_text())
    server = next(iter(config["mcpServers"].values()))
    env = {**os.environ, **env, **server["env"]}
    env["HOME"] = str(sandbox)
    env["PATH"] = f"{Path(sys.executable).parent}:{env.get('PATH', '')}"
    parameters = StdioServerParameters(
        command=server["command"], args=server["args"], env=env,
        cwd=str(sandbox / "workspace"),
    )

    async def query():
        async with stdio_client(parameters) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert tool_name in {tool.name for tool in tools.tools}
                arguments = {"filters": {}, "limit": 1000} if kind == "orbital" else {}
                result = await session.call_tool(tool_name, arguments)
                assert not result.isError
                if kind == "orbital":
                    assert result.content
                    for item in result.content:
                        payload = json.loads(item.text)
                        assert "id" in payload
                else:
                    payload = json.loads(result.content[0].text)
                    assert payload["total"] > 0
                    assert payload["items"]

    asyncio.run(asyncio.wait_for(query(), timeout=30))
