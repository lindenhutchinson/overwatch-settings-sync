# Overwatch Settings Transfer

So you want to play on a new account, but on your main you've adjusted the sensitivity for each hero.

Do you want to spend hours transferring all those settings across manually? Of course not!

This script allows you to capture all your individual hero sensitivities as a JSON file. You can then run it again on your new account to load up the custom sensitivity for each hero.

## How to Run

This script will take control of your cursor for a short period.
If you want to cancel it at any time, press `ctrl + shift + escape` and end the process.

1. Create a virtual environment and activate it

    virtualenv venv
    source venv/Scripts/activate

2. Install the required packages

    pip install -r requirements.txt

3. Run the GUI

    python gui.py

4. Capture the settings from your desired account. Load up the game client and press escape. Then click 'Get Settings' (toggle human movement on to better see what's happening)

5. Sync the settings with another account. Load up the game client on the second account and press escape. Then click 'Set Settings'
