import os

# These are required to access data from spotify and can be found here:
# https://developer.spotify.com/documentation/general/guides/app-settings/
os.environ["SPOTIPY_CLIENT_ID"] = ""
os.environ["SPOTIPY_CLIENT_SECRET"] = ""

# In order to have songs show up in a search their names might have to be changed
# Include these changes using the format {"track1Name": "changed track1Name", "track2Name": "changed track2Name"}
special_rules = {}

# Check if not git tracked config file exists
path = os.path.dirname(__file__)
if os.path.exists(os.path.join(path, "my_config.py")):
    from my_config import *
