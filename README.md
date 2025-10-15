# KSTAR MCP PoC v2 - Natural Language Plasma Control System

🚀 **Interactive Real-time Control System with Natural Language Command Translation**

A proof-of-concept system that enables researchers to control KSTAR plasma parameters using natural language commands, with real-time visualization of the command translation process and temperature changes.

**Note**: This is a PoC demonstrating a simple approach where target values are set and current values gradually follow the targets. This approach is designed for demonstration purposes and future versions will integrate with sophisticated simulation models and machine learning algorithms for more realistic plasma physics behavior.

## 🌟 Key Features

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
- macOS/Linux/Windows
- Python 3.13+
- EPICS Base 7.0.9 with SoftIOC

### Required Software
- EPICS Base with SoftIOC
- Python virtual environment
- OpenAI API key (optional - demo mode works without it)

## 🛠️ Installation Guide

### Step 1: Install EPICS Base and SoftIOC

1. **Download EPICS Base 7.0.9**:
   ```bash
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
   export EPICS_BASE=/path/to/epics/base-7.0.9
   export PATH=$EPICS_BASE/bin/darwin-aarch64:$PATH  # Adjust for your platform
   ```

4. **Verify SoftIOC Installation**:
   ```bash
   which softIoc
   # Should output: /path/to/epics/base/bin/darwin-aarch64/softIoc
   ```

### Step 2: Clone and Setup Project

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/kstar-mcp-poc-v2.git
   cd kstar-mcp-poc-v2
   ```

2. **Create Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**:
   ```bash
   cp config.env.example .env
   # Edit .env and add your OpenAI API key (optional for demo mode)
   ```

## 🚀 Quick Start

### Option 1: Demo Mode (Recommended for First Time)

1. **Start the Application**:
   ```bash
   python main.py
   ```

2. **Open Web Browser**:
   Navigate to `http://localhost:8000`

3. **Try Commands**:
   - Enter: `"Raise plasma temperature to 12 keV"`
   - Click "Execute Command"
   - Watch the real-time translation and temperature changes!

### Option 2: With OpenAI API (Full LLM Mode)

1. **Set up API Key**:
   ```bash
   # Edit .env file and add:
   OPENAI_API_KEY=your_openai_api_key_here
   ```

2. **Start the Application**:
   ```bash
   python main.py
   ```

### Option 3: With EPICS SoftIOC (Advanced)

1. **Start SoftIOC** (in separate terminal):
   ```bash
   export EPICS_CA_AUTO_ADDR_LIST=NO
   export EPICS_CA_ADDR_LIST=127.0.0.1
   softIoc -d databases/kstar_control.db
   ```

2. **Start the Application** (in another terminal):
   ```bash
   python main.py
   ```

## 📁 Project Structure

```
kstar_mcp_poc_v2/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.env.example       # Environment configuration template
├── main.py                  # Main application entry point
├── test_system.py           # System testing script
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

## 🔧 Technical Details

### Architecture

- **Frontend**: HTML5 + JavaScript + WebSocket
- **Backend**: FastAPI + WebSocket
- **LLM**: OpenAI GPT-4o-mini (optional)
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

## 🧪 Testing

Run the test suite to verify system functionality:

```bash
# Test all components
python test_system.py --component all

# Test individual components
python test_system.py --component parser
python test_system.py --component epics
python test_system.py --component engine
```

## 🐛 Troubleshooting

### Common Issues

1. **Port 8000 Already in Use**:
   ```bash
   lsof -ti:8000 | xargs kill -9  # macOS/Linux
   netstat -ano | findstr :8000   # Windows
   ```

2. **EPICS Connection Failed**:
   - Check SoftIOC is running
   - Verify environment variables
   - Use Demo Mode for testing

3. **OpenAI API Error**:
   - Verify API key in `.env` file
   - Check API key has sufficient credits

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
3. Run the test suite

---

**Happy Plasma Controlling! 🌟**