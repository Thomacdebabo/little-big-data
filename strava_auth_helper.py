#!/usr/bin/env python3
"""Helper script to get Strava authorization URL with correct scopes."""

import os
from dotenv import load_dotenv
from little_big_data.sources.strava import StravaSource

def main():
    """Generate Strava authorization URL."""
    load_dotenv()
    
    client_id = os.getenv("STRAVA_CLIENT_ID")
    if not client_id:
        print("❌ STRAVA_CLIENT_ID not found in .env file")
        return
    
    # Use a generic redirect URI - you'll need to set this up in your Strava app
    redirect_uri = "http://localhost:8000/auth/strava/callback"
    
    # Get authorization URL with correct scopes
    auth_url = StravaSource.get_authorization_url(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope="read,activity:read_all"  # This includes activity reading permissions
    )
    
    print("🔗 Strava Authorization URL:")
    print("=" * 80)
    print(auth_url)
    print("=" * 80)
    print()
    print("📋 Instructions:")
    print("1. Visit the URL above in your browser")
    print("2. Authorize the application with Strava")
    print("3. Copy the authorization code from the callback URL")
    print("4. Use the code to get new access and refresh tokens")
    print()
    print("⚠️  Note: Make sure your Strava app settings have the redirect URI:")
    print(f"   {redirect_uri}")
    print()
    print("🔧 The required scopes are: read,activity:read_all")
    print("   - 'read' allows basic profile access")
    print("   - 'activity:read_all' allows reading all activities")

if __name__ == "__main__":
    main() 