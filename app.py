import gradio as gr
from gradio.components.chatbot import ChatMessage
from client.client import MCPClient
import os

client = MCPClient()

def gradio_interface():
    with gr.Blocks(title="MCP Client") as demo:
        gr.Markdown("# MCP Assistant")
        
        with gr.Row(equal_height=True):
            with gr.Column(scale=4):
                api_key = gr.Textbox(
                    label="Groq API Key",
                    placeholder="Enter your Groq API key",
                    type="password",
                    value=os.getenv("GROQ_API_KEY", "")
                )
            with gr.Column(scale=1):
                set_api_key_btn = gr.Button("Set API Key")
        
        api_key_status = gr.Textbox(label="API Key Status", interactive=False, value=client.get_api_key_status())
        
        with gr.Row(equal_height=True):
            with gr.Column(scale=4):
                server_path = gr.Textbox(
                    label="Server Script Path",
                    placeholder="Enter path to server script (e.g., weather.py)",
                    value="../server/business-recorder.py"
                )
            with gr.Column(scale=1):
                connect_btn = gr.Button("Connect")
        
        status = gr.Textbox(label="Connection Status", interactive=False)
        
        chatbot = gr.Chatbot(
            value=[], 
            height=500,
            type="messages",
            show_copy_button=True,
            # avatar_images=("👤", "🤖")
        )
        
        with gr.Row(equal_height=True):
            msg = gr.Textbox(
                label="Your Question",
                placeholder="Ask about weather or alerts (e.g., What's the weather in New York?)",
                scale=4
            )
            clear_btn = gr.Button("Clear Chat", scale=1)
        
        set_api_key_btn.click(client.set_api_key, inputs=api_key, outputs=api_key_status)
        connect_btn.click(client.connect, inputs=server_path, outputs=status)
        msg.submit(client.process_message, [msg, chatbot], [chatbot, msg])
        clear_btn.click(lambda: [], None, chatbot)
        
    return demo

if __name__ == "__main__":
    # if not os.getenv("ANTHROPIC_API_KEY"):
    #     print("Warning: ANTHROPIC_API_KEY not found in environment. Please set it in your .env file.")
    
    interface = gradio_interface()
    interface.launch(debug=True)