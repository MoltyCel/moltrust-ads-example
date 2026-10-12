"""Where your own Amazon Ads MCP call goes.

The guard calls `my_ads_call(tool, args)` only after MolTrust allowed the call (or a
person approved a hold). It receives exactly the tool name and arguments your agent
produced. Replace the stub with your MCP client session, for example with the `mcp`
Python SDK and your Login with Amazon token:

    async with streamablehttp_client("https://advertising-ai.amazon.com/mcp",
                                      headers={"Amazon-Ads-ClientId": CLIENT_ID,
                                               "Authorization": f"Bearer {ACCESS_TOKEN}"}) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            return await session.call_tool(tool, args)

Your credentials stay in this process. MolTrust never receives them.
"""


def my_ads_call(tool, args):
    return {"stub": True, "tool": tool}
