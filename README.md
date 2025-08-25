# Pipecat + BAML vs. Vanilla Prompting: Voice Agent Comparison

## 🎯 **Project Overview**

This project implements and compares two voice agents built on Pipecat:
1. **BAML-powered agent** using structured prompts and type-safe interactions
2. **Vanilla agent** using traditional string-based prompting

The goal is to evaluate whether BAML provides measurable improvements in voice agent performance, latency, and reliability.

## 🏗️ **Architecture**

Both agents use the same Pipecat infrastructure:
- **Speech-to-Text**: Deepgram STT
- **Language Model**: OpenAI GPT-4o-mini
- **Text-to-Speech**: Cartesia TTS
- **Transport**: Daily.co for real-time voice communication

### Agent Variants

#### 1. BAML Agent (`baml_agent.py`)
- Uses BAML for structured prompt management
- Type-safe customer support interactions
- Structured response handling
- Built-in validation and error handling

#### 2. Vanilla Agent (`vanilla_agent.py`)
- Traditional string-based prompting
- Manual prompt construction
- Basic error handling
- Same core functionality without BAML benefits

## 🚀 **Quick Start**

### Prerequisites
- Python 3.8+
- OpenAI API key
- Deepgram API key
- Cartesia API key
- Daily.co account and room

### Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd pipecat-o1

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.template .env
# Edit .env with your API keys
```

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_key
DEEPGRAM_API_KEY=your_deepgram_key
CARTESIA_API_KEY=your_cartesia_key
DAILY_TOKEN=your_daily_token
DAILY_ROOM_URL=your_daily_room_url
CARTESIA_VOICE_ID=clara  # or your preferred voice
```

### Running the Agents

#### BAML Agent
```bash
python baml_agent.py
```

#### Vanilla Agent
```bash
python vanilla_agent.py
```

## 🧪 **Evaluation Framework**

### Test Scenarios
The evaluation covers 5-10 realistic customer support scenarios:

1. **Simple Query**: "What are your business hours?"
2. **Product Information**: "Tell me about your premium plan"
3. **Technical Issue**: "I can't log into my account"
4. **Billing Question**: "Why was I charged twice?"
5. **Feature Request**: "Can you add mobile app support?"
6. **Complaint Handling**: "Your service was down yesterday"
7. **Account Management**: "How do I change my password?"
8. **Pricing Inquiry**: "What's the difference between plans?"
9. **Integration Question**: "Does this work with Slack?"
10. **Escalation Scenario**: "I need to speak to a supervisor"

### Metrics Collected

#### 1. **Latency Metrics**
- Time to first response (TTFR)
- End-to-end conversation time
- STT processing time
- LLM response generation time
- TTS synthesis time

#### 2. **Accuracy Metrics**
- Turn accuracy (correct responses per turn)
- Context retention across conversation
- Response relevance score (1-5 scale)
- Intent recognition accuracy

#### 3. **Handoff Success**
- Successful escalation rate
- Human agent handoff success
- Fallback mechanism effectiveness

## 📊 **Running Evaluations**

### Automated Testing
```bash
# Run comprehensive evaluation
python evaluate_agent.py --agent baml --scenarios all
python evaluate_agent.py --agent vanilla --scenarios all

# Run specific scenario
python evaluate_agent.py --agent baml --scenario "billing_question"
```

### Manual Testing
```bash
# Interactive testing mode
python evaluate_agent.py --agent baml --interactive
```

## 📈 **Results & Analysis**

### Performance Comparison
- **Latency**: BAML vs Vanilla response times
- **Accuracy**: Response quality and relevance
- **Reliability**: Error rates and fallback success
- **User Experience**: Conversation flow and naturalness

### Key Findings
- [To be populated after testing]
- [Performance metrics and analysis]
- [Clear winner determination with evidence]

## 🔧 **Technical Details**

### BAML Implementation
- Structured prompt templates
- Type-safe response handling
- Built-in validation
- Error handling and fallbacks

### Vanilla Implementation
- String concatenation for prompts
- Manual response parsing
- Basic error handling
- Same core functionality

### Compatibility Layer
- `deepgram_compatibility.py`: Fixes Deepgram API compatibility issues
- Ensures both agents work with current library versions

## 📁 **File Structure**
```
pipecat-o1/
├── README.md                    # This file
├── baml_agent.py               # BAML-powered voice agent
├── vanilla_agent.py            # Vanilla prompting agent
├── evaluate_agent.py           # Evaluation framework
├── deepgram_compatibility.py   # API compatibility layer
├── test_apis.py                # API connectivity testing
├── test_pipecat_services.py   # Service integration testing
├── test_all_services.py        # Comprehensive service testing
├── requirements.txt            # Python dependencies
├── .env.template               # Environment variables template
└── results/                    # Evaluation results and metrics
    ├── baml_results.json
    ├── vanilla_results.json
    └── comparison_report.md
```

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 **License**

[Your License Here]

## 🆘 **Support**

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section below

## 🔍 **Troubleshooting**

### Common Issues
1. **Deepgram Import Errors**: Ensure `deepgram_compatibility.py` is imported first
2. **Cartesia TaskManager**: Services must be initialized within Pipecat pipeline context
3. **API Key Issues**: Verify all environment variables are set correctly

### Testing APIs
```bash
# Test all services
python test_all_services.py

# Test individual APIs
python test_apis.py
```
