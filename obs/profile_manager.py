import json
from pathlib import Path
from typing import Any, Dict

PROFILE_FILE = Path('profiles.json')


def load_profiles() -> Dict:
    if PROFILE_FILE.exists():
        with open(PROFILE_FILE, 'r') as f:
            return json.load(f)
    return {'active_profile': '', 'profiles': {}}


def save_profiles(profiles: Dict):
    with open(PROFILE_FILE, 'w') as f:
        json.dump(profiles, f, indent=4)


def set_active_profile(name: str):
    profiles = load_profiles()
    profiles['active_profile'] = name
    save_profiles(profiles)


def save_profile(name: str, data: dict[str, Any]):
    profiles = load_profiles()
    profiles['profiles'][name] = data
    profiles['active_profile'] = name
    save_profiles(profiles)


def get_profile(name: str):
    profiles = load_profiles()
    return profiles['profiles'].get(name, {'obs': '', 'holyrics': ''})
