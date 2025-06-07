from typing import List, Dict, Any, Union
import gradio as gr
from gradio.components.chatbot import ChatMessage
import json
import os
import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from groq import Groq

from prompt import system_prompt
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env
MODEL = os.getenv("MODEL")

print(MODEL)
loop = asyncio.new_event_loop()

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.client = None  # Will be initialized when API key is set
        self.api_key = os.getenv("GROQ_API_KEY")

    def set_api_key(self, api_key: str):
        """Set the Groq API key and initialize the client"""
        self.api_key = api_key
        self.client = Groq(api_key=api_key)
        return "API key set successfully"

    def get_api_key_status(self) -> str:
        """Return the status of the API key"""
        if self.api_key:
            return "API key is set"
        return "API key is not set"

    def connect(self, server_script_path: str):
        return loop.run_until_complete(self.connect_to_server(server_script_path))
 
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
    

    def process_message(self, message: str, history: List[Union[Dict[str, Any], ChatMessage]]) -> tuple:
        if not self.client:
            return history + [
                {"role": "user", "content": message}, 
                {"role": "assistant", "content": "Please set your Groq API key first."}
            ], gr.Textbox(value="")
            
        if not self.session:
            return history + [
                {"role": "user", "content": message}, 
                {"role": "assistant", "content": "Please connect to an MCP server first."}
            ], gr.Textbox(value="")
        
        new_messages = loop.run_until_complete(self._process_query(message, history))
        return history + [{"role": "user", "content": message}] + new_messages, gr.Textbox(value="")

    async def _process_query(self, message: str, history: List[Union[Dict[str, Any], ChatMessage]]):
        model_messages = []
        # Add system prompt
        model_messages.append({
            "role": "system",
            # "content": "You are an assistant that can respond to the user queries and if required, use the available tools to help answer questions."
            "content": system_prompt
        })
        for msg in history:
            if isinstance(msg, ChatMessage):
                role, content = msg.role, msg.content
            else:
                role, content = msg.get("role"), msg.get("content")
            
            if role in ["user", "assistant", "system"]:
                model_messages.append({"role": role, "content": content})
        
        model_messages.append({"role": "user", "content": message})
        # messages = [
        #     {
        #     "role": "system",
        #     "content": "You are an assistant that can respond to the user queries and if required, use the get_alerts and get_forecast tools."
        #     },
        #     {
        #         "role": "user",
        #         "content": query
        #     }
        # ]

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
        messages=model_messages, # Conversation history
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
        result_messages = []

        # print(f"response_messageyy: {response_message}")
        if tool_calls:
            print("\n\n")
            print(f"messages: {model_messages}")
            model_messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                # Call the tool and get the response
                result_messages.append({
                    "role": "assistant",
                    "content": f"I'll use the {function_name} tool to help answer your question.",
                    "metadata": {
                        "title": f"Using tool: {function_name}",
                        "log": f"Parameters: {json.dumps(function_args, ensure_ascii=True)}",
                        "status": "pending",
                        "id": f"tool_call_{function_name}"
                    }
                })
                
                result_messages.append({
                    "role": "assistant",
                    "content": "```json\n" + json.dumps(function_args, indent=2, ensure_ascii=True) + "\n```",
                    "metadata": {
                        "parent_id": f"tool_call_{function_name}",
                        "id": f"params_{function_name}",
                        "title": "Tool Parameters"
                    }
                })
                result = await self.session.call_tool(function_name, function_args)

                if result_messages and "metadata" in result_messages[-2]:
                    result_messages[-2]["metadata"]["status"] = "done"
                
                result_messages.append({
                    "role": "assistant",
                    "content": "Here are the results from the tool:",
                    "metadata": {
                        "title": f"Tool Result for {function_name}",
                        "status": "done",
                        "id": f"result_{function_name}"
                    }
                })


                result_content = result.content
                if isinstance(result_content, list):
                    result_content = "\n".join(str(item.text) for item in result_content)
                # Add the tool response to the conversation
                model_messages.append(
                    {
                        "tool_call_id": tool_call.id, 
                        "role": "tool", # Indicates this message is from tool use
                        "name": function_name,
                        "content": result_content,
                    }
                )
            # Make a second API call with the updated conversation
            second_response = self.client.chat.completions.create(
                model=MODEL,
                messages=model_messages
            )
            result_messages.append({
                "role": "assistant",
                "content": second_response.choices[0].message.content
            })
            # Return the final response
            return result_messages
        
        result_messages.append({
                    "role": "assistant", 
                    "content": response_message.content
                })
        return result_messages

        

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