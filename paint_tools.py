#!/usr/bin/env python
# paint_tools.py - Combined Paint and Gmail tools using MCP 
import os
import sys
import time
import platform
import traceback
import logging
import math
import base64
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to load .env from multiple possible locations
possible_env_paths = [
    ".env",  # Current directory
    "Assignment/.env",  # If run from Session4
    "../.env",  # One directory up
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),  # Same dir as script
]

env_loaded = False
for env_path in possible_env_paths:
    if os.path.exists(env_path):
        logger.info(f"Found .env file at: {env_path}")
        load_dotenv(env_path)
        env_loaded = True
        break

if not env_loaded:
    logger.warning("Could not find .env file in any expected location")

# Check for Gmail environment variables
gmail_address = os.getenv("GMAIL_ADDRESS")
gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")

if not gmail_address or not gmail_app_password:
    logger.warning("Missing Gmail credentials in environment variables")
    logger.warning("Email functionality will not be available")
    logger.warning("Create a .env file with GMAIL_ADDRESS and GMAIL_APP_PASSWORD")
    HAS_GMAIL_CREDENTIALS = False
else:
    HAS_GMAIL_CREDENTIALS = True
    logger.info(f"Gmail credentials found for: {gmail_address}")

# Check if we're running on Windows
if platform.system() != "Windows":
    logger.error("This script requires Windows to run MS Paint.")
    HAS_WINDOWS = False
else:
    HAS_WINDOWS = True

# Try to import Windows-specific modules
try:
    from pywinauto.application import Application
    import win32gui
    import win32con
    from win32api import GetSystemMetrics
except ImportError as e:
    logger.error(f"Failed to import Windows modules: {e}")
    logger.error("Will use simulated mode instead (no actual paint operations)")
    HAS_WINDOWS_MODULES = False
else:
    HAS_WINDOWS_MODULES = True

# Import MCP modules
try:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import TextContent
    from mcp import types
    logger.info("MCP modules imported successfully")
except ImportError as e:
    logger.error(f"Failed to import MCP modules: {e}")
    logger.error("Make sure MCP is installed (pip install mcp)")
    sys.exit(1)

