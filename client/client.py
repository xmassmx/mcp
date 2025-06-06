import json
import os
import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from groq import Groq


from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env
MODEL = os.getenv("MODEL")

print(MODEL)

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    # methods will go here
    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])
    
    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        messages = [
            {
            "role": "system",
            "content": "You are an assistant that can respond to the user queries and if required, use the get_alerts and get_forecast tools."
            },
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{
            "type": "function",
            "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema}
        } for tool in response.tools]

        # # Initial Claude API call
        response = self.client.chat.completions.create(
        model=MODEL, # LLM to use
        messages=messages, # Conversation history
        stream=False,
        tools=available_tools, # Available tools (i.e. functions) for our LLM to use
        tool_choice="auto", # Let our LLM decide when to use tools
        max_completion_tokens=1000 # Maximum number of tokens to allow in our response
    )
        # print(response)
        # Process response and handle tool calls
            # Extract the response and any tool call responses
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        print(f"response_messageyy: {response_message}")
        if tool_calls:
            print("\n\n")
            print(f"messages: {messages}")
            messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                # Call the tool and get the response
                result = await self.session.call_tool(function_name, function_args)
                # Add the tool response to the conversation
                messages.append(
                    {
                        "tool_call_id": tool_call.id, 
                        "role": "tool", # Indicates this message is from tool use
                        "name": function_name,
                        "content": result.content[0].text,
                    }
                )
            # Make a second API call with the updated conversation
            second_response = self.client.chat.completions.create(
                model=MODEL,
                messages=messages
            )
            # Return the final response
            return second_response.choices[0].message.content
        return response_message.content

        

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()
        

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())