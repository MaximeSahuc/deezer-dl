import sys
import os
import os.path
from configparser import ConfigParser

config_file = "settings.ini"
config = ConfigParser()

def create_config_file(path):
        f = open(config_path, 'w')
        f.write(
"""[deezer]
; login manually using your web browser and take the ARL cookie
cookie_arl = your_arl_cookie

; user id for favorite song to be downloaded
user_id = your_user_id

music_dir = /tmp/deezer-dl

; download track once, use hard links for tracks in playlists
use_hard_links = True

; deezer country
country = us"""
        )
        f.close()


def load_config(config_path):
    config.read(config_path)

    if "DEEZER_COOKIE_ARL" in os.environ.keys():
        config["deezer"]["cookie_arl"] = os.environ["DEEZER_COOKIE_ARL"]


config_folder = os.path.join(os.path.expanduser("~"), '.config', 'deezer-dl')
os.makedirs(config_folder, exist_ok=True)
config_path = os.path.join(config_folder, config_file)

# Create config if not present
if not os.path.exists(config_path):
    create_config_file(config_path)
    print(f"New config file created at {config_path}\nPlease configure it before running deezer-dl.")
    sys.exit(1)

# print(f"Loading {config_path}")
load_config(config_path)