# Paint tools implementation
class PaintTools:
    def __init__(self):
        self.paint_app = None
        self.simulation_mode = not HAS_WINDOWS_MODULES
        logger.info(f"Paint tools initialized (simulation mode: {self.simulation_mode})")
        
    def open_paint(self):
        """Open Microsoft Paint maximized on primary monitor"""
        try:
            logger.info("Attempting to open Paint")
            
            if self.simulation_mode:
                logger.info("SIMULATION: Opening Paint")
                time.sleep(1)
                return "SIMULATION: Paint opened successfully"
                
            self.paint_app = Application().start('mspaint.exe')
            time.sleep(1.0)  # Give Paint more time to start
            
            # Get the Paint window
            paint_window = self.paint_app.window(class_name='MSPaintApp')
            
            # Maximize the window
            win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
            time.sleep(1.0)  # Give more time for the window to maximize
            
            logger.info("Paint opened successfully")
            return "Paint opened successfully and maximized"
        except Exception as e:
            error_msg = f"Error opening Paint: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return error_msg
    
    def draw_rectangle(self, x1, y1, x2, y2):
        """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
        try:
            if self.simulation_mode:
                logger.info(f"SIMULATION: Drawing rectangle from ({x1},{y1}) to ({x2},{y2})")
                time.sleep(1)
                return f"SIMULATION: Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
                
            if not self.paint_app:
                logger.warning("Paint not open, need to call open_paint first")
                return "Paint is not open. Please call open_paint first."
            
            logger.info(f"Drawing rectangle from ({x1},{y1}) to ({x2},{y2})")
            
            # Get Paint window and make sure it's active
            paint_window = self.paint_app.window(class_name='MSPaintApp')
            paint_window.set_focus()
            time.sleep(1.0)
            logger.info("Paint window focused")
            
            # Click at position 512,82 for rectangle tool
            paint_window.click_input(coords=(512, 82))
            time.sleep(2.0)  # Wait longer for tool selection
            logger.info("Clicked at (512,82) for rectangle tool")
            
            # Get canvas area
            canvas = paint_window.child_window(class_name='MSPaintView')
            
            # Force click in center of canvas to ensure focus
            canvas.click_input(coords=(400, 300))
            time.sleep(1.0)
            logger.info("Clicked to ensure canvas focus")
            
            # Get actual canvas position and dimensions
            canvas_rect = canvas.rectangle()
            canvas_left = canvas_rect.left
            canvas_top = canvas_rect.top
            
            # Calculate absolute mouse positions relative to screen
            abs_x1 = canvas_left + x1
            abs_y1 = canvas_top + y1
            abs_x2 = canvas_left + x2
            abs_y2 = canvas_top + y2
            
            logger.info(f"Absolute positions: ({abs_x1},{abs_y1}) to ({abs_x2},{abs_y2})")
            
            # Draw with absolute coordinates using win32api
            import win32api
            import win32con
            
            # Position mouse at start
            logger.info(f"Moving mouse to start position ({abs_x1},{abs_y1})")
            win32api.SetCursorPos((abs_x1, abs_y1))
            time.sleep(1.0)
            
            # Press mouse button
            logger.info("Pressing mouse button")
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(1.0)
            
            # Move to end position
            logger.info(f"Moving mouse to end position ({abs_x2},{abs_y2})")
            win32api.SetCursorPos((abs_x2, abs_y2))
            time.sleep(1.0)
            
            # Release mouse button
            logger.info("Releasing mouse button")
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(1.0)
            
            # Store rectangle coordinates for future reference
            self.last_rect = {
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2
            }
            logger.info("Rectangle drawn successfully and coordinates stored")
            
            return f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
        except Exception as e:
            error_msg = f"Error drawing rectangle: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return error_msg
            
    def save_paint(self, filename):
        """Save the current Paint file"""
        try:
            if self.simulation_mode:
                logger.info(f"SIMULATION: Saving Paint file as {filename}")
                return f"SIMULATION: File saved as {filename}"
                
            if not self.paint_app:
                logger.warning("Paint not open, need to call open_paint first")
                return "Paint is not open. Please call open_paint first."
            
            # Create full path in Assignment directory
            assignment_path = os.path.dirname(os.path.abspath(__file__))  # Get current script dir
            full_path = os.path.join(assignment_path, filename)
            
            logger.info(f"Saving Paint file to: {full_path}")
            
            # Using SendKeys approach
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            
            # Get Paint window and activate it
            paint_window = self.paint_app.window(class_name='MSPaintApp')
            paint_window.set_focus()
            time.sleep(1.0)
            
            # Press Ctrl+S to open save dialog
            shell.SendKeys("^s")
            time.sleep(2.0)  # Wait for dialog to appear
            
            # Enter the full path with filename
            shell.SendKeys(full_path)
            time.sleep(1.0)
            
            # Press Enter to save
            shell.SendKeys("{ENTER}")
            time.sleep(2.0)
            
            # Handle possible overwrite confirmation
            shell.SendKeys("{ENTER}")
            time.sleep(1.0)
            
            logger.info(f"File saved to: {full_path}")
            return f"File saved to Assignment directory as: {filename}"
        except Exception as e:
            error_msg = f"Error saving file: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return error_msg
    
    def add_text_in_paint(self, text):
        """Add text in Paint"""
        try:
            if self.simulation_mode:
                logger.info(f"SIMULATION: Adding text: '{text}'")
                time.sleep(1)
                return f"SIMULATION: Text '{text}' added to Paint"
                
            if not self.paint_app:
                logger.warning("Paint not open, need to call open_paint first")
                return "Paint is not open. Please call open_paint first."
            
            logger.info(f"Adding text: '{text}'")
            
            # Get Paint window and ensure it's focused
            paint_window = self.paint_app.window(class_name='MSPaintApp')
            paint_window.set_focus()
            time.sleep(1.0)
            logger.info("Paint window focused")
            
            # Get canvas first
            canvas = paint_window.child_window(class_name='MSPaintView')
            canvas_rect = canvas.rectangle()
            
            # IMPORTANT: Activate select tool first to reset state
            logger.info("Activating select tool first to reset state")
            paint_window.click_input(coords=(350, 82))  # Position for select tool
            time.sleep(1.0)
            
            # Click at top-left (0,0) of canvas to ensure selection is cleared
            logger.info("Clicking at (0,0) to clear any selections")
            import win32api
            import win32con
            win32api.SetCursorPos((canvas_rect.left, canvas_rect.top))
            time.sleep(0.5)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.2)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(1.0)
            
            # Now click directly on the Text button - try multiple positions
            logger.info("Clicking directly on Text button")
            text_button_positions = [(724, 82), (736, 82), (750, 82), (763, 82)]
            
            for pos in text_button_positions:
                logger.info(f"Trying Text button at position {pos}")
                paint_window.click_input(coords=pos)
                time.sleep(1.0)
            
            # Calculate center of rectangle if we have stored rectangle coordinates
            if hasattr(self, 'last_rect') and self.last_rect:
                # Use the center of the last drawn rectangle (shifted 50px to the left)
                center_x = canvas_rect.left + (self.last_rect['x1'] + self.last_rect['x2']) // 2 - 50
                center_y = canvas_rect.top + (self.last_rect['y1'] + self.last_rect['y2']) // 2
                logger.info(f"Using last rectangle center for text (shifted 50px left): ({center_x}, {center_y})")
            else:
                # Use fixed position in center of canvas (shifted 50px to the left)
                center_x = canvas_rect.left + 450  # 500 - 50
                center_y = canvas_rect.top + 275
                logger.info(f"Using fixed center point for text (shifted 50px left): ({center_x}, {center_y})")
            
            # Create a smaller text box by dragging
            logger.info(f"Creating smaller text area at ({center_x-50}, {center_y-25})")
            win32api.SetCursorPos((center_x-50, center_y-25))
            time.sleep(0.5)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.5)
            
            # Drag to create text box (smaller area)
            logger.info(f"Dragging to ({center_x+50}, {center_y+25})")
            win32api.SetCursorPos((center_x+50, center_y+25))
            time.sleep(0.5)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(2.0)
            
            # Alternative approach: Click inside the text box first
            logger.info("Clicking inside the text box")
            win32api.SetCursorPos((center_x, center_y))
            time.sleep(0.5)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.2)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(1.0)
            
            # Try both methods for text input
            # Method 1: Using pywinauto's type_keys
            try:
                logger.info(f"Typing text with type_keys: '{text}'")
                paint_window.type_keys(text, with_spaces=True)
                time.sleep(1.0)
            except Exception as e:
                logger.warning(f"Error with type_keys: {e}, trying SendKeys instead")
                # Method 2: Using SendKeys
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                logger.info(f"Typing text with SendKeys: '{text}'")
                shell.SendKeys(text)
                time.sleep(1.0)
            
            # Click elsewhere to finalize
            logger.info("Clicking elsewhere to finalize text")
            win32api.SetCursorPos((canvas_rect.left + 50, canvas_rect.top + 50))
            time.sleep(0.5)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.5)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(1.0)
            
            logger.info("Text added successfully")
            return f"Text '{text}' added to Paint"
        except Exception as e:
            error_msg = f"Error adding text: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return error_msg

    def calculate_ascii_exp_sum(self, input_string):
        """Calculate the sum of exponentials of ASCII values of a string"""
        try:
            if not input_string:
                return "Input string is empty"
                
            logger.info(f"Calculating ASCII exponential sum for: '{input_string}'")
            
            # Calculate ASCII values and their exponentials
            ascii_values = [ord(char) for char in input_string]
            exp_values = [math.exp(val) for val in ascii_values]
            total_sum = sum(exp_values)
            
            # Format the details for logging and return
            ascii_details = ", ".join([f"{char}={ord(char)}→e^{ord(char)}={math.exp(ord(char)):.2e}" for char in input_string])
            
            logger.info(f"ASCII values: {ascii_values}")
            logger.info(f"Exponential values: {[f'{val:.2e}' for val in exp_values]}")
            logger.info(f"Sum of exponentials: {total_sum:.6e}")
            
            result = f"Sum of exponentials of ASCII values for '{input_string}': {total_sum:.6e}\n"
            result += f"Details: {ascii_details}"
            
            return result
        except Exception as e:
            error_msg = f"Error calculating ASCII exponential sum: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return error_msg

# Gmail tools implementation
class GmailTools:
    def __init__(self):
        self.gmail_address = gmail_address
        self.gmail_app_password = gmail_app_password
        self.simulation_mode = not HAS_GMAIL_CREDENTIALS
        logger.info(f"Gmail tools initialized (simulation mode: {self.simulation_mode})")
        
    def send_email(self, to_address, subject, body, attachment_path=None):
        """Send an email with optional attachment"""
        try:
            if self.simulation_mode:
                logger.info(f"SIMULATION: Sending email to {to_address} with subject: {subject}")
                if attachment_path:
                    logger.info(f"SIMULATION: Would attach: {attachment_path}")
                return f"SIMULATION: Email sent to {to_address} with subject: {subject}"
            
            import smtplib
            
            # Create multipart message
            message = MIMEMultipart()
            message["From"] = self.gmail_address
            message["To"] = to_address
            message["Subject"] = subject
            
            # Add body text
            message.attach(MIMEText(body, "plain"))
            
            # Add attachment if provided
            if attachment_path:
                if not os.path.exists(attachment_path):
                    error_msg = f"Attachment file not found: {attachment_path}"
                    logger.error(error_msg)
                    return error_msg
                    
                logger.info(f"Adding attachment: {attachment_path}")
                
                # Determine the MIME type
                content_type, encoding = mimetypes.guess_type(attachment_path)
                if content_type is None or encoding is not None:
                    content_type = 'application/octet-stream'
                main_type, sub_type = content_type.split('/', 1)
                
                try:
                    with open(attachment_path, 'rb') as file:
                        attachment_data = file.read()
                except Exception as e:
                    error_msg = f"Error reading attachment file: {str(e)}"
                    logger.error(error_msg)
                    return error_msg
                
                if main_type == 'text':
                    attachment = MIMEText(attachment_data.decode('utf-8'), _subtype=sub_type)
                elif main_type == 'image':
                    attachment = MIMEImage(attachment_data, _subtype=sub_type)
                else:
                    attachment = MIMEApplication(attachment_data, _subtype=sub_type)
                
                # Add filename header
                attachment.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(attachment_path)}",
                )
                message.attach(attachment)
                logger.info(f"Successfully attached file: {os.path.basename(attachment_path)}")
            
            # Connect to Gmail SMTP server
            logger.info("Connecting to Gmail SMTP server...")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.gmail_address, self.gmail_app_password)
                server.send_message(message)
                logger.info(f"Email sent successfully to {to_address}")
            
            result_text = f"Email sent to {to_address} with subject: {subject}"
            if attachment_path:
                result_text += f" and attachment: {os.path.basename(attachment_path)}"
            return result_text
            
        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return error_msg
            
    def check_file_exists(self, file_path):
        """Check if a file exists and return details about it"""
        try:
            # Create full path if not already absolute
            if not os.path.isabs(file_path):
                base_path = os.path.dirname(os.path.abspath(__file__))
                full_path = os.path.join(base_path, file_path)
            else:
                full_path = file_path
                
            if os.path.exists(full_path):
                file_size = os.path.getsize(full_path)
                file_info = f"File exists: {full_path}\nSize: {file_size} bytes"
                logger.info(file_info)
                return file_info
            else:
                error_msg = f"File does not exist: {full_path}"
                logger.warning(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"Error checking file: {str(e)}"
            logger.error(error_msg)
            return error_msg
            
    def email_image(self, to_address, subject, body, image_filename="ascii_result.png"):
        """Send an email with the ASCII image attachment"""
        try:
            # Get the absolute path of the image file
            assignment_path = os.path.dirname(os.path.abspath(__file__))
            full_image_path = os.path.join(assignment_path, image_filename)
            
            # First check if the image file exists
            if not os.path.exists(full_image_path):
                error_msg = f"Cannot send image email. File not found: {full_image_path}"
                logger.error(error_msg)
                return error_msg
                
            # Now send the email with the image
            logger.info(f"Sending image email to {to_address} with subject: {subject}")
            logger.info(f"Attaching file: {full_image_path}")
            result = self.send_email(to_address, subject, body, full_image_path)
            return result
            
        except Exception as e:
            error_msg = f"Error sending image email: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return error_msg

# Create MCP Server
mcp = FastMCP("PaintAndMailTools")
paint_tools = PaintTools()
gmail_tools = GmailTools()

# Register Paint tools
@mcp.tool()
async def open_paint() -> dict:
    """Opens Microsoft Paint application on the primary monitor and maximizes the window"""
    result = paint_tools.open_paint()
    return {
        "content": [
            TextContent(
                type="text",
                text=result
            )
        ]
    }

@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Draws a rectangle in Paint from (x1,y1) to (x2,y2)"""
    result = paint_tools.draw_rectangle(x1, y1, x2, y2)
    return {
        "content": [
            TextContent(
                type="text",
                text=result
            )
        ]
    }

