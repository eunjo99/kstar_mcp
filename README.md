# KSTAR MCP PoC v2 - Interactive Real-time Control System

🚀 **Natural Language to EPICS Command Translation with Real-time Monitoring**

A proof-of-concept system that enables researchers to control KSTAR plasma parameters using natural language commands, with real-time visualization of the command translation process and temperature changes.

## 🌟 Features

- **Natural Language Interface**: Control plasma temperature using simple English commands
- **Real-time Command Translation**: Visualize how LLM converts natural language to EPICS SET commands
- **Interactive Monitoring**: Real-time temperature, coil current, and heater power monitoring
- **Demo Mode**: Complete simulation without requiring actual EPICS hardware
- **Web-based UI**: Modern, responsive web interface with WebSocket updates

## 🎯 Demo Commands

Try these natural language commands:

```
"Raise plasma temperature to 12 keV"
"Set temperature to 8 keV for 3 seconds"
"Increase heater power to 80%"
"Lower temperature to 6 keV"
```

## 📋 Prerequisites

### System Requirements
- macOS (tested on macOS 14.6.0)
- Python 3.13+
- EPICS Base 7.0.9

### Required Software
- EPICS Base with SoftIOC
- Python virtual environment
- OpenAI API key

## 🛠️ Installation Guide

### Step 1: Install EPICS Base

1. **Download EPICS Base 7.0.9**:
   ```bash
   cd ~/Desktop/EnF/epics_mcp
   wget https://epics.anl.gov/download/base/base-7.0.9.tar.gz
   tar -xzf base-7.0.9.tar.gz
   ```

2. **Build EPICS Base**:
   ```bash
   cd base-7.0.9
   make
   ```

3. **Set Environment Variables**:
   ```bash
   export EPICS_BASE=/Users/eunjo/Desktop/EnF/epics_mcp/base-7.0.9
   export PATH=$EPICS_BASE/bin/darwin-aarch64:$PATH
   ```

### Step 2: Install SoftIOC

SoftIOC is included with EPICS Base. Verify installation:
```bash
which softIoc
# Should output: /path/to/epics/base/bin/darwin-aarch64/softIoc
```

### Step 3: Set Up Python Environment

1. **Create Virtual Environment**:
   ```bash
   cd ~/Desktop/EnF/epics_mcp
   python3 -m venv epics
   source epics/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   cd kstar_mcp_poc_v2
   pip install -r requirements.txt
   ```

### Step 4: Configure Environment

1. **Create Environment File**:
   ```bash
   cp config.env.example .env
   ```

2. **Edit .env file**:
   ```bash
   # Add your OpenAI API key
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   
   # EPICS Configuration
   EPICS_CA_AUTO_ADDR_LIST=NO
   EPICS_CA_ADDR_LIST=127.0.0.1
   EPICS_CA_SERVER_PORT=5064
   EPICS_CA_REPEATER_PORT=5065
   
   # Server Configuration
   HOST=0.0.0.0
   PORT=8000
   DEBUG=True
   ```

## 🚀 Quick Start

### Option 1: Demo Mode (Recommended for Testing)

1. **Start the Server**:
   ```bash
   cd kstar_mcp_poc_v2
   source ../epics/bin/activate
   python main.py
   ```

2. **Open Web Browser**:
   Navigate to `http://localhost:8000`

3. **Try Commands**:
   - Enter: `"Raise plasma temperature to 12 keV"`
   - Click "Execute Command"
   - Watch the real-time translation and temperature changes!

### Option 2: With EPICS SoftIOC (Advanced)

1. **Start SoftIOC** (in separate terminal):
   ```bash
   cd kstar_mcp_poc_v2
   source ../epics/bin/activate
   export EPICS_CA_AUTO_ADDR_LIST=NO
   export EPICS_CA_ADDR_LIST=127.0.0.1
   softIoc -d databases/kstar_control.db
   ```

2. **Start the Server** (in another terminal):
   ```bash
   cd kstar_mcp_poc_v2
   source ../epics/bin/activate
   python main.py
   ```

## 📁 Project Structure

```
kstar_mcp_poc_v2/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.env.example       # Environment configuration template
├── .env                     # Your environment configuration
├── main.py                  # Main application entry point
├── databases/
│   └── kstar_control.db     # EPICS database for KSTAR simulation
└── src/
    ├── core/
    │   └── execution_engine.py  # Command execution logic
    ├── epics/
    │   └── controller.py        # EPICS PV communication
    ├── llm/
    │   └── command_parser.py     # Natural language parsing
    └── ui/
        └── demo_ui.py           # Web UI (FastAPI + WebSocket)
```

## 🎮 Usage Guide

### Web Interface

1. **Natural Language Commands**: Type commands in English
2. **Command Translation**: Watch the 4-step translation process:
   - Natural Language Input
   - LLM Interpretation
   - EPICS SET Commands
   - Execution Results
3. **Real-time Monitoring**: Observe temperature changes on the chart
4. **Command History**: Review all executed commands

### Supported Commands

- **Temperature Control**:
  - `"Raise plasma temperature to 12 keV"`
  - `"Set temperature to 8 keV for 3 seconds"`
  - `"Lower temperature to 6 keV"`

- **Power Control**:
  - `"Increase heater power to 80%"`
  - `"Set coil current to 1500A"`

### Demo Mode Features

- **Simulation**: No actual EPICS hardware required
- **Realistic Behavior**: Temperature changes gradually toward target
- **Complete Translation**: Full natural language → EPICS command pipeline
- **Real-time Updates**: WebSocket-based live monitoring

## 🔧 Technical Details

### Architecture

- **Frontend**: HTML5 + JavaScript + WebSocket
- **Backend**: FastAPI + WebSocket
- **LLM**: OpenAI GPT-4o-mini
- **EPICS**: Process Variables (PVs) for control
- **Simulation**: In-memory PV simulation

### Key Components

1. **Command Parser**: Converts natural language to structured commands
2. **Execution Engine**: Orchestrates command execution and monitoring
3. **EPICS Controller**: Manages PV communication
4. **Web UI**: Real-time visualization and control interface

### Process Variables (PVs)

- `KSTAR:PCS:TE:SP`: Temperature Setpoint
- `KSTAR:PCS:TE:RBV`: Temperature Readback Value
- `KSTAR:COIL:CURR`: Coil Current
- `KSTAR:HEATER:POW`: Heater Power

## 🐛 Troubleshooting

### Common Issues

1. **Port 8000 Already in Use**:
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

2. **EPICS Connection Failed**:
   - Check SoftIOC is running
   - Verify environment variables
   - Use Demo Mode for testing

3. **OpenAI API Error**:
   - Verify API key in `.env` file
   - Check API key has sufficient credits

### Debug Mode

Enable debug output by adding print statements in `src/ui/demo_ui.py`:
```python
print(f"DEBUG: Command received: {command}")
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for research and educational purposes.

## 🙏 Acknowledgments

- EPICS Community for the control system framework
- OpenAI for the language model capabilities
- KSTAR Research Team for the plasma physics context

## 📞 Support

For questions or issues:
1. Check the troubleshooting section
2. Review the project structure
3. Enable debug mode for detailed logging

---

**Happy Plasma Controlling! 🌟**