# Paint Agent with ASCII Calculations

## Overview
This project implements an autonomous agent that controls Microsoft Paint to visualize ASCII exponential calculations. The agent can:
1. Calculate the ASCII exponential sum for a given string
2. Visualize the result in Microsoft Paint (draw a rectangle and add text)
3. Save the visualization as an image
4. Email the image to a specified recipient

## Components

### 1. `paint_tools.py`
The core MCP (Model Control Protocol) server that provides tools for:
- Controlling Microsoft Paint (opening, drawing rectangles, adding text, saving)
- Calculating ASCII exponential sums
- Sending emails with attachments

### 2. `autonomous_paint_agent.py`
The main agent implementation that:
- Connects to the MCP server
- Uses Google's Gemini LLM to determine the execution order
- Processes user input for ASCII calculations and email recipients
- Manages the conversation with the LLM to complete the task

## Setup Instructions

### Prerequisites
- Python 3.8+
- Windows OS (for Paint automation)
- Gmail account (for email functionality)

### Installation
1. Install required dependencies:
   ```
   pip install python-dotenv google-generativeai mcp
   ```

2. For Paint automation (optional):
   ```
   pip install pywinauto pywin32
   ```

3. Create a `.env` file with the following variables:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   GMAIL_ADDRESS=your_gmail_address
   GMAIL_APP_PASSWORD=your_gmail_app_password
   ```

   Note: For Gmail, you need to create an App Password if you have 2-Factor Authentication enabled.

## Usage

### Running the Autonomous Agent
1. Execute the autonomous agent:
   ```
   python autonomous_paint_agent.py
   ```

2. When prompted, enter:
   - A string to calculate its ASCII exponential sum
   - An email address to send the visualization

3. The agent will:
   - Calculate the ASCII exponential sum
   - Open Paint and draw a rectangle
   - Add the calculation result as text
   - Save the image
   - Email the image to the specified recipient

### Canvas Configuration
The agent is configured for a 1152x648 pixel canvas with:
- Text positioned at (576, 324) - the center of the canvas
- Rectangle drawn around the text position

## Project Structure
```
├── autonomous_paint_agent.py  # Main agent implementation
├── paint_tools.py             # MCP server with Paint and email tools
├── .env                       # Environment variables
└── README.md                  # This documentation
```

## Notes
- The agent operates in autonomous mode, allowing the LLM to determine the execution order
- Email functionality requires proper Gmail credentials in the .env file 
