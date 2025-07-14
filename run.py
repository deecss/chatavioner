#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punkt startowy aplikacji Aero-Chat
"""
import os
from app import create_app
from flask_socketio import SocketIO

app = create_app()
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

if __name__ == "__main__":
    # Uruchom watcher w osobnym wątku
    from watcher import start_watcher
    start_watcher()
    
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
