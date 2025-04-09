#!/usr/bin/env python
"""
Paint Agent - Uses LLM to control Microsoft Paint via MCP with autonomous execution order
"""
import os
import sys
import asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import traceback
from google import genai
import atexit
import signal

# Try to load .env from multiple possible locations
possible_env_paths = [
    ".env",  # Current directory
    "Assignment/.env",  # If run from Session4
]

env_loaded = False
for env_path in possible_env_paths:
    if os.path.exists(env_path):
        print(f"Found .env file at: {env_path}")
        load_dotenv(env_path)
        env_loaded = True
        break

if not env_loaded:
    print("Warning: Could not find .env file in any expected location")

# Access your API key and initialize Gemini client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment variables")
    print("Please create a .env file with GEMINI_API_KEY=your_api_key")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# Setup tracking for iterations
max_iterations = 10  # Increased to allow for more flexible execution
iteration = 0
iteration_response = []

async def generate_with_timeout(client, prompt, timeout=60):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except asyncio.TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

async def format_tools_for_prompt(tools):
    """Format tools information for the prompt"""
    if not tools:
        return "No tools available."
    
    tools_description = []
    for i, tool in enumerate(tools):
        try:
            # Get tool properties
            params = tool.inputSchema
            desc = getattr(tool, 'description', 'No description available')
            name = getattr(tool, 'name', f'tool_{i}')
            
            # Format the input schema in a more readable way
            if 'properties' in params:
                param_details = []
                for param_name, param_info in params['properties'].items():
                    param_type = param_info.get('type', 'unknown')
                    param_details.append(f"{param_name}: {param_type}")
                params_str = ', '.join(param_details)
            else:
                params_str = 'no parameters'

            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
            tools_description.append(tool_desc)
            print(f"Added description for tool: {tool_desc}")
        except Exception as e:
            print(f"Error processing tool {i}: {e}")
            tools_description.append(f"{i+1}. Error processing tool")
    
    return "\n".join(tools_description)

def cleanup_resources():
    """Clean up any remaining resources."""
    try:
        # Force flush any buffered output
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Clean up any subprocesses if needed
        import psutil
        current_process = psutil.Process()
        children = current_process.children(recursive=True)
        for child in children:
            try:
                child.terminate()
            except Exception as e:
                print(f"Error terminating child process: {e}")
    except Exception as e:
        print(f"Cleanup error: {e}")

# Register the cleanup function
atexit.register(cleanup_resources)

