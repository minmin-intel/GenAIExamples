#!/bin/bash

# Setup and start the GUI Sandbox environment

# Make shared directory if it doesn't exist
mkdir -p shared

# Build and start the container
echo "Building and starting the GUI Sandbox container..."
docker-compose up -d --build

# Wait for the server to start
echo "Waiting for the server to start..."
sleep 10

# # Install client requirements
# echo "Installing client requirements..."
# cd client
# pip install -r requirements.txt

# # Test if the server is running
# echo "Testing connection to the server..."
# python client.py status

# echo ""
# echo "GUI Sandbox is now running!"
# echo "Server API: http://localhost:5000"
# echo "VNC Server: localhost:5900"
# echo ""
# echo "You can use the client.py script to interact with the sandbox."
# echo "Example: python client.py screenshot --save screenshot.png"
# echo ""
# echo "To stop the container, run: docker-compose down"
