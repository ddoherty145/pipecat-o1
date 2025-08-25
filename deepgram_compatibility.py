#!/usr/bin/env python3
"""
Deepgram compatibility layer for Pipecat
This fixes the import issues between Pipecat and the current Deepgram library
"""

import sys
from types import ModuleType

# Create a compatibility module
class DeepgramCompatibility(ModuleType):
    """Compatibility layer for Deepgram imports"""
    
    def __init__(self):
        super().__init__('deepgram')
        self._setup_compatibility()
    
    def _setup_compatibility(self):
        """Set up compatibility mappings"""
        try:
            # Import the actual deepgram module
            import deepgram as real_deepgram
            
            # Map old names to new names
            self.AsyncListenWebSocketClient = real_deepgram.transcription.LiveTranscription
            self.DeepgramClient = real_deepgram.Deepgram
            self.DeepgramClientOptions = real_deepgram.transcription.Options
            self.ErrorResponse = real_deepgram.Transcription
            
            # Create a wrapper for DeepgramClient to handle the old API
            class DeepgramClientWrapper:
                def __init__(self, api_key, config=None, **kwargs):
                    # Extract options from config if provided
                    if config and hasattr(config, 'to_dict'):
                        options = config.to_dict()
                    else:
                        options = {}
                    
                    # Create the actual Deepgram client
                    self._client = real_deepgram.Deepgram(api_key)
                    
                    # Forward any other attributes
                    for attr in dir(self._client):
                        if not attr.startswith('_'):
                            setattr(self, attr, getattr(self._client, attr))
            
            self.DeepgramClient = DeepgramClientWrapper
            
            # Map additional required classes
            self.LiveOptions = real_deepgram.transcription.Options
            self.LiveResultResponse = real_deepgram.Transcription
            self.LiveTranscriptionEvents = real_deepgram.transcription.LiveTranscription
            
            # Create dummy classes for missing functionality
            class SpeakOptions:
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)
            
            self.SpeakOptions = SpeakOptions
            
            # Fix the Options class to have to_dict method
            class FixedOptions:
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)
                
                def to_dict(self):
                    return self.__dict__.copy()
            
            # Replace the Options classes
            self.Options = FixedOptions
            self.LiveOptions = FixedOptions
            self.DeepgramClientOptions = FixedOptions
            
            # Copy other attributes
            for attr in dir(real_deepgram):
                if not attr.startswith('_'):
                    setattr(self, attr, getattr(real_deepgram, attr))
                    
            print("✅ Deepgram compatibility layer initialized successfully")
            
        except ImportError as e:
            print(f"❌ Failed to import deepgram: {e}")
            # Create dummy classes to prevent import errors
            class DummyClass:
                def __init__(self, *args, **kwargs):
                    raise ImportError("Deepgram library not available")
            
            self.AsyncListenWebSocketClient = DummyClass
            self.DeepgramClient = DummyClass
            self.DeepgramClientOptions = DummyClass
            self.ErrorResponse = DummyClass

# Install the compatibility layer
compatibility_module = DeepgramCompatibility()
sys.modules['deepgram'] = compatibility_module

print("🔧 Deepgram compatibility layer installed")
print("💡 This should resolve Pipecat import issues")
