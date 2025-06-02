from kiteconnect import KiteConnect
import webbrowser

# 🔑 Set your API key and secret here
api_key = "l9y0a5vozuozcjw4"
api_secret = "aof34binfok8wn7bzh4buootmhkscw01"  # Replace with your actual secret

# Create KiteConnect instance
kite = KiteConnect(api_key=api_key)

# Step 1: Get the login URL and open it in the browser
login_url = kite.login_url()
print(f"👉 Open this URL to login:\n{login_url}")
webbrowser.open(login_url)

# Step 2: After login, user pastes request_token from redirected URL
request_token = input("🔐 Enter the request_token from the URL after login: ").strip()

# Step 3: Generate session (access_token)
try:
    data = kite.generate_session(request_token, api_secret=api_secret)
    access_token = data["access_token"]
    
    # Save access token to file
    with open("access_token.txt", "w") as f:
        f.write(access_token)
    
    print("✅ Access token saved successfully!")

except Exception as e:
    print("❌ Failed to generate session:", str(e))
