#!/usr/bin/env python3
"""
GUI Sandbox Server
This server provides an HTTP API to control the GUI in a sandboxed environment.
"""

import os
import time
import base64
import json
from io import BytesIO
from flask import Flask, request, jsonify
from flask_cors import CORS
import pyautogui
import pyscreenshot as ImageGrab
from PIL import Image

# Configure PyAutoGUI for safety
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5  # Add a short pause between PyAutoGUI commands

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Set the display environment variable if not set
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':1'

@app.route('/status', methods=['GET'])
def status():
    """Check if the server is running."""
    return jsonify({
        'status': 'ok',
        'message': 'GUI Sandbox server is running',
        'resolution': pyautogui.size()
    })

@app.route('/screenshot', methods=['GET'])
def take_screenshot():
    """Take a screenshot of the current screen and return it as base64."""
    try:
        # Take a screenshot
        img = ImageGrab.grab()
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return jsonify({
            'status': 'ok',
            'data': img_str,
            'format': 'base64',
            'mime_type': 'image/png'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/click', methods=['POST'])
def click():
    """Perform a mouse click at the specified coordinates."""
    try:
        data = request.json
        
        # Get coordinates
        x = data.get('x')
        y = data.get('y')
        
        if x is None or y is None:
            return jsonify({
                'status': 'error',
                'message': 'Missing x or y coordinates'
            }), 400
        
        # Get optional parameters
        button = data.get('button', 'left')  # 'left', 'right', or 'middle'
        clicks = data.get('clicks', 1)  # Number of clicks
        interval = data.get('interval', 0.0)  # Seconds between clicks
        
        # Perform the click
        pyautogui.click(x=x, y=y, button=button, clicks=clicks, interval=interval)
        
        return jsonify({
            'status': 'ok',
            'message': f'Clicked at ({x}, {y})'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/doubleclick', methods=['POST'])
def doubleclick():
    """Perform a double-click at the specified coordinates."""
    try:
        data = request.json
        
        # Get coordinates
        x = data.get('x')
        y = data.get('y')
        
        if x is None or y is None:
            return jsonify({
                'status': 'error',
                'message': 'Missing x or y coordinates'
            }), 400
        
        # Perform double-click
        pyautogui.doubleClick(x=x, y=y)
        
        return jsonify({
            'status': 'ok',
            'message': f'Double-clicked at ({x}, {y})'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/rightclick', methods=['POST'])
def rightclick():
    """Perform a right-click at the specified coordinates."""
    try:
        data = request.json
        
        # Get coordinates
        x = data.get('x')
        y = data.get('y')
        
        if x is None or y is None:
            return jsonify({
                'status': 'error',
                'message': 'Missing x or y coordinates'
            }), 400
        
        # Perform right-click
        pyautogui.rightClick(x=x, y=y)
        
        return jsonify({
            'status': 'ok',
            'message': f'Right-clicked at ({x}, {y})'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/moveto', methods=['POST'])
def moveto():
    """Move the mouse to the specified coordinates."""
    try:
        data = request.json
        
        # Get coordinates
        x = data.get('x')
        y = data.get('y')
        
        if x is None or y is None:
            return jsonify({
                'status': 'error',
                'message': 'Missing x or y coordinates'
            }), 400
        
        # Get optional parameters
        duration = data.get('duration', 0.0)  # Duration of movement
        
        # Move the mouse
        pyautogui.moveTo(x=x, y=y, duration=duration)
        
        return jsonify({
            'status': 'ok',
            'message': f'Moved to ({x}, {y})'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/drag', methods=['POST'])
def drag():
    """Drag the mouse from current position to the specified coordinates."""
    try:
        data = request.json
        
        # Get coordinates
        x = data.get('x')
        y = data.get('y')
        
        if x is None or y is None:
            return jsonify({
                'status': 'error',
                'message': 'Missing x or y coordinates'
            }), 400
        
        # Get optional parameters
        button = data.get('button', 'left')  # 'left', 'right', or 'middle'
        duration = data.get('duration', 0.5)  # Duration of drag
        
        # Drag the mouse
        pyautogui.drag(x=x, y=y, button=button, duration=duration)
        
        return jsonify({
            'status': 'ok',
            'message': f'Dragged to ({x}, {y})'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/type', methods=['POST'])
def type_text():
    """Type the specified text."""
    try:
        data = request.json
        
        # Get text to type
        text = data.get('text')
        
        if text is None:
            return jsonify({
                'status': 'error',
                'message': 'Missing text parameter'
            }), 400
        
        # Get optional parameters
        interval = data.get('interval', 0.0)  # Seconds between keypresses
        
        # Type the text
        pyautogui.typewrite(text, interval=interval)
        
        return jsonify({
            'status': 'ok',
            'message': f'Typed text: {text}'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/press', methods=['POST'])
def press_key():
    """Press the specified key or key combination."""
    try:
        data = request.json
        
        # Get key(s) to press
        keys = data.get('keys')
        
        if keys is None:
            return jsonify({
                'status': 'error',
                'message': 'Missing keys parameter'
            }), 400
        
        # Handle different types of input
        if isinstance(keys, list):
            # Press key combination
            pyautogui.hotkey(*keys)
            message = f'Pressed key combination: {"+".join(keys)}'
        else:
            # Press single key
            pyautogui.press(keys)
            message = f'Pressed key: {keys}'
        
        return jsonify({
            'status': 'ok',
            'message': message
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/hotkey', methods=['POST'])
def hotkey():
    """Press a combination of keys."""
    try:
        data = request.json
        
        # Get keys to press
        keys = data.get('keys')
        
        if not keys or not isinstance(keys, list):
            return jsonify({
                'status': 'error',
                'message': 'Keys must be a non-empty list'
            }), 400
        
        # Press the key combination
        pyautogui.hotkey(*keys)
        
        return jsonify({
            'status': 'ok',
            'message': f'Pressed hotkey: {"+".join(keys)}'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/scroll', methods=['POST'])
def scroll():
    """Scroll the mouse wheel."""
    try:
        data = request.json
        
        # Get scroll amount
        clicks = data.get('clicks')
        
        if clicks is None:
            return jsonify({
                'status': 'error',
                'message': 'Missing clicks parameter'
            }), 400
        
        # Scroll up (positive) or down (negative)
        pyautogui.scroll(clicks)
        
        direction = 'up' if clicks > 0 else 'down'
        return jsonify({
            'status': 'ok',
            'message': f'Scrolled {direction} by {abs(clicks)} clicks'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/find_image', methods=['POST'])
def find_image():
    """Find an image on the screen."""
    try:
        data = request.json
        
        # Get base64 encoded image
        image_b64 = data.get('image')
        
        if not image_b64:
            return jsonify({
                'status': 'error',
                'message': 'Missing image parameter'
            }), 400
        
        # Decode image
        image_data = base64.b64decode(image_b64)
        image = Image.open(BytesIO(image_data))
        
        # Optional parameters
        confidence = data.get('confidence', 0.9)  # Default confidence level
        
        # Look for the image on screen
        location = pyautogui.locateOnScreen(image, confidence=confidence)
        
        if location:
            return jsonify({
                'status': 'ok',
                'found': True,
                'location': {
                    'left': location.left,
                    'top': location.top,
                    'width': location.width,
                    'height': location.height,
                    'center_x': location.left + location.width // 2,
                    'center_y': location.top + location.height // 2
                }
            })
        else:
            return jsonify({
                'status': 'ok',
                'found': False,
                'message': 'Image not found on screen'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/launch_application', methods=['POST'])
def launch_application():
    """Launch an application."""
    try:
        data = request.json
        
        # Get application command
        command = data.get('command')
        
        if not command:
            return jsonify({
                'status': 'error',
                'message': 'Missing command parameter'
            }), 400
        
        # Limit the allowed applications for security
        allowed_apps = ['firefox', 'xfce4-terminal', 'mousepad', 'thunar']
        app_name = command.split()[0]
        
        if app_name not in allowed_apps:
            return jsonify({
                'status': 'error',
                'message': f'Application not allowed. Allowed apps: {", ".join(allowed_apps)}'
            }), 403
        
        # Launch the application
        os.system(f"{command} &")
        
        return jsonify({
            'status': 'ok',
            'message': f'Launched application: {command}'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Wait for X server to start
    time.sleep(2)
    print("Starting GUI Sandbox Server...")
    print(f"Screen resolution: {pyautogui.size()}")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
