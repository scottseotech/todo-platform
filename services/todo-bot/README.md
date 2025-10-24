# Todo Slack Bot

A Slack bot for managing todos using slash commands. Built with Slack Bolt SDK for Python using Socket Mode (no public endpoint required).

## Features

- **`/todo` command**: Add todos directly from Slack
- **Socket Mode**: No need to expose a public endpoint
- **Rich formatting**: Uses Slack blocks for better UI
- **Error handling**: Graceful error messages
- **Python-based**: Easy to extend and integrate

## Setup

### Prerequisites

- Python 3.7 or higher
- A Slack workspace where you can install apps
- Slack App with Socket Mode enabled

### Slack App Configuration

1. **Create a Slack App** at https://api.slack.com/apps
   - Choose "From scratch"
   - Give it a name (e.g., "Todo Bot")
   - Select your workspace

2. **Enable Socket Mode**
   - Go to "Socket Mode" in the sidebar
   - Enable Socket Mode
   - Generate an App-Level Token with `connections:write` scope
   - Save the token as `SLACK_APP_TOKEN`

3. **Add Bot Token Scopes**
   - Go to "OAuth & Permissions"
   - Add these Bot Token Scopes:
     - `chat:write` - Send messages
     - `commands` - Use slash commands
     - `app_mentions:read` - Respond to mentions (optional)
     - `im:history` - Read DM history (optional)

4. **Create Slash Command**
   - Go to "Slash Commands"
   - Click "Create New Command"
   - Command: `/todo`
   - Short Description: "Add a new todo item"
   - Usage Hint: `<todo text>`
   - (Socket Mode means you don't need a Request URL)

5. **Install App to Workspace**
   - Go to "Install App"
   - Click "Install to Workspace"
   - Authorize the app
   - Save the Bot Token as `SLACK_BOT_TOKEN`

6. **Get Signing Secret**
   - Go to "Basic Information"
   - Find "Signing Secret"
   - Save it as `SLACK_SIGNING_SECRET`

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Edit .env and add your Slack tokens
```

### Environment Variables

Create a `.env` file with:

```env
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
TODO_API_URL=http://localhost:8080
```

## Running the Bot

### Development

```bash
python app.py
```

### Production

For production, consider using a process manager like `systemd`, `supervisor`, or running in a container.

```bash
# With systemd
sudo systemctl start todo-bot

# With Docker
docker run -d --env-file .env todo-bot
```

The bot will connect to Slack via WebSocket (Socket Mode) and start listening for commands.

## Usage

### Add a Todo

In any Slack channel or DM where the bot is installed:

```
/todo Buy groceries
/todo "Call dentist tomorrow"
/todo Finish project report
```

The bot will:
1. Acknowledge your command immediately
2. Create the todo via the Todo API (to be implemented)
3. Respond with a confirmation message

### Example Response

```
✅ Todo added successfully!

📝 Buy groceries

Added by @username | 2024-12-25 15:45:30
```

## Architecture

```
┌─────────────┐           ┌──────────────┐           ┌──────────────┐
│   Slack     │  Socket   │  Todo Bot    │   HTTP    │  Todo API    │
│   Client    │◄─────────►│  (Python)    │◄─────────►│   (Go)       │
└─────────────┘    Mode   └──────────────┘           └──────────────┘
```

- **Socket Mode**: Bot maintains a WebSocket connection to Slack
- **No Public Endpoint**: No need for HTTPS or port forwarding
- **REST API**: Bot calls Todo API via HTTP

## Code Structure

- `app.py` - Main application with Slack Bolt setup
- `requirements.txt` - Python dependencies
- `.env.example` - Example environment variables
- `README.md` - This file

## Adding Todo API Integration

To integrate with the Todo API, update the `/todo` command handler in `app.py`:

```python
import requests

# Inside handle_todo_command function, replace the TODO comment:
response = requests.post(
    f"{TODO_API_URL}/api/v1/todos",
    json={"title": cleaned_text},
    headers={"Content-Type": "application/json"}
)

if response.status_code != 201:
    raise Exception(f"API error: {response.status_code}")

todo = response.json()
```

Or use the todo-client-python:

```python
import sys
sys.path.append('../../clients/todo-client-python')
from todoclient import TodoClient

# Initialize client
client = TodoClient(TODO_API_URL)

# Inside handle_todo_command:
todo = client.create_todo(cleaned_text)
```

## Future Enhancements

- [ ] Integrate with Todo API
- [ ] List todos: `/todo list`
- [ ] Complete todo: `/todo done <id>`
- [ ] Delete todo: `/todo delete <id>`
- [ ] Interactive buttons for todo management
- [ ] Scheduled reminders
- [ ] User-specific todos

## Troubleshooting

### Bot doesn't respond to commands

1. Check that Socket Mode is enabled
2. Verify `SLACK_APP_TOKEN` has `connections:write` scope
3. Check bot logs for connection errors
4. Ensure the bot is installed in your workspace

### Command not found

1. Verify the slash command is created in Slack App settings
2. Reinstall the app to your workspace
3. Check that the command name matches exactly (`/todo`)

### Import errors

1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check Python version: `python --version` (should be 3.7+)

## License

Part of the scottseo.tech todo-platform monorepo.
