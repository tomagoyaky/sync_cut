#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock modules for development and testing when packages are not available
This allows the application to run and be tested without external dependencies
"""

# Mock Flask module
class MockFlask:
    def __init__(self, *args, **kwargs):
        self.secret_key = None
        self.config = {}
        
    def register_blueprint(self, *args, **kwargs):
        pass
        
    def errorhandler(self, code):
        def decorator(f):
            return f
        return decorator
        
    def run(self, *args, **kwargs):
        print(f"Mock Flask app would run on {kwargs.get('host', '0.0.0.0')}:{kwargs.get('port', 5000)}")

class MockBlueprint:
    def __init__(self, *args, **kwargs):
        pass
        
    def route(self, *args, **kwargs):
        def decorator(f):
            return f
        return decorator

class MockRequest:
    def __init__(self):
        self.method = 'GET'
        self.files = {}
        self.form = {}
        self.args = {}

# Mock Flask-SocketIO module  
class MockSocketIO:
    def __init__(self, *args, **kwargs):
        pass
        
    def on(self, event, namespace=None):
        def decorator(f):
            return f
        return decorator
        
    def run(self, app, **kwargs):
        print(f"Mock SocketIO app would run on {kwargs.get('host', '0.0.0.0')}:{kwargs.get('port', 5000)}")

def mock_emit(*args, **kwargs):
    print(f"Mock SocketIO emit: {args}")

def mock_join_room(*args, **kwargs):
    pass

def mock_leave_room(*args, **kwargs):
    pass

# Mock PyYAML
class MockYAML:
    @staticmethod
    def safe_load(stream):
        return {}
    
    @staticmethod
    def dump(data, stream, **kwargs):
        return "# Mock YAML output"

# Mock requests
class MockResponse:
    def __init__(self, status_code=200, text="Mock response"):
        self.status_code = status_code
        self.text = text
    
    def json(self):
        return {"mock": "response"}

class MockRequests:
    @staticmethod
    def get(*args, **kwargs):
        return MockResponse()
    
    @staticmethod
    def post(*args, **kwargs):
        return MockResponse()

# Mock websocket
class MockWebSocketApp:
    def __init__(self, *args, **kwargs):
        pass
    
    def run_forever(self, *args, **kwargs):
        pass

# Mock pydub
class MockAudioSegment:
    def __init__(self, *args, **kwargs):
        self.duration_seconds = 60.0
        
    @classmethod
    def from_file(cls, *args, **kwargs):
        return cls()
    
    def export(self, *args, **kwargs):
        return self
    
    def set_channels(self, *args):
        return self
    
    def set_frame_rate(self, *args):
        return self

def mock_split_on_silence(*args, **kwargs):
    return [MockAudioSegment()]

# Function to install mock modules
def install_mock_modules():
    """Install mock modules into sys.modules to replace missing dependencies"""
    import sys
    
    # Mock Flask
    class MockFlaskModule:
        Flask = MockFlask
        Blueprint = MockBlueprint
        request = MockRequest()
        jsonify = lambda x: x
        render_template = lambda template, **kwargs: f"Mock template: {template}"
        send_file = lambda x: f"Mock file: {x}"
        current_app = MockFlask()
    
    sys.modules['flask'] = MockFlaskModule()
    
    # Mock Flask-SocketIO
    class MockFlaskSocketIOModule:
        SocketIO = MockSocketIO
        emit = mock_emit
        join_room = mock_join_room
        leave_room = mock_leave_room
    
    sys.modules['flask_socketio'] = MockFlaskSocketIOModule()
    
    # Mock PyYAML
    sys.modules['yaml'] = MockYAML()
    
    # Mock requests
    sys.modules['requests'] = MockRequests()
    
    # Mock websocket
    class MockWebSocketModule:
        WebSocketApp = MockWebSocketApp
    
    sys.modules['websocket'] = MockWebSocketModule()
    
    # Mock pydub
    class MockPydubModule:
        AudioSegment = MockAudioSegment
        
        class silence:
            split_on_silence = staticmethod(mock_split_on_silence)
    
    sys.modules['pydub'] = MockPydubModule()
    sys.modules['pydub.silence'] = MockPydubModule.silence()
    
    # Mock whisper
    class MockWhisperModule:
        @staticmethod
        def load_model(name):
            return object()
        
        @staticmethod
        def transcribe(model, audio, **kwargs):
            return {
                "text": "Mock transcription result",
                "segments": [
                    {"start": 0.0, "end": 5.0, "text": "Mock segment 1"},
                    {"start": 5.0, "end": 10.0, "text": "Mock segment 2"}
                ]
            }
    
    sys.modules['whisper'] = MockWhisperModule()
    
    # Mock werkzeug
    class MockWerkzeugUtils:
        @staticmethod
        def secure_filename(filename):
            return filename.replace(" ", "_")
    
    class MockWerkzeugModule:
        utils = MockWerkzeugUtils()
    
    sys.modules['werkzeug'] = MockWerkzeugModule()
    sys.modules['werkzeug.utils'] = MockWerkzeugUtils()
    
    print("Mock modules installed successfully")

if __name__ == "__main__":
    install_mock_modules()