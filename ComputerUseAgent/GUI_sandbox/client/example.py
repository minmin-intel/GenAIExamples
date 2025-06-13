#!/usr/bin/env python3
"""
Example script demonstrating how to use the GUI Sandbox client library.
This script launches Firefox, navigates to a website, and takes a screenshot.
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.client import GUISandboxClient

def main():
    # Create client instance
    client = GUISandboxClient("http://localhost:5000")
    
    try:
        # Check if server is running
        status = client.check_status()
        print("Server status:", status)
        
        # Launch Firefox
        print("Launching Firefox...")
        result = client.launch_application("firefox")
        print(result)
        
        # Wait for Firefox to load
        time.sleep(5)
        
        # Take a screenshot
        print("Taking screenshot...")
        client.take_screenshot("firefox_start.png")
        
        # Click in the address bar (assuming Firefox is in focus)
        print("Clicking address bar...")
        client.click(640, 60)  # Adjust coordinates as needed for your screen
        
        # Type a URL
        print("Typing URL...")
        client.type_text("https://www.example.com")
        
        # Press Enter
        print("Pressing Enter...")
        client.press_key("enter")
        
        # Wait for page to load
        time.sleep(3)
        
        # Take another screenshot
        print("Taking screenshot of loaded page...")
        client.take_screenshot("example_website.png")
        
        # Scroll down
        print("Scrolling down...")
        client.scroll(-10)  # Negative value to scroll down
        
        # Wait a moment
        time.sleep(1)
        
        # Take final screenshot
        print("Taking final screenshot...")
        client.take_screenshot("scrolled_page.png")
        
        print("Example completed successfully!")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
