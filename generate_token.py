"""
Generate Daily.co meeting token for your specific room
Room: https://ddoherty145.daily.co/pipecat-o1
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_token_for_room():
    # Your specific room details
    room_name = "pipecat-o1"  # Extracted from your URL
    room_url = "https://ddoherty145.daily.co/pipecat-o1"
    
    # Get API key from environment
    api_key = os.getenv("DAILY_API_KEY")
    
    if not api_key:
        print("❌ Error: DAILY_API_KEY not found in .env file")
        print("\nPlease add your Daily API key to .env:")
        print("DAILY_API_KEY=your_daily_api_key_here")
        return None
    
    print(f"🎯 Generating token for room: {room_name}")
    print(f"🔗 Room URL: {room_url}")
    
    # Set up API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Token properties optimized for AI agent
    token_data = {
        "properties": {
            "room_name": room_name,
            "user_name": "AI Agent",
            "is_owner": True,           # Gives admin privileges
            "enable_recording": False,   # Disable recording for now
            "start_audio_off": False,   # Agent needs audio on
            "start_video_off": True,    # Agent doesn't need video
            # "exp": int(time.time()) + (24 * 60 * 60)  # 24 hour expiry (optional)
        }
    }
    
    try:
        # Make API request
        response = requests.post(
            "https://api.daily.co/v1/meeting-tokens",
            headers=headers,
            json=token_data,
            timeout=30
        )
        
        if response.status_code == 200:
            token_info = response.json()
            token = token_info["token"]
            
            print("\n✅ Token generated successfully!")
            print("=" * 50)
            print(f"Token: {token}")
            print("=" * 50)
            
            print("\n📝 Add these lines to your .env file:")
            print("-" * 40)
            print(f"DAILY_ROOM_URL={room_url}")
            print(f"DAILY_TOKEN={token}")
            print("-" * 40)
            
            print("\n🚀 Your agent can now connect to the room!")
            print(f"💡 Users can join at: {room_url}")
            
            return token
            
        elif response.status_code == 400:
            print(f"❌ Bad Request (400): {response.text}")
            print("💡 Check if room name 'pipecat-o1' exists in your Daily account")
            
        elif response.status_code == 401:
            print("❌ Unauthorized (401): Invalid API key")
            print("💡 Check your DAILY_API_KEY in .env file")
            
        elif response.status_code == 404:
            print("❌ Room not found (404)")
            print(f"💡 Make sure room 'pipecat-o1' exists in your Daily account")
            
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        
    return None

def verify_room_exists():
    """Optional: Verify the room exists first"""
    api_key = os.getenv("DAILY_API_KEY")
    
    if not api_key:
        return False
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            "https://api.daily.co/v1/rooms/pipecat-o1",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            room_info = response.json()
            print(f"✅ Room exists: {room_info.get('name')}")
            print(f"🔗 URL: {room_info.get('url')}")
            return True
        else:
            print(f"⚠️  Room check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️  Could not verify room: {e}")
        return False

if __name__ == "__main__":
    print("🎪 Daily.co Token Generator")
    print("=" * 30)
    
    # Optional: Check if room exists first
    print("\n🔍 Verifying room exists...")
    verify_room_exists()
    
    # Generate the token
    print("\n🎫 Generating meeting token...")
    token = generate_token_for_room()
    
    if token:
        print(f"\n🎉 Success! Your AI agent can now join the room.")
    else:
        print(f"\n💔 Token generation failed. Check the error messages above.")