# AI Agent System for the Improbable Automata Newsletter

> *[Improbable Automata](https://improbable.beehiiv.com/) is a newsletter written by Alfie, an AI agent we're developing at [agency42](https://agency42.co/). This is an example implementation built as an early experiment. We're now working on [alchemist](https://github.com/k3nnethfrancis/alchemist), which is still built on [Mirascope](https://mirascope.com/), but integrates other tools and a simple graph framework to help chain together agent operations.*

An automated system for generating AI newsletters using a team of specialized agents, built with the Mirascope framework.

## System Overview

The system consists of several specialized agents working together:
- **Writer Agent**: Processes and categorizes content into structured newsletter sections using GPT-4
- **Discord Reader**: Fetches and formats content from Discord channels
- **Researcher**: Performs web research to supplement content (currently standalone)

## Setup

### Prerequisites
- Python 3.10 or higher
- A Discord bot with the following permissions:
  - Read Message History
  - View Channels
  - Message Content Intent enabled
- OpenAI API access (GPT-4 model access required)

### Installation
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables
Create a `.env` file with the following variables:

```bash
OPENAI_API_KEY=xx        # Your OpenAI API key
DISCORD_BOT_TOKEN=xx     # Your Discord bot token
DISCORD_SERVER_ID=xx     # ID of your Discord server
DISCORD_CHANNEL_ID=xx    # ID of the channel to monitor
```

## Current Working Features

The system is under development, with the following components currently operational:

1. **Discord Reader** (`tools/discord_reader.py`): Fully functional for fetching and processing Discord messages
2. **Writer Agent** (`agents/writer.py`): Fully functional for processing Discord content into newsletter sections
3. **Researcher** (`agents/researcher.py`): Functional but not yet integrated with the main workflow
4. **Agent Executor** (`executor.py`): Framework in place but needs configuration for full integration

## Usage

### Command Line Interface

1. Run the Discord Reader Demo:
   ```bash
   python tools/discord_reader.py
   ```
   This will demonstrate:
   - Fetching last week's messages
   - Fetching messages since a specific date
   - Fetching all historical messages
   - Fetching last month's messages

2. Run the Writer Agent:
   ```bash
   python agents/writer.py
   ```
   This will:
   - Load example messages
   - Process them through GPT-4
   - Output categorized content in JSON format

### Programmatic Usage

#### Discord Reader

```python
from tools.discord_reader import DiscordContentReader

# Initialize the reader
reader = DiscordContentReader(token=os.getenv('DISCORD_BOT_TOKEN'))

# Fetch recent content
messages = await reader.get_channel_content(
    channel_id=int(os.getenv('DISCORD_CHANNEL_ID'))
)
```

#### Writer Agent

```python
from agents.writer import Writer, WriterBase

# Configure the newsletter
config = WriterBase.NewsletterConfig(
    name="Improbable Automata",
    description="Field notes from the AI frontier",
    audience="Tech professionals",
    tone="Professional yet accessible",
    style_guide="Concise and practical",
    section_preferences={
        "Developments": "AI news and research",
        "Community": "Updates on AI community"
    }
)

# Initialize and run the writer
writer = Writer(newsletter_config=config)
result = await writer.process_content(
    token=os.getenv('DISCORD_BOT_TOKEN'),
    channel_id=int(os.getenv('DISCORD_CHANNEL_ID')),
    days=7  # Fetch last week's content
)
```

## Code Documentation

### Base Agent (`base.py`)
The foundation for all agents in the system:
- Provides the `OpenAIAgent` base class
- Handles message history management
- Defines the basic agent interface with `_step` and `run` methods

### Discord Reader (`tools/discord_reader.py`)
A utility for fetching and processing Discord content:
- Fetches messages from specified channels
- Processes message content, embeds, and attachments
- Provides both one-time and continuous reading capabilities
- Includes utilities for date-based message filtering

### Writer Agent (`agents/writer.py`)
Processes Discord content into structured newsletter sections:
- Configurable newsletter style and format
- Uses GPT-4 for content categorization
- Outputs JSON-structured content with categories and summaries
- Includes self-critique capabilities

### Researcher Agent (`agents/researcher.py`)
Standalone web research capabilities (not yet integrated):
- Web search using DuckDuckGo
- Webpage content parsing
- GPT-4 powered research summarization
- Configurable search result limits

### Agent Executor (`executor.py`)
Framework for agent orchestration (needs configuration):
- Handles agent initialization and coordination
- Provides retry mechanisms for API calls
- Includes error handling and validation
- Will eventually manage the full agent workflow

## Development

### Adding New Agents

1. Inherit from `OpenAIAgent` in `base.py`
2. Implement the required `_step` method
3. Use the Mirascope decorators for OpenAI integration:
   - `@openai.call` for model configuration
   - `@prompt_template` for structured prompts
   - `@retry` for error handling

### Future Integration Work

1. Configure the Agent Executor to manage the full workflow
2. Integrate the Researcher and the Writer Agent to work togther in `executor.py`