async def main():
    """Main function to run the Paint agent with Gemini."""
    global iteration, iteration_response
    server_process = None
    
    print("Starting Paint Agent execution...")
    
    try:
        # Find the paint_tools.py script path
        possible_paths = [
            "Session4/Assignment/paint_tools.py",
            "paint_tools.py",
            "./paint_tools.py",
            "Assignment/paint_tools.py",  # When running from Session4
            os.path.join(os.getcwd(), "Session4/Assignment/paint_tools.py"),
            os.path.join(os.getcwd(), "paint_tools.py"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "paint_tools.py"),  # Same dir as script
        ]
        
        path = None
        for p in possible_paths:
            if os.path.exists(p):
                path = p
                break
        
        if not path:
            print("Error: Could not find paint_tools.py")
            sys.exit(1)
        
        print(f"Found paint_tools.py at: {path}")
        
        # Create parameters for the server connection
        print("Starting MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=[path]
        )

        # Connect to MCP server
        print("Establishing connection to MCP server...")
        try:
            # Set a timeout for the server connection
            connection_timeout = 10  # seconds
            
            # Create a client connection with proper cleanup
            async with stdio_client(server_params) as (read, write):
                print("Connection established, creating session...")
                async with ClientSession(read, write) as session:
                    print("Session created, initializing...")
                    await session.initialize()
                    
                    # Get available tools
                    print("Requesting tool list...")
                    tools_result = await session.list_tools()
                    tools = tools_result.tools
                    print(f"Successfully retrieved {len(tools)} tools")

                    # Create system prompt with available tools
                    print("Creating system prompt...")
                    tools_description = await format_tools_for_prompt(tools)
                    
                    # Create a prompt that will guide the LLM to control Paint and send emails
                    system_prompt = f"""You are an agent that can control Microsoft Paint and send emails.

Available tools:
{tools_description}

Your task is to:
1. Calculate the ASCII exponential sum for a given string
2. Visualize the result in Microsoft Paint (draw a rectangle and add the text)
3. Save the visualization as an image
4. Email the image to a specified recipient

You must respond with EXACTLY ONE line in this format (no additional text):
FUNCTION_CALL: function_name|param1|param2|...

You must call only functions available to you.

IMPORTANT INSTRUCTIONS:
1. When drawing a rectangle, you MUST use coordinates that will surround the text. The text will be added at position (576, 324) in the canvas, which is the center of a 1152x648 pixel canvas.
2. Draw a rectangle that is centered around (576, 324) with enough space for the text. For example, use coordinates like (476, 274, 676, 374).
3. When adding text, it will be placed at (576, 324) in the canvas.
4. When sending an email with an attachment, you MUST use the EXACT SAME filename that was used in the save_paint_file function call.

Examples:
- FUNCTION_CALL: ascii_exp_sum|Hello World

IMPORTANT: When sending an email with an attachment, you MUST use the EXACT SAME filename that was used in the save_paint_file function call. Look at the previous steps to find this filename.

You can determine the order of operations yourself. Just respond with the next function call you want to make.
When you're done, respond with: FINAL_ANSWER: <summary of what was done>"""

                    # Get input string from the user
                    user_input = input("\nEnter a string to calculate its ASCII exponential sum: ")
                    if not user_input:
                        user_input = "Hello World"  # Default if user doesn't enter anything
                        print(f"Using default input: '{user_input}'")
                        
                    # Get recipient email from the user
                    recipient_email = input("\nEnter recipient email address for sending the visualization: ")
                    if not recipient_email:
                        recipient_email = os.getenv("GMAIL_ADDRESS", "")  # Default to own email if in .env
                        if recipient_email:
                            print(f"Using default recipient: {recipient_email}")
                        else:
                            print("No recipient email provided. Will skip email step.")

                    # Initial query
                    query = f"""Calculate the ASCII exponential sum for "{user_input}", visualize it in Paint, and email it to {recipient_email}."""

                    # Main interaction loop
                    while iteration < max_iterations:
                        print(f"\n=== Iteration {iteration + 1} ===")
                        
                        # Generate response
                        print("Generating LLM response...")
                        prompt = f"{system_prompt}\n\nQuery: {query}"
                        
                        try:
                            response = await generate_with_timeout(client, prompt)
                            response_text = response.text.strip()
                            print(f"LLM Response: {response_text}")
                            
                            if response_text.startswith("FUNCTION_CALL:"):
                                # Parse the function call
                                _, function_info = response_text.split(":", 1)
                                parts = [p.strip() for p in function_info.split("|")]
                                func_name, params = parts[0], parts[1:]
                                
                                # Prepare arguments based on the function
                                arguments = {}
                                
                                if func_name == "ascii_exp_sum":
                                    arguments = {"input_string": user_input}
                                elif func_name == "open_paint":
                                    pass  # No arguments needed
                                elif func_name == "draw_rectangle":
                                    if len(params) >= 4:
                                        arguments = {
                                            "x1": int(params[0]),
                                            "y1": int(params[1]),
                                            "x2": int(params[2]),
                                            "y2": int(params[3])
                                        }
                                elif func_name == "add_text_in_paint":
                                    if params:
                                        arguments = {"text": params[0]}
                                elif func_name == "save_paint_file":
                                    if params:
                                        arguments = {"filename": params[0]}
                                elif func_name == "email_ascii_image":
                                    if len(params) >= 3:
                                        arguments = {
                                            "to_address": recipient_email,  # Use the email provided by the user
                                            "subject": params[1],
                                            "body": params[2]
                                        }
                                    else:
                                        # If not enough parameters, use the recipient email
                                        arguments = {
                                            "to_address": recipient_email,
                                            "subject": "ASCII Calculation Result",
                                            "body": f"Here is the ASCII calculation result for '{user_input}'"
                                        }
                                elif func_name == "send_email_with_attachment":
                                    # Handle send_email_with_attachment function
                                    if len(params) >= 4:
                                        # Get the filename from the params
                                        filename = params[3]
                                        
                                        # Check if the file exists in the current directory
                                        if os.path.exists(filename):
                                            attachment_path = filename
                                        else:
                                            # Try to find the file in the Assignment directory
                                            assignment_path = os.path.join("Assignment", filename)
                                            if os.path.exists(assignment_path):
                                                attachment_path = assignment_path
                                            else:
                                                # Try to find the file in the Session4/Assignment directory
                                                session_path = os.path.join("Session4", "Assignment", filename)
                                                if os.path.exists(session_path):
                                                    attachment_path = session_path
                                                else:
                                                    # Use the absolute path
                                                    attachment_path = os.path.abspath(filename)
                                        
                                        print(f"Using attachment path: {attachment_path}")
                                        
                                        arguments = {
                                            "to_address": recipient_email,  # Use the email provided by the user
                                            "subject": params[1],
                                            "body": params[2],
                                            "attachment_path": attachment_path
                                        }
                                    else:
                                        # If not enough parameters, use defaults
                                        arguments = {
                                            "to_address": recipient_email,
                                            "subject": "ASCII Calculation Result",
                                            "body": f"Here is the ASCII calculation result for '{user_input}'",
                                            "attachment_path": "paint_visualization.png"  # Default path
                                        }
                                
                                print(f"Calling tool {func_name} with arguments: {arguments}")
                                
                                # Call the tool
                                result = await session.call_tool(func_name, arguments=arguments)
                                
                                # Process the result
                                if hasattr(result, 'content'):
                                    if isinstance(result.content, list):
                                        result_text = result.content[0].text
                                    else:
                                        result_text = str(result.content)
                                else:
                                    result_text = str(result)
                                
                                # Add the result to the conversation history
                                iteration_response.append(f"In iteration {iteration + 1}, {func_name} returned: {result_text}")
                                
                                # Update the query with the result
                                query = f"""Previous steps and results:
{chr(10).join(iteration_response)}

What should be the next step?"""
                                
                                print("Query: ",query)
                                
                                # Add delay between steps
                                await asyncio.sleep(1)
                                
                            elif response_text.startswith("FINAL_ANSWER:"):
                                print("\n=== Agent Execution Complete ===")
                                print(response_text)
                                break
                                
                            else:
                                print(f"Unexpected response format: {response_text}")
                                break
                                
                        except Exception as e:
                            print(f"Error in iteration {iteration + 1}: {e}")
                            break
                            
                        iteration += 1
                        
                    if iteration >= max_iterations:
                        print("\n=== Maximum iterations reached ===")
                        print("The agent has reached the maximum number of iterations.")
                        
        except Exception as e:
            print(f"Error in MCP server connection: {e}")
            traceback.print_exc()
            return
    except Exception as e:
        print(f"Error in main execution: {e}")
        traceback.print_exc()
    finally:
        # Explicitly flush stdout/stderr to prevent pipe errors
        sys.stdout.flush()
        sys.stderr.flush()
        await asyncio.sleep(0.5)  # Give a moment for pipes to clear

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExecution interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Ensure all resources are properly cleaned up
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Clean up any subprocesses
        try:
            import psutil
            current_process = psutil.Process()
            children = current_process.children(recursive=True)
            for child in children:
                try:
                    print(f"Terminating child process: {child.pid}")
                    child.terminate()
                except:
                    pass
        except Exception as e:
            print(f"Cleanup error: {e}") 