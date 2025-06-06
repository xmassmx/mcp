# MCP (Model Control Protocol) Weather Assistant

A Python-based weather information system that uses the Model Control Protocol (MCP) to provide weather forecasts and alerts through a user-friendly Gradio interface.

## Project Structure

```
mcp/
├── client/
│   ├── app.py          # Gradio web interface
│   ├── client.py       # MCP client implementation
│   └── pyproject.toml  # Client dependencies
└── server/
    ├── weather.py      # Weather service implementation
    └── pyproject.toml  # Server dependencies
```

## Features

- Real-time weather forecasts for any location using latitude and longitude
- Active weather alerts for US states
- User-friendly web interface built with Gradio
- Secure API key management
- Interactive chat-based interface

## Prerequisites

- Python 3.8 or higher
- Groq API key (for the client)
- Internet connection for weather data

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mcp
```

2. Set up the client environment:
```bash
cd client
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

3. Set up the server environment:
```bash
cd ../server
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

## Usage

1. Start the server:
```bash
cd server
python weather.py
```

2. In a new terminal, start the client:
```bash
cd client
python app.py
```

3. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:7860)

4. In the web interface:
   - Enter your Groq API key
   - Set the server script path (default: ./server/weather.py)
   - Click "Connect" to establish connection
   - Start asking questions about weather!

## Example Queries

- "What's the weather forecast for New York City?"
- "Are there any weather alerts in California?"
- "What's the forecast for latitude 40.7128 and longitude -74.0060?"

## API Endpoints

The server provides two main endpoints:

1. `get_forecast(latitude: float, longitude: float)`
   - Returns a detailed weather forecast for the specified location
   - Includes temperature, wind conditions, and detailed forecast

2. `get_alerts(state: str)`
   - Returns active weather alerts for the specified US state
   - Uses two-letter state codes (e.g., CA, NY)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license information here]
