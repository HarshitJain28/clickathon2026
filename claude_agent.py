"""Minimal Claude Agent SDK + ClickHouse Cloud MCP smoke test.

Initializes the Claude Agent SDK, registers the ClickHouse Cloud remote MCP
server (https://mcp.clickhouse.cloud/mcp), and asks it to list the tables in
the `clickathon` database. Nothing else.

Usage:
    python claude_agent.py
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

REPO_ROOT = Path(__file__).resolve().parent
load_dotenv(REPO_ROOT / ".env")

if os.environ.get("CLAUDE_OAUTH_TOKEN") and not os.environ.get(
    "CLAUDE_CODE_OAUTH_TOKEN"
):
    os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = os.environ["CLAUDE_OAUTH_TOKEN"]

QUESTION = "list the tables in clickathon db"


async def main():
    options = ClaudeAgentOptions(
        mcp_servers={
            "clickhouse-cloud": {
                "type": "http",
                "url": "https://mcp.clickhouse.cloud/mcp",
            }
        },
        allowed_tools=["mcp__clickhouse-cloud__*"],
        permission_mode="bypassPermissions",
    )

    async for message in query(prompt=QUESTION, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)


if __name__ == "__main__":
    asyncio.run(main())
