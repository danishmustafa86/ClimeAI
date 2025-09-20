## [ClimeAI Agent](https://github.com/Coral-Protocol/Clime-AI-Agent)

ClimeAI Agent is an intelligent weather assistant that provides real-time weather information, forecasts, and weather-aware guidance through natural language conversations.

## Responsibility
ClimeAI Agent serves as a conversational weather expert that helps users with weather-related queries including current conditions, hourly/daily forecasts, and weather-aware travel/event planning. It maintains conversation context and provides actionable weather insights.

## Details
- **Framework**: LangGraph, LangChain
- **Tools used**: OpenWeatherMap API, OpenCageData Geocoding API
- **AI model**: GPT-4o-2024-08-06 (via AIML API)
- **Date added**: September 18, 2025
- **License**: MIT

## Features
- **Current Weather**: Real-time weather conditions for any location
- **Forecasts**: Hourly and 7-day daily weather forecasts
- **Historical Weather**: Weather data for specific timestamps
- **Conversational Interface**: Natural language weather queries
- **Context Awareness**: Maintains conversation history and context
- **Geocoding**: Automatic city name to coordinates conversion
- **Weather Tools**: Multiple specialized weather data endpoints

## Setup the Agent

### 1. Clone & Install Dependencies

<details>  

```bash
# In a new terminal clone the repository:
git clone https://github.com/Coral-Protocol/Clime-AI-Agent.git

# Navigate to the project directory:
cd Clime-AI-Agent

# Download and run the UV installer, setting the installation directory to the current one
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=$(pwd) sh

# Create a virtual environment named `.venv` using UV
uv venv .venv

# Activate the virtual environment
source .venv/bin/activate

# install uv
pip install uv

# Install dependencies from `pyproject.toml` using `uv`:
uv sync
```

</details>

### 2. Configure Environment Variables

Get the API Keys:
- [AIML API](https://aimlapi.com/) - For LLM responses
- [OpenWeatherMap](https://openweathermap.org/api) - For weather data
- [OpenCageData](https://opencagedata.com/api) - For geocoding

<details>

```bash
# Create .env file in project root
cp -r .env_sample .env

# Edit .env file with your API keys:
# AIML_API_KEY=your_aiml_api_key_here
# OPENWEATHERMAP_API_KEY=your_openweathermap_api_key_here
# OPENCAGE_API_KEY=your_opencage_api_key_here
# MODEL_NAME=gpt-4o-2024-08-06
# MONGODB_URI=mongodb://localhost:27017/
```

</details>

## Run the Agent

You can run in either of the below modes to get your system running.  

- The Executable Model is part of the Coral Protocol Orchestrator which works with [Coral Studio UI](https://github.com/Coral-Protocol/coral-studio).  
- The Dev Mode allows the Coral Server and all agents to be seperately running on each terminal without UI support.  

### 1. Executable Mode

Checkout: [How to Build a Multi-Agent System with Awesome Open Source Agents using Coral Protocol](https://github.com/Coral-Protocol/existing-agent-sessions-tutorial-private-temp) and update the file: `coral-server/src/main/resources/application.yaml` with the details below, then run the [Coral Server](https://github.com/Coral-Protocol/coral-server) and [Coral Studio UI](https://github.com/Coral-Protocol/coral-studio). You do not need to set up the `.env` in the project directory for running in this mode; it will be captured through the variables below.

<details>

For Linux or MAC:

```bash

registry:
  # ... your other agents
  clime-ai-agent:
    options:
      - name: "AIML_API_KEY"
        type: "string"
        description: "API key for AIML API provider"
      - name: "OPENWEATHERMAP_API_KEY"
        type: "string"
        description: "API key for OpenWeatherMap weather data"
      - name: "OPENCAGE_API_KEY"
        type: "string"
        description: "API key for OpenCageData geocoding"
      - name: "MODEL_NAME"
        type: "string"
        description: "What model to use (e.g 'gpt-4o-2024-08-06')"
        default: "gpt-4o-2024-08-06"
      - name: "MONGODB_URI"
        type: "string"
        description: "MongoDB connection URI"
        default: "mongodb://localhost:27017/"

    runtime:
      type: "executable"
      command: ["bash", "-c", "<replace with path to this agent>/run_agent.sh main.py"]
      environment:
        - option: "AIML_API_KEY"
        - option: "OPENWEATHERMAP_API_KEY"
        - option: "OPENCAGE_API_KEY"
        - option: "MODEL_NAME"
        - option: "MONGODB_URI"


```

For Windows, create a powershell command (run_agent.ps1) and run:

```bash
command: ["powershell","-ExecutionPolicy", "Bypass", "-File", "${PROJECT_DIR}/run_agent.ps1","main.py"]
```

</details>

### 2. Dev Mode

Ensure that the [Coral Server](https://github.com/Coral-Protocol/coral-server) is running on your system and run below command in a separate terminal.

<details>

```bash
# Run the agent using `uv`:
uv run python main.py
```

You can view the agents running in Dev Mode using the [Coral Studio UI](https://github.com/Coral-Protocol/coral-studio) by running it separately in a new terminal.

</details>

## Example

<details>

```bash
# Input:
User: What's the current weather in New York?

# Output:
ClimeAI: 🌤️ Current weather in New York:

**Temperature**: 22°C (72°F)
**Feels like**: 24°C (75°F)
**Conditions**: Partly cloudy
**Humidity**: 65%
**Wind**: 12 km/h from the west
**Visibility**: 10 km

Perfect weather for outdoor activities! The partly cloudy skies provide good visibility and comfortable temperatures. Consider light layers as it feels slightly warmer than the actual temperature.

Would you like a forecast for the next few hours or days?
```

</details>

## API Endpoints

The agent provides the following capabilities:
- **Current Weather**: Get real-time conditions for any city
- **Hourly Forecast**: 24-hour weather forecast
- **Daily Forecast**: 7-day weather outlook
- **Historical Weather**: Weather data for specific timestamps
- **Weather Advice**: Contextual recommendations based on conditions

## Creator Details
- **Name**: ClimeAI Development Team
- **Affiliation**: Coral Protocol
- **Contact**: [Discord](https://discord.com/invite/Xjm892dtt3)
