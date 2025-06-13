FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install X11, window manager, Python, and other dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    xfce4 \
    xfce4-terminal \
    python3 \
    python3-pip \
    python3-tk \
    python3-dev \
    firefox \
    curl \
    dbus-x11 \
    libnotify4 \
    libgtk-3-0 \
    libx11-xcb1 \
    libnss3 \
    libxss1 \
    libasound2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY server/requirements.txt /app/server/requirements.txt
RUN pip3 install --no-cache-dir -r /app/server/requirements.txt

# Set up working directory
WORKDIR /app

# Copy server code
COPY server /app/server

# Expose port for the API server
EXPOSE 5000

# Expose VNC port (optional, for debugging)
EXPOSE 5900

# Create a non-root user to run the application
RUN useradd -m -s /bin/bash sandbox
RUN chown -R sandbox:sandbox /app

USER sandbox

# Create a script to start Xvfb, window manager, and the server
RUN echo '#!/bin/bash\n\
Xvfb :1 -screen 0 1280x1024x16 &\n\
export DISPLAY=:1\n\
x11vnc -display :1 -nopw -forever -quiet &\n\
startxfce4 &\n\
cd /app/server && python3 server.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Set the display environment variable
ENV DISPLAY=:1

# Command to run when container starts
CMD ["/app/start.sh"]
