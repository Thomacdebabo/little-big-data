#!/usr/bin/env python3
"""Complete Strava authorization script that handles OAuth flow and updates .env file."""

import os
import asyncio
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv, set_key
from little_big_data.sources.strava import StravaSource


async def main():
    """Complete Strava authorization flow."""
    load_dotenv()
    
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ Missing STRAVA_CLIENT_ID or STRAVA_CLIENT_SECRET in .env file")
        return
    
    # Step 1: Generate authorization URL
    redirect_uri = "http://localhost:8000/auth/strava/callback"
    auth_url = StravaSource.get_authorization_url(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope="read,activity:read_all"
    )
    
    print("🚀 Strava Authorization Flow")
    print("=" * 50)
    print()
    print("📋 Step 1: Visit the authorization URL")
    print("-" * 40)
    print(auth_url)
    print()
    print("📋 Step 2: After authorizing, you'll be redirected to:")
    print(f"   {redirect_uri}?code=AUTHORIZATION_CODE&scope=...")
    print()
    print("📋 Step 3: Copy the entire callback URL from your browser")
    print("   (It will show an error page, but that's OK - we just need the URL)")
    print()
    
    # Step 2: Get the callback URL from user
    while True:
        callback_url = input("🔗 Paste the full callback URL here: ").strip()
        
        if not callback_url:
            print("❌ Please enter the callback URL")
            continue
            
        try:
            # Parse the callback URL to extract the authorization code
            parsed_url = urlparse(callback_url)
            query_params = parse_qs(parsed_url.query)
            
            if 'code' not in query_params:
                print("❌ No authorization code found in URL. Please make sure you copied the full callback URL.")
                continue
                
            auth_code = query_params['code'][0]
            print(f"✅ Found authorization code: {auth_code[:10]}...")
            break
            
        except Exception as e:
            print(f"❌ Error parsing URL: {e}")
            continue
    
    # Step 3: Exchange code for tokens
    print("\n🔄 Exchanging authorization code for access tokens...")
    
    try:
        token_data = await StravaSource.exchange_code_for_token(
            client_id=client_id,
            client_secret=client_secret,
            code=auth_code
        )
        
        print("✅ Successfully obtained tokens!")
        print(f"   Access Token: {token_data['access_token'][:20]}...")
        print(f"   Refresh Token: {token_data['refresh_token'][:20]}...")
        print(f"   Expires At: {token_data.get('expires_at', 'Unknown')}")
        
        # Step 4: Update .env file
        print("\n💾 Updating .env file with new tokens...")
        
        env_file = ".env"
        set_key(env_file, "STRAVA_ACCESS_TOKEN", token_data['access_token'])
        set_key(env_file, "STRAVA_REFRESH_TOKEN", token_data['refresh_token'])
        
        print("✅ .env file updated successfully!")
        
        # Step 5: Test the new tokens
        print("\n🧪 Testing new tokens...")
        
        config = {
            "client_id": client_id,
            "client_secret": client_secret,
            "access_token": token_data['access_token'],
            "refresh_token": token_data['refresh_token']
        }
        
        strava_source = StravaSource(config)
        authenticated = await strava_source.authenticate()
        
        if authenticated:
            print("✅ Authentication test passed!")
            
            # Try to fetch a few activities
            print("🏃 Fetching recent activities...")
            activities = await strava_source.fetch_data()
            print(f"✅ Successfully fetched {len(activities)} activities!")
            
            if activities:
                print("\n📊 Recent activities:")
                for i, activity in enumerate(activities[:3]):  # Show first 3
                    print(f"  {i+1}. {activity.name} - {activity.timestamp.strftime('%Y-%m-%d')} - {activity.activity_type}")
            
        else:
            print("❌ Authentication test failed")
            
    except Exception as e:
        print(f"❌ Error exchanging code for tokens: {e}")
        return
    
    print("\n🎉 Authorization complete!")
    print("You can now run: uv run python fetch_strava_data.py")


def print_manual_instructions():
    """Print manual instructions if user needs them."""
    print("\n📖 Manual Instructions:")
    print("=" * 50)
    print("1. Go to: https://www.strava.com/settings/api")
    print("2. Create or edit your application")
    print("3. Set Authorization Callback Domain to: localhost")
    print("4. Note your Client ID and Client Secret")
    print("5. Add them to your .env file as:")
    print("   STRAVA_CLIENT_ID=your_client_id")
    print("   STRAVA_CLIENT_SECRET=your_client_secret")


if __name__ == "__main__":
    print("🏃‍♂️ Strava Authorization Helper")
    print("=" * 50)
    
    if not os.path.exists(".env"):
        print("❌ .env file not found!")
        print("Please create a .env file with your Strava app credentials.")
        print_manual_instructions()
    else:
        asyncio.run(main()) 