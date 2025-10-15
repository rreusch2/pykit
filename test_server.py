#!/usr/bin/env python3
"""
Test script for ParleyApp ChatKit Server
Run this to verify your setup is working correctly
"""

import asyncio
import json
import httpx
from datetime import datetime

async def test_chatkit_server():
    """Test the ChatKit server endpoints"""
    
    base_url = "http://localhost:8001"
    
    print("🧪 Testing ParleyApp ChatKit Server...")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1. Testing health endpoint...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Could not connect to server: {e}")
            print("   Make sure the server is running: uvicorn app:app --reload")
            return
    
    # Test 2: Create Thread
    print("\n2. Testing thread creation...")
    async with httpx.AsyncClient() as client:
        create_thread_request = {
            "type": "threads.create",
            "params": {
                "input": {
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Hey Professor Lock, what are the best MLB bets today?"
                        }
                    ],
                    "attachments": [],
                    "inference_options": {}
                }
            }
        }
        
        try:
            response = await client.post(
                f"{base_url}/chatkit",
                json=create_thread_request,
                headers={
                    "X-User-Id": "test-user-123",
                    "X-Session-Id": "test-session-456"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                print("✅ Thread created successfully")
                
                # Handle streaming response
                if response.headers.get("content-type") == "text/event-stream":
                    print("   Streaming response received:")
                    lines = response.text.split('\n')
                    for line in lines[:5]:  # Show first 5 lines
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                print(f"   Event: {data.get('type', 'unknown')}")
                            except:
                                pass
                else:
                    print(f"   Response: {response.json()}")
            else:
                print(f"❌ Thread creation failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error creating thread: {e}")
    
    # Test 3: Test Widget Generation
    print("\n3. Testing widget generation...")
    async with httpx.AsyncClient() as client:
        widget_test_request = {
            "type": "threads.create",
            "params": {
                "input": {
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Show me live MLB odds with a visual comparison"
                        }
                    ],
                    "attachments": [],
                    "inference_options": {}
                }
            }
        }
        
        try:
            response = await client.post(
                f"{base_url}/chatkit",
                json=widget_test_request,
                headers={
                    "X-User-Id": "test-user-123",
                    "X-Session-Id": "test-session-widget"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                print("✅ Widget request processed")
                # Check if response contains widget events
                if "widget" in response.text:
                    print("   ✅ Widget events detected in response")
                else:
                    print("   ⚠️ No widget events found (agent may need real data)")
            else:
                print(f"❌ Widget test failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing widgets: {e}")
    
    # Test 4: Test Parlay Builder
    print("\n4. Testing parlay builder action...")
    async with httpx.AsyncClient() as client:
        parlay_request = {
            "type": "threads.create",
            "params": {
                "input": {
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Build me a 3-leg parlay with Yankees, Dodgers, and under 8.5 runs"
                        }
                    ],
                    "attachments": [],
                    "inference_options": {}
                }
            }
        }
        
        try:
            response = await client.post(
                f"{base_url}/chatkit",
                json=parlay_request,
                headers={
                    "X-User-Id": "test-user-123",
                    "X-Session-Id": "test-session-parlay"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                print("✅ Parlay builder request processed")
                if "parlay" in response.text.lower():
                    print("   ✅ Parlay widget likely generated")
                    
        except Exception as e:
            print(f"❌ Error testing parlay builder: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("   If all tests passed, your ChatKit server is ready!")
    print("   Professor Lock is ready to analyze bets! 🎰")
    print("\n📝 Next Steps:")
    print("   1. Set up your OpenAI API key in .env")
    print("   2. Configure DATABASE_URL for PostgreSQL")
    print("   3. Connect to your Node.js backend")
    print("   4. Deploy to Railway for production")

if __name__ == "__main__":
    asyncio.run(test_chatkit_server())
