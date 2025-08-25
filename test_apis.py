#!/usr/bin/env python3
"""
Test script to verify Cartesia and Deepgram APIs are working
"""

import os
import asyncio
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_cartesia_api():
    """Test Cartesia TTS API connectivity"""
    print("🧪 Testing Cartesia TTS API...")
    
    api_key = os.getenv("CARTESIA_API_KEY")
    if not api_key:
        print("  ❌ CARTESIA_API_KEY not found in environment variables")
        print("  💡 Add CARTESIA_API_KEY=your_key_here to your .env file")
        return False
    
    try:
        # Test basic API connectivity by fetching available voices
        headers = {
            "X-API-Key": api_key,
            "Cartesia-Version": "2025-04-16"  # Add required version header
        }
        resp = requests.get("https://api.cartesia.ai/voices", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            print("  ✅ Cartesia API: Connected successfully")
            voices = resp.json()
            print(f"  📊 Available voices: {len(voices.get('voices', []))}")
            return True
        else:
            print(f"  ❌ Cartesia API: HTTP {resp.status_code}")
            print(f"  📝 Response: {resp.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Cartesia API: Connection failed - {str(e)[:100]}")
        return False
    except Exception as e:
        print(f"  ❌ Cartesia API: Unexpected error - {str(e)[:100]}")
        return False

def test_deepgram_api():
    """Test Deepgram STT API connectivity"""
    print("\n🧪 Testing Deepgram STT API...")
    
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        print("  ❌ DEEPGRAM_API_KEY not found in environment variables")
        print("  💡 Add DEEPGRAM_API_KEY=your_key_here to your .env file")
        return False
    
    try:
        # Test basic API connectivity by fetching project info
        headers = {"Authorization": f"Token {api_key}"}
        resp = requests.get("https://api.deepgram.com/v1/projects", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            print("  ✅ Deepgram API: Connected successfully")
            projects = resp.json()
            print(f"  📊 Available projects: {len(projects.get('projects', []))}")
            return True
        else:
            print(f"  ❌ Deepgram API: HTTP {resp.status_code}")
            print(f"  📝 Response: {resp.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Deepgram API: Connection failed - {str(e)[:100]}")
        return False
    except Exception as e:
        print(f"  ❌ Deepgram API: Unexpected error - {str(e)[:100]}")
        return False

async def test_pipecat_services():
    """Test Pipecat service integrations"""
    print("\n🧪 Testing Pipecat Service Integrations...")
    
    # Test Cartesia TTS service
    try:
        from pipecat.services.cartesia.tts import CartesiaTTSService
        print("  ✅ Cartesia TTS service: Import successful")
        
        # Test service creation
        api_key = os.getenv("CARTESIA_API_KEY")
        if api_key:
            # Cartesia requires a voice_id parameter
            voice_id = os.getenv("CARTESIA_VOICE_ID", "clara")  # Use default voice if not specified
            tts = CartesiaTTSService(api_key=api_key, voice_id=voice_id)
            print("  ✅ Cartesia TTS service: Instance created successfully")
        else:
            print("  ⚠️ Cartesia TTS service: Cannot test without API key")
            
    except ImportError as e:
        print(f"  ❌ Cartesia TTS service: Import failed - {str(e)[:100]}")
    except Exception as e:
        print(f"  ❌ Cartesia TTS service: Error - {str(e)[:100]}")
    
    # Test Deepgram STT service
    try:
        from pipecat.services.deepgram.stt import DeepgramSTTService
        print("  ✅ Deepgram STT service: Import successful")
        
        # Test service creation
        api_key = os.getenv("DEEPGRAM_API_KEY")
        if api_key:
            stt = DeepgramSTTService(api_key=api_key)
            print("  ✅ Deepgram STT service: Instance created successfully")
        else:
            print("  ⚠️ Deepgram STT service: Cannot test without API key")
            
    except ImportError as e:
        print(f"  ❌ Deepgram STT service: Import failed - {str(e)[:100]}")
    except Exception as e:
        print(f"  ❌ Deepgram STT service: Error - {str(e)[:100]}")

def check_environment():
    """Check environment variables"""
    print("🔍 Environment Variables Check:")
    
    required_vars = {
        "CARTESIA_API_KEY": "Cartesia TTS API key",
        "DEEPGRAM_API_KEY": "Deepgram STT API key",
        "OPENAI_API_KEY": "OpenAI API key (for LLM)",
        "DAILY_TOKEN": "Daily.co token",
        "DAILY_ROOM_URL": "Daily.co room URL"
    }
    
    all_good = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask the API key for security
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"  ✅ {var}: {masked_value}")
        else:
            print(f"  ❌ {var}: Missing ({description})")
            all_good = False
    
    return all_good

def create_env_template():
    """Create a template .env file"""
    print("\n📝 Creating .env template file...")
    
    template = """# API Keys
CARTESIA_API_KEY=your_cartesia_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Daily.co Configuration
DAILY_TOKEN=your_daily_token_here
DAILY_ROOM_URL=https://your-domain.daily.co/your-room-name

# Optional: Cartesia voice settings
CARTESIA_VOICE_ID=your_preferred_voice_id_here
"""
    
    try:
        with open(".env.template", "w") as f:
            f.write(template)
        print("  ✅ Created .env.template file")
        print("  💡 Copy this to .env and fill in your actual API keys")
    except Exception as e:
        print(f"  ❌ Failed to create template: {e}")

def main():
    """Main test function"""
    print("🚀 API Connectivity Test Suite")
    print("=" * 50)
    
    # Check environment
    env_ok = check_environment()
    
    if not env_ok:
        print("\n⚠️ Some environment variables are missing.")
        create_env_template()
        print("\n🔧 Please set up your .env file and run this script again.")
        return
    
    # Test APIs
    cartesia_ok = test_cartesia_api()
    deepgram_ok = test_deepgram_api()
    
    # Test Pipecat integrations
    asyncio.run(test_pipecat_services())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"  Cartesia API: {'✅ Working' if cartesia_ok else '❌ Failed'}")
    print(f"  Deepgram API: {'✅ Working' if deepgram_ok else '❌ Failed'}")
    print(f"  Environment: {'✅ Complete' if env_ok else '❌ Incomplete'}")
    
    if cartesia_ok and deepgram_ok:
        print("\n🎉 All APIs are working correctly!")
        print("💡 You can now run your baml_agent.py successfully.")
    else:
        print("\n⚠️ Some APIs are not working.")
        print("🔧 Check your API keys and internet connection.")

if __name__ == "__main__":
    main()
