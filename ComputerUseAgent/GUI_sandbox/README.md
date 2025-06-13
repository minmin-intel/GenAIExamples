# GUI Sandbox Environment

This project provides a sandboxed desktop UI environment with a server that can be controlled via HTTP requests and a client that can send these requests.

## Features

- Containerized GUI environment using Docker
- HTTP API for GUI automation operations
- Python client library for easy integration
- Command-line client tool
- Support for various GUI operations:
  - Mouse clicks (left, right, double)
  - Mouse movement and dragging
  - Keyboard input
  - Image recognition
  - Screenshots
  - Application launch

## Getting Started

### Prerequisites

- Docker
- Python 3.6 or higher (for client)

### Setting up the Server

1. Build the Docker image:

```bash
cd GUI_sandbox
docker build -t gui-sandbox .
```

2. Run the Docker container:

```bash
docker run -p 5000:5000 -p 5900:5900 --name gui-sandbox-container gui-sandbox
```

The server will be accessible at http://localhost:5000.

For debugging purposes, you can connect to the VNC server running on port 5900 using any VNC client.

### Using the Client

1. Install the client requirements:

```bash
cd GUI_sandbox/client
pip install -r requirements.txt
```

2. Check if the server is running:

```bash
python client.py status
```

3. Take a screenshot:

```bash
python client.py screenshot --save screenshot.png
```

4. Perform a mouse click:

```bash
python client.py click 100 200
```

5. Type text:

```bash
python client.py type "Hello, World!"
```

6. Launch an application:

```bash
python client.py launch "firefox"
```

## API Reference

The server provides the following HTTP endpoints:

- `GET /status` - Check server status
- `GET /screenshot` - Take a screenshot
- `POST /click` - Perform a mouse click
- `POST /doubleclick` - Perform a double-click
- `POST /rightclick` - Perform a right-click
- `POST /moveto` - Move the mouse
- `POST /drag` - Drag the mouse
- `POST /type` - Type text
- `POST /press` - Press a key
- `POST /hotkey` - Press a key combination
- `POST /scroll` - Scroll the mouse wheel
- `POST /find_image` - Find an image on screen
- `POST /launch_application` - Launch an application

## Using the Python Client Library

```python
from client.client import GUISandboxClient

# Create a client instance
client = GUISandboxClient("http://localhost:5000")

# Check server status
status = client.check_status()
print(status)

# Take a screenshot
screenshot = client.take_screenshot("screenshot.png")

# Click at coordinates
result = client.click(100, 200)
print(result)

# Type text
result = client.type_text("Hello, World!")
print(result)

# Launch Firefox
result = client.launch_application("firefox")
print(result)
```

## Security Considerations

This sandbox environment is designed for testing and automation purposes. It provides unrestricted access to the GUI within the container. When deploying in a production environment, consider:

1. Adding authentication to the API
2. Restricting allowed applications
3. Limiting network access
4. Implementing rate limiting

