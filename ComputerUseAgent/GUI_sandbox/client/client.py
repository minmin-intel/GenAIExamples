#!/usr/bin/env python3
"""
GUI Sandbox Client
This client provides a command-line interface to interact with the GUI Sandbox server.
"""

import os
import sys
import json
import base64
import argparse
import requests
from PIL import Image
from io import BytesIO

class GUISandboxClient:
    """Client for interacting with the GUI Sandbox server."""
    
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
    
    def check_status(self):
        """Check if the server is running."""
        response = requests.get(f"{self.server_url}/status")
        return response.json()
    
    def take_screenshot(self, save_path=None):
        """Take a screenshot and optionally save it to a file."""
        response = requests.get(f"{self.server_url}/screenshot")
        data = response.json()
        
        if data['status'] == 'ok':
            # Decode the base64 image
            img_data = base64.b64decode(data['data'])
            img = Image.open(BytesIO(img_data))
            
            # Save to file if requested
            if save_path:
                img.save(save_path)
                print(f"Screenshot saved to {save_path}")
            
            return img
        else:
            print(f"Error: {data.get('message', 'Unknown error')}")
            return None
    
    def click(self, x, y, button='left', clicks=1, interval=0.0):
        """Perform a mouse click at the specified coordinates."""
        data = {
            'x': x,
            'y': y,
            'button': button,
            'clicks': clicks,
            'interval': interval
        }
        response = requests.post(f"{self.server_url}/click", json=data)
        return response.json()
    
    def double_click(self, x, y):
        """Perform a double-click at the specified coordinates."""
        data = {'x': x, 'y': y}
        response = requests.post(f"{self.server_url}/doubleclick", json=data)
        return response.json()
    
    def right_click(self, x, y):
        """Perform a right-click at the specified coordinates."""
        data = {'x': x, 'y': y}
        response = requests.post(f"{self.server_url}/rightclick", json=data)
        return response.json()
    
    def move_to(self, x, y, duration=0.0):
        """Move the mouse to the specified coordinates."""
        data = {
            'x': x,
            'y': y,
            'duration': duration
        }
        response = requests.post(f"{self.server_url}/moveto", json=data)
        return response.json()
    
    def drag(self, x, y, button='left', duration=0.5):
        """Drag the mouse from current position to the specified coordinates."""
        data = {
            'x': x,
            'y': y,
            'button': button,
            'duration': duration
        }
        response = requests.post(f"{self.server_url}/drag", json=data)
        return response.json()
    
    def type_text(self, text, interval=0.0):
        """Type the specified text."""
        data = {
            'text': text,
            'interval': interval
        }
        response = requests.post(f"{self.server_url}/type", json=data)
        return response.json()
    
    def press_key(self, keys):
        """Press the specified key or key combination."""
        data = {'keys': keys}
        response = requests.post(f"{self.server_url}/press", json=data)
        return response.json()
    
    def hotkey(self, *keys):
        """Press a combination of keys."""
        data = {'keys': list(keys)}
        response = requests.post(f"{self.server_url}/hotkey", json=data)
        return response.json()
    
    def scroll(self, clicks):
        """Scroll the mouse wheel."""
        data = {'clicks': clicks}
        response = requests.post(f"{self.server_url}/scroll", json=data)
        return response.json()
    
    def find_image(self, image_path, confidence=0.9):
        """Find an image on the screen."""
        # Read and encode the image
        with open(image_path, 'rb') as f:
            image_data = f.read()
            image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        data = {
            'image': image_b64,
            'confidence': confidence
        }
        
        response = requests.post(f"{self.server_url}/find_image", json=data)
        return response.json()
    
    def launch_application(self, command):
        """Launch an application."""
        data = {'command': command}
        response = requests.post(f"{self.server_url}/launch_application", json=data)
        return response.json()

def main():
    """Command-line interface for the GUI Sandbox client."""
    parser = argparse.ArgumentParser(description='GUI Sandbox Client')
    parser.add_argument('--server', default='http://localhost:5000', help='Server URL')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check server status')
    
    # Screenshot command
    screenshot_parser = subparsers.add_parser('screenshot', help='Take a screenshot')
    screenshot_parser.add_argument('--save', help='Save screenshot to file')
    
    # Click command
    click_parser = subparsers.add_parser('click', help='Perform a mouse click')
    click_parser.add_argument('x', type=int, help='X coordinate')
    click_parser.add_argument('y', type=int, help='Y coordinate')
    click_parser.add_argument('--button', default='left', choices=['left', 'right', 'middle'], help='Mouse button')
    click_parser.add_argument('--clicks', type=int, default=1, help='Number of clicks')
    
    # Double-click command
    dclick_parser = subparsers.add_parser('doubleclick', help='Perform a double-click')
    dclick_parser.add_argument('x', type=int, help='X coordinate')
    dclick_parser.add_argument('y', type=int, help='Y coordinate')
    
    # Right-click command
    rclick_parser = subparsers.add_parser('rightclick', help='Perform a right-click')
    rclick_parser.add_argument('x', type=int, help='X coordinate')
    rclick_parser.add_argument('y', type=int, help='Y coordinate')
    
    # Move command
    move_parser = subparsers.add_parser('move', help='Move the mouse')
    move_parser.add_argument('x', type=int, help='X coordinate')
    move_parser.add_argument('y', type=int, help='Y coordinate')
    move_parser.add_argument('--duration', type=float, default=0.0, help='Movement duration')
    
    # Type command
    type_parser = subparsers.add_parser('type', help='Type text')
    type_parser.add_argument('text', help='Text to type')
    type_parser.add_argument('--interval', type=float, default=0.0, help='Interval between keypresses')
    
    # Press command
    press_parser = subparsers.add_parser('press', help='Press a key')
    press_parser.add_argument('key', help='Key to press')
    
    # Hotkey command
    hotkey_parser = subparsers.add_parser('hotkey', help='Press a key combination')
    hotkey_parser.add_argument('keys', nargs='+', help='Keys to press')
    
    # Scroll command
    scroll_parser = subparsers.add_parser('scroll', help='Scroll the mouse wheel')
    scroll_parser.add_argument('clicks', type=int, help='Number of clicks to scroll')
    
    # Find image command
    find_parser = subparsers.add_parser('find', help='Find an image on screen')
    find_parser.add_argument('image', help='Path to image file')
    find_parser.add_argument('--confidence', type=float, default=0.9, help='Confidence level (0-1)')
    
    # Launch application command
    launch_parser = subparsers.add_parser('launch', help='Launch an application')
    launch_parser.add_argument('command', help='Command to launch')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    client = GUISandboxClient(args.server)
    
    try:
        if args.command == 'status':
            result = client.check_status()
            print(json.dumps(result, indent=2))
        
        elif args.command == 'screenshot':
            img = client.take_screenshot(args.save)
            if img and not args.save:
                img.show()
        
        elif args.command == 'click':
            result = client.click(args.x, args.y, args.button, args.clicks)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'doubleclick':
            result = client.double_click(args.x, args.y)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'rightclick':
            result = client.right_click(args.x, args.y)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'move':
            result = client.move_to(args.x, args.y, args.duration)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'type':
            result = client.type_text(args.text, args.interval)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'press':
            result = client.press_key(args.key)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'hotkey':
            result = client.hotkey(*args.keys)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'scroll':
            result = client.scroll(args.clicks)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'find':
            result = client.find_image(args.image, args.confidence)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'launch':
            result = client.launch_application(args.command)
            print(json.dumps(result, indent=2))
    
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
