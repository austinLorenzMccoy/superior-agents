# Setting Up CoinGecko MCP Server: Official Integration Guide

This guide will walk you through the process of setting up and configuring the official CoinGecko Market Cap Percentage (MCP) server for use with AutoTradeX.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [MCP Server Options](#mcp-server-options)
3. [Setting Up the Public Remote MCP Server](#setting-up-the-public-remote-mcp-server)
4. [Setting Up the Local MCP Server](#setting-up-the-local-mcp-server)
5. [Configuring AutoTradeX to Use MCP Server](#configuring-autotradex)
6. [Testing the Integration](#testing-the-integration)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

Before starting, ensure you have:

- Node.js installed (download from https://nodejs.org/en/download)
- For local MCP server: CoinGecko Pro or Demo API key (get it from [CoinGecko](https://www.coingecko.com/en/api))
- Basic knowledge of terminal/command line

## MCP Server Options

CoinGecko offers two main options for MCP Server integration:

1. **Public Remote MCP Server**
   - No API key required
   - Limited rate limits (shared usage)
   - Ideal for testing and basic applications
   - Works out of the box with tools like Claude Desktop

2. **Local MCP Server**
   - Requires Pro or Demo API key
   - Higher rate limits
   - More control over the server
   - Ideal for development and production use

## Setting Up the Public Remote MCP Server

The public remote MCP server is the easiest option to get started with:

1. **Create an MCP configuration file**:
   Create a file named `mcp_config.json` with the following content:

   ```json
   {
     "mcpServers": {
       "coingecko_api_remote": {
         "command": "npx",
         "args": [
           "mcp-remote",
           "https://mcp.api.coingecko.com/sse"
         ]
       }
     }
   }
   ```

2. **Place the configuration file** in the appropriate location for your LLM client:
   - For Claude Desktop: Use `claude_desktop_config.json` in the location specified by Claude's documentation
   - For other clients: Check their documentation for the correct location and filename

## Setting Up the Local MCP Server

For more control and higher rate limits, you can run a local MCP server:

1. **Get a CoinGecko API Key**:
   - Sign up for a CoinGecko account at [CoinGecko](https://www.coingecko.com/)
   - Subscribe to either the Pro or Demo API plan
   - Generate an API key from your dashboard

2. **Create an MCP configuration file**:
   Create a file named `mcp_config.json` with the following content:

   For Pro API access:
   ```json
   {
     "mcpServers": {
       "coingecko_api_local": {
         "command": "npx",
         "args": [
           "-y",
           "@coingecko/coingecko-mcp"
         ],
         "env": {
           "COINGECKO_PRO_API_KEY": "YOUR_PRO_API_KEY",
           "COINGECKO_ENVIRONMENT": "pro"
         }
       }
     }
   }
   ```

   For Demo API access:
   ```json
   {
     "mcpServers": {
       "coingecko_api_local": {
         "command": "npx",
         "args": [
           "-y",
           "@coingecko/coingecko-mcp"
         ],
         "env": {
           "COINGECKO_DEMO_API_KEY": "YOUR_DEMO_API_KEY",
           "COINGECKO_ENVIRONMENT": "demo"
         }
       }
     }
   }
   ```

   Replace `YOUR_PRO_API_KEY` or `YOUR_DEMO_API_KEY` with your actual API key.

3. **Place the configuration file** in the appropriate location for your LLM client:
   - For Claude Desktop: Use `claude_desktop_config.json` in the location specified by Claude's documentation
   - For other clients: Check their documentation for the correct location and filename

## Configuring AutoTradeX

To configure AutoTradeX to use the CoinGecko MCP server:

1. **Edit your .env file** in the AutoTradeX directory:

   For the public remote MCP server:
   ```
   MCP_BASE_URL=https://mcp.api.coingecko.com
   COINGECKO_API_KEY=
   ```

   For the local MCP server with Pro API:
   ```
   MCP_BASE_URL=http://localhost:3000
   COINGECKO_API_KEY=YOUR_PRO_API_KEY
   COINGECKO_ENVIRONMENT=pro
   ```

   For the local MCP server with Demo API:
   ```
   MCP_BASE_URL=http://localhost:3000
   COINGECKO_API_KEY=YOUR_DEMO_API_KEY
   COINGECKO_ENVIRONMENT=demo
   ```

2. **Update the AutoTradeX configuration**:
   ```bash
   python -m autotradex setup
   ```

## Testing the Integration

To test if your MCP server is working correctly:

1. **For Claude Desktop or other LLM clients**:
   - Start your LLM client
   - Ask a question like "What is the current price of Bitcoin in USD?"
   - The LLM should be able to access the MCP server and provide the current price

2. **For AutoTradeX**:
   - Run the following command:
     ```bash
     python -m autotradex.data.mcp_integration
     ```
   - This should output the current market regime based on MCP data

## Troubleshooting

### Common Issues

1. **Rate Limit Exceeded**:
   - If using the public remote server, consider switching to the local server with a Pro API key
   - If using the local server, check your API key's rate limits

2. **Connection Issues**:
   - Ensure Node.js is installed correctly
   - Check your internet connection
   - Verify the MCP server is running (for local server)

3. **Authentication Issues**:
   - Double-check your API key
   - Ensure you're using the correct environment (pro/demo)

### Limitations with Claude

If you're using the Public Remote MCP Server with the free version of Claude, you may hit message limits easily. Consider:

- Subscribing to Claude Pro plan for higher message and usage limits
- Using the Local MCP Server instead

### Dynamic vs. Static Tools

When using the Local MCP with Claude, you can choose between:

- **Dynamic Tools**: Dynamically discover and invoke endpoints from the API
- **Static Tools**: One tool per endpoint, with filtering as necessary

For specific use cases with only a few endpoints, consider removing the `tools=dynamic` option.

## Additional Resources

- [CoinGecko MCP Server Documentation](https://docs.coingecko.com/reference/mcp-server)
- [Model Context Protocol Quickstart Guide](https://modelcontextprotocol.io/quickstart/user)
- [CoinGecko LLMs.txt](https://docs.coingecko.com/llms.txt) - Provides context for responsible AI behavior
- [CoinGecko GitHub](https://github.com/coingecko) - For the latest updates and code

---

For feedback or suggestions on this integration guide, please contact the AutoTradeX team.
