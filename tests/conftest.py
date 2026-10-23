import os

import shared.config

os.environ["CLOCKIFY_API_KEY"] = "test-key"
os.environ["CLOCKIFY_WORKSPACE_ID"] = "ws1"
shared.config.load_env = lambda env_file=None: None
