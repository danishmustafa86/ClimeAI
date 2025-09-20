## [Travel Advisor Weather Agent](https://github.com/Coral-Protocol/Travel-Advisor-Weather-Agent)

Travel Advisor Weather Agent provides comprehensive weather-aware travel guidance by analyzing conditions at origin and destination locations, offering transportation-specific recommendations and safety advisories for optimal travel planning.

## Responsibility
Travel Advisor Weather Agent evaluates weather conditions at departure and arrival locations to provide practical, safety-focused travel guidance. It considers transportation modes, timing, route optimization, and packing recommendations based on forecasted weather conditions.

## Details
- **Framework**: LangGraph, LangChain
- **Tools used**: OpenWeatherMap API, OpenCageData Geocoding API
- **AI model**: GPT-4o-2024-08-06 (via AIML API)
- **Date added**: September 18, 2025
- **License**: MIT

## Features
- **Multi-Location Analysis**: Weather assessment at origin and destination
- **Transportation-Specific Guidance**: Vehicle-type considerations (car, flight, train, bus, etc.)
- **Safety-First Approach**: Risk assessment and mitigation strategies
- **Timing Recommendations**: Optimal departure/arrival scheduling
- **Route Optimization**: Weather-aware travel suggestions
- **Packing Checklists**: Weather-appropriate items and gear
- **Local Considerations**: Regional weather patterns and conditions
- **Delay Predictions**: Weather-related travel disruption forecasts

## Setup the Agent

### 1. Clone & Install Dependencies

<details>  

```bash
# In a new terminal clone the repository:
git clone https://github.com/Coral-Protocol/Travel-Advisor-Weather-Agent.git

# Navigate to the project directory:
cd Travel-Advisor-Weather-Agent

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
  travel-advisor-weather-agent:
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
  "from_longitude": 74.3587,
  "from_latitude": 31.5204,
  "to_longitude": 73.0479,
  "to_latitude": 33.6844,
  "from_time": "2025-09-21T06:30:00Z",
  "to_time": "2025-09-21T10:30:00Z",
  "vehicle_type": "car",
  "travel_details": "Early morning highway drive with two passengers and luggage."
}

# Output:
Travel Advisor: 🚗 **Travel Weather Analysis: Lahore to Islamabad**

**Route Overview:**
- **Origin**: Lahore (31.5204°N, 74.3587°E)
- **Destination**: Islamabad (33.6844°N, 73.0479°E)
- **Distance**: ~380 km via M2 Motorway
- **Duration**: ~4 hours

**Weather Conditions:**

**Departure (Lahore - 6:30 AM):**
- Temperature: 18°C, Clear skies
- Visibility: Excellent (10+ km)
- Wind: Light breeze (8 km/h)
- Road conditions: Dry and clear

**Arrival (Islamabad - 10:30 AM):**
- Temperature: 22°C, Partly cloudy
- Visibility: Good (8 km)
- Wind: Gentle breeze (12 km/h)
- Road conditions: Dry

**Travel Recommendations:**

✅ **GO/NO-GO**: PROCEED - Excellent driving conditions

**Safety Advisories:**
- Clear visibility throughout journey
- No precipitation expected
- Comfortable temperatures for driving
- Light winds won't affect vehicle stability

**Timing & Route:**
- Departure time is optimal
- M2 Motorway recommended (best maintained)
- Allow 30-minute buffer for rest stops
- Peak morning traffic expected in Lahore

**Vehicle-Specific Tips:**
- Check tire pressure (temperature variation)
- Ensure AC system working (comfort for passengers)
- Fuel up before departure (no weather delays expected)
- Standard highway driving conditions

**Packing Checklist:**
- Light jackets for morning chill
- Sunglasses for clear morning visibility
- Water bottles (4-hour journey)
- Snacks for passengers
- Emergency kit (standard items)

**Local Considerations:**
- Lahore: Urban traffic, good road conditions
- Islamabad: Mountain approach, watch for elevation changes
- M2 Motorway: Well-maintained, toll road
- Rest areas available every 50-60 km

**Confidence Level**: 95% - High confidence in forecast accuracy
```

</details>

## Input Parameters

The agent accepts the following parameters:
- **from_longitude**: Origin longitude (required)
- **from_latitude**: Origin latitude (required)
- **to_longitude**: Destination longitude (required)
- **to_latitude**: Destination latitude (required)
- **from_time**: Departure time in ISO 8601 format (required)
- **to_time**: Arrival time in ISO 8601 format (required)
- **vehicle_type**: Transportation mode (car/flight/train/bus/motorcycle/bicycle/walking) (optional)
- **travel_details**: Additional travel context and requirements (optional)

## Supported Transportation Modes

- **Car**: Highway driving, road conditions, fuel stops
- **Flight**: Airport weather, turbulence, delays
- **Train**: Rail conditions, station weather
- **Bus**: Public transport, route conditions
- **Motorcycle**: Wind conditions, visibility, gear requirements
- **Bicycle**: Wind, precipitation, temperature comfort
- **Walking**: Pedestrian safety, visibility, comfort

## Output Features

The agent provides:
- **Weather Analysis**: Conditions at origin and destination
- **Safety Assessment**: Risk evaluation and mitigation
- **Timing Recommendations**: Optimal scheduling suggestions
- **Route Guidance**: Weather-aware travel suggestions
- **Vehicle-Specific Tips**: Mode-appropriate recommendations
- **Packing Lists**: Weather-appropriate items and gear
- **Local Insights**: Regional considerations and patterns

## Creator Details
- **Name**: ClimeAI Development Team
- **Affiliation**: Coral Protocol
- **Contact**: [Discord](https://discord.com/invite/Xjm892dtt3)
