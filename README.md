# Website Cloner Tool

A powerful Python-based tool for cloning websites and capturing visitor images. This tool is designed for educational purposes and security testing only.

## Features

- 🌐 Website Cloning: Accurately clones target websites including styles and layout
- 📸 Camera Capture: Captures visitor images when they interact with the cloned site
- 🔗 Ngrok Integration: Automatically creates public URLs for the cloned sites
- 💬 Discord Integration: Sends captured images directly to a Discord channel
- 🚀 Automated Setup: One-click setup with virtual environment and dependency management
- 🎨 Professional UI: Rich command-line interface with colors and status indicators

## Requirements

- Python 3.8 or higher
- Internet connection
- Ngrok account (free)
- Discord webhook URL (optional, for receiving captured images)

## Installation

1. Clone or download this repository
2. Run the tool:
   ```bash
   python website_cloner.py
   ```
   The script will automatically:
   - Create a virtual environment
   - Install required packages
   - Prompt for your ngrok auth token
   - Prompt for your Discord webhook URL (optional)

## First-Time Setup

1. Get your ngrok auth token from [Ngrok Dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)
2. (Optional) Create a Discord webhook URL:
   - Open your Discord server settings
   - Go to Integrations > Webhooks
   - Create a new webhook and copy the URL

## Usage

1. Run the tool:
   ```bash
   python website_cloner.py
   ```

2. Enter the target website URL when prompted

3. The tool will:
   - Clone the website
   - Start a local server
   - Create a public URL using ngrok
   - Begin capturing visitor images
   - Send captured images to Discord (if configured)

4. Press Ctrl+C to stop the server

## Important Notes

- 🔒 This tool is for educational purposes only
- ⚠️ Always obtain proper authorization before testing on any website
- 🛡️ Use responsibly and ethically
- 📝 Captured images are stored in the `captured_images` directory
- ⚙️ Configuration files are saved in:
  - `ngrok_config.json`: Stores your ngrok auth token
  - `webhook_config.json`: Stores your Discord webhook URL

## Files

- `website_cloner.py`: Main script file
- `requirements.txt`: Python package dependencies
- `captured_images/`: Directory for storing captured images
- `cloned_site/`: Directory for storing cloned website files

## Cleanup

To remove all generated files and start fresh:
1. Delete the `venv` directory
2. Delete the `captured_images` directory
3. Delete the `cloned_site` directory
4. Delete `ngrok_config.json` and `webhook_config.json`

## Legal Disclaimer

This tool is provided for educational purposes only. Users are responsible for complying with applicable laws and obtaining necessary permissions before using this tool. The authors are not responsible for any misuse or damage caused by this tool. 