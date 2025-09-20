## [Event Advisor Weather Agent](https://github.com/Coral-Protocol/Event-Advisor-Weather-Agent)

Event Advisor Weather Agent provides weather-aware guidance for event planning, helping organizers make informed decisions about outdoor and indoor events based on forecasted weather conditions.

## Responsibility
Event Advisor Weather Agent analyzes weather conditions for specific locations and time windows to provide comprehensive event planning advice. It evaluates weather suitability, safety considerations, timing recommendations, and contingency planning for various event types.

## Details
- **Framework**: LangGraph, LangChain
- **Tools used**: OpenWeatherMap API, OpenCageData Geocoding API
- **AI model**: GPT-4o-2024-08-06 (via AIML API)
- **Date added**: September 18, 2025
- **License**: MIT

## Features
- **Location-Based Analysis**: Weather assessment for specific coordinates
- **Time-Window Planning**: Weather analysis for event duration
- **Event Type Awareness**: Indoor/outdoor event considerations
- **Safety Advisories**: Weather-related risk assessment
- **Timing Recommendations**: Optimal scheduling suggestions
- **Contingency Planning**: Backup plans for weather changes
- **Attire Suggestions**: Weather-appropriate clothing recommendations
- **Indoor Alternatives**: Alternative venue suggestions

## Setup the Agent

### 1. Clone & Install Dependencies

<details>  

```bash
# In a new terminal clone the repository:
git clone https://github.com/Coral-Protocol/Event-Advisor-Weather-Agent.git

# Navigate to the project directory:
cd Event-Advisor-Weather-Agent

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
  event-advisor-weather-agent:
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

    runtime:
      type: "executable"
      command: ["bash", "-c", "<replace with path to this agent>/run_agent.sh main.py"]
      environment:
        - option: "AIML_API_KEY"
        - option: "OPENWEATHERMAP_API_KEY"
        - option: "OPENCAGE_API_KEY"
        - option: "MODEL_NAME"


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
{
  "longitude": 73.0923,
  "latitude": 31.4221,
  "from_time": "2025-09-21T17:00:00Z",
  "to_time": "2025-09-21T20:00:00Z",
  "event_type": "outdoor",
  "event_details": "Evening community concert in the park. Family-friendly, open seating."
}

# Output:
Event Advisor: 🎵 **Event Weather Analysis for Evening Concert**

**Weather Summary:**
- **Start Time (5:00 PM)**: 28°C, Partly cloudy, Light breeze
- **End Time (8:00 PM)**: 24°C, Clear skies, Calm conditions

**Recommendations:**
✅ **Event Status**: PROCEED - Excellent conditions for outdoor concert

**Safety & Comfort:**
- Temperature will be comfortable throughout the event
- No precipitation expected
- Good visibility for evening performance
- Light wind won't affect sound quality

**Attendee Guidance:**
- Light layers recommended (temperature drops 4°C)
- No rain gear needed
- Consider bringing blankets for seating comfort
- Sunscreen not needed for evening event

**Event Setup:**
- Standard outdoor setup sufficient
- No weather-related equipment needed
- Sound system should work optimally
- Lighting may be needed as event ends at dusk

**Contingency Plan:**
- 95% confidence in current forecast
- Monitor for any sudden weather changes
- Indoor venue backup recommended for 100+ attendees
```

</details>

## Input Parameters

The agent accepts the following parameters:
- **longitude**: Event location longitude (required)
- **latitude**: Event location latitude (required)
- **from_time**: Event start time in ISO 8601 format (required)
- **to_time**: Event end time in ISO 8601 format (required)
- **event_type**: Type of event (indoor/outdoor/hybrid) (optional)
- **event_details**: Additional event context and requirements (optional)

## Output Features

The agent provides:
- **Weather Analysis**: Detailed conditions during event window
- **Safety Assessment**: Risk evaluation and mitigation strategies
- **Timing Recommendations**: Optimal scheduling suggestions
- **Attendee Guidance**: Weather-appropriate recommendations
- **Setup Instructions**: Event preparation based on conditions
- **Contingency Planning**: Backup plans for weather changes

## Creator Details
- **Name**: ClimeAI Development Team
- **Affiliation**: Coral Protocol
- **Contact**: [Discord](https://discord.com/invite/Xjm892dtt3)
