# Agentic-AI-Model-using-Gemini

A modular, extensible AI agent framework built on [Google Gemini](https://deepmind.google/technologies/gemini/) and Python. This project enables users to create, register, and orchestrate AI-powered functions for agentic workflows, with a web interface.

## Features

- **Agentic Function Orchestration**: Chain and compose AI functions.
- **Gemini Integration**: Uses Google Gemini for LLM-based tasks.
- **Web Interface**: Interact with agents via a FastAPI web app.
- **Custom Function Registry**: Dynamically register user-defined functions.
- **Multi-language Support**: Backend in Python, frontend in HTML/CSS/JS.

---

## Installation

### Prerequisites

- Python 3.8+
- [pip](https://pip.pypa.io/en/stable/)
- (Optional) [Node.js](https://nodejs.org/) for frontend development

### Clone the Repository

```bash
git clone https://github.com/SanjitKamath/Agentic-AI-Model-using-Gemini.git
cd Agentic-AI-Model-using-Gemini
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Setup

1. Obtain your Gemini API key and set it as an environment variable:

   ```bash
   export GEMINI_API_KEY=your_api_key_here
   ```

2. (Optional) If using `.env`:

   ```
   GEMINI_API_KEY=your_api_key_here
   ```

---

## Usage

### Run the FastAPI Web Application

```bash
python main.py
```

Open your browser and navigate to `http://localhost:8000` to interact with the agent.

---

# How to Register a New Function

This guide outlines the steps required to add a new function to the agent, making it available as a tool for the AI to use. The process involves writing the function's logic and then registering it with the agent's decorator.


## Step 1: Write the Function's Core Logic

First, write the Python code for your function. By convention, this logic should be placed in the `functions.py` file corresponding to its domain. If you're adding a function to a new domain, you'll first need to create a new module folder (e.g., `modules/finance/`).

**Example:** Let's create a new function to get a support ticket's status. We'll place it in a new module called `support`.

**File:** `modules/support/functions.py`
```python
def get_ticket_status(ticket_id: str) -> dict:
    """Retrieves the status of a specific support ticket."""
    mock_db = {
        "TICKET-001": {"status": "Resolved", "priority": "High"},
        "TICKET-002": {"status": "In Progress", "priority": "Medium"},
    }
    status = mock_db.get(ticket_id)
    if status:
        return {"ticket_id": ticket_id, **status}
    else:
        return {"error": f"Ticket {ticket_id} not found."}
```
## Step 2: Register the Function as a Tool
For the agent to see your function, you must register it in the corresponding tools.py file. This is done by importing the function and wrapping it with the @register decorator from the agent's registry.

The @register decorator requires two important arguments:

name: The exact name the AI will use to call the function.

description: A clear, detailed explanation of what the function does. A good description is crucial for the AI to understand when to use the tool.

**File:** `modules/support/tools.py`

```python
from agent.registry import register
from .functions import get_ticket_status

@register(
    name="get_ticket_status",
    description="Fetches the current status and priority of a customer support ticket using its unique ID."
)
def decorated_get_ticket_status(ticket_id: str) -> dict:
    return get_ticket_status(ticket_id)
```
Note: Don't forget to create the __init__.py files in modules/support/ and modules/ if they don't already exist.

## Step 3: Restart and Verify
The agent discovers all available tools when it starts. For your new function to be loaded, you must restart the server.

After restarting, the debug output in your terminal should now include your new function in the list of registered tools:

```bash
--- AGENT REGISTRY LOADED ---
Registered functions: ['check_eligibility', 'is_eligible_for_raise', ..., 'get_ticket_status']
Your new function is now ready to be used by the agent.
```
---

## Project Structure

```
Agentic-AI-Model-using-Gemini/
├── app.py                  # Main Flask app
├── functions/              # Custom and core agent functions
│   ├── __init__.py
│   └── custom_functions.py # Add your functions here
├── model/                  # Gemini model orchestration
├── templates/              # HTML templates
├── static/                 # CSS, JS, images
├── requirements.txt
├── README.md
└── tests/                  # Unit tests
```

---
Note: employees.csv is a dummy database containing AI generated data of 100 emplpoyees, simply to provide a demo of the project