@mcp.tool()
async def add_text_in_paint(text: str) -> dict:
    """Adds text to Paint canvas"""
    result = paint_tools.add_text_in_paint(text)
    return {
        "content": [
            TextContent(
                type="text",
                text=result
            )
        ]
    }

@mcp.tool()
async def save_paint_file(filename: str) -> dict:
    """Saves the current Paint file with the given filename"""
    result = paint_tools.save_paint(filename)
    return {
        "content": [
            TextContent(
                type="text",
                text=result
            )
        ]
    }

@mcp.tool()
async def ascii_exp_sum(input_string: str) -> dict:
    """Converts each character in string to ASCII, calculates e^(ASCII) for each, and returns the sum"""
    result = paint_tools.calculate_ascii_exp_sum(input_string)
    return {
        "content": [
            TextContent(
                type="text",
                text=result
            )
        ]
    }

# # Register Gmail tools
# @mcp.tool()
# async def send_email(to_address: str, subject: str, body: str) -> dict:
#     """Sends an email without attachment"""
#     result = gmail_tools.send_email(to_address, subject, body)
#     return {
#         "content": [
#             TextContent(
#                 type="text",
#                 text=result
#             )
#         ]
#     }

@mcp.tool()
async def send_email_with_attachment(to_address: str, subject: str, body: str, attachment_path: str) -> dict:
    """Sends an email with an attachment"""
    result = gmail_tools.send_email(to_address, subject, body, attachment_path)
    return {
        "content": [
            TextContent(
                type="text",
                text=result
            )
        ]
    }

@mcp.tool()
async def check_file_exists(file_path: str) -> dict:
    """Checks if a file exists and returns details about it"""
    result = gmail_tools.check_file_exists(file_path)
    return {
        "content": [
            TextContent(
                type="text",
                text=result
            )
        ]
    }

# @mcp.tool()
# async def email_ascii_image(to_address: str, subject: str = "ASCII Visualization", body: str = "") -> dict:
#     """Sends the ASCII visualization image via email"""
#     # Create default body if not provided
#     if not body:
#         body = "Please find attached the ASCII exponential sum visualization created with Paint."
    
#     result = gmail_tools.email_image(to_address, subject, body)
#     return {
#         "content": [
#             TextContent(
#                 type="text",
#                 text=result
#             )
#         ]
#     }

if __name__ == "__main__":
    try:
        logger.info("Starting Paint and Gmail Tools MCP server")
        
        # Print a message that the client can detect
        print("PAINT_TOOLS_SERVER_READY", flush=True)
        
        # Run the MCP server
        if len(sys.argv) > 1 and sys.argv[1] == "dev":
            logger.info("Running in dev mode")
            mcp.run()  # Run without transport for dev server
        else:
            logger.info("Running with stdio transport")
            mcp.run(transport="stdio")
            
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1) 