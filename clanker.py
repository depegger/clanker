from flask import Flask, request, abort, Response
from telegram import Bot, error
import hmac
import hashlib
import re
import os

app = Flask(__name__)

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "8046276998:AAE3uEaRg1sOXa6cmyDAdmU_bJA5CL2Lc-0"  # Replace with your bot token
CHAT_ID = "-1002286230493"  # Replace with your group chat ID

# Webhook Secret for Verification
WEBHOOK_SECRET = "qfHUgWP7t6ISOYClcbFgHRwmF"


# Create a Telegram bot instance
bot = Bot(token=TELEGRAM_BOT_TOKEN)




# Regex pattern to extract contract address from the embed hyperlink
CONTRACT_ADDRESS_PATTERN = r'href=["\'](https://clanker.world/token/([^"\']+))["\']'

def verify_signature(request):
    """Verify webhook signature"""
    received_signature = request.headers.get('X-Neynar-Signature')
    if not received_signature:
        return False

    computed_signature = hmac.new(
        key=WEBHOOK_SECRET.encode(),
        msg=request.get_data(),
        digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_signature, received_signature)

@app.route('/')
def home():
    return "Webhook server is running.", 200

@app.route('/webhook', methods=['POST'])
def neynar_webhook():
    # Enable verification for security
    if not verify_signature(request):
        abort(403)

    # Get the incoming JSON data
    data = request.get_json()
    print("Received Data:", data)  # Debug line to see what data is coming in

    if data:
        # Extract relevant details from webhook payload
        event_type = data.get('event_type', '')
        cast_author_fid = data.get('author_fid', '')
        print(f"Event Type: {event_type}, Author FID: {cast_author_fid}")  # Debug line

        # Check if it's a new cast created by FID 874542
        if event_type == "cast.created" and cast_author_fid == "874542":
            print("New cast event detected.")  # Debug line
            token_name = data.get('text', 'Unknown Token')
            contract_address = None

            # Extract contract address from embeds (hyperlink)
            embeds = data.get('embeds', [])
            for embed in embeds:
                # Match and extract the href attribute to get the contract address
                match = re.search(CONTRACT_ADDRESS_PATTERN, embed)
                if match:
                    contract_address = match.group(2)  # Extracted contract address
                    print(f"Contract Address Found: {contract_address}")  # Debug line
                    break

            # Format the notification message
            if contract_address:
                message = f"New Token Created!\nToken Name: {token_name}\nContract Address: {contract_address}"
            else:
                message = f"New Token Created!\nToken Name: {token_name}\n(Contract Address not available)"

            # Debugging before sending message
            print("Preparing to send message to Telegram...")
            try:
                send_telegram_message(message)
                print("Message sent to Telegram successfully!")  # Debug line
            except error.TelegramError as e:
                print(f"Failed to send message to Telegram: {e}")  # Debug line for error

    return Response(status=200)

def send_telegram_message(message):
    bot.send_message(chat_id=CHAT_ID, text=message)

if __name__ == "__main__":
    app.run(port=5000)
