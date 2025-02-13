import os
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

# example config 
# OPENAI_URL = 'https://api.openai-proxy.org/v1'
# OPENAI_KEY = 'sk-0HKYasB4TFALRzleJcV1si3MDPAIer1bL6XCQM5orCI50CV2'
# SEND_EMAIL = 'gswxp2@163.com'
# SEND_EMAIL_PASSWORD = 'DUMMY WORDS HERE'
# SEND_EMAIL_SERVER = 'smtp.163.com'
# SEND_EMAIL_PORT = 25
OPENAI_URL = 'https://api.openai-proxy.org/v1'
OPENAI_KEY = 'sk-0HKYasB4TFALRzleJcV1si3MDPAIer1bL6XCQM5orCI50CV2'
SEND_EMAIL = 'paperdogfeed@163.com'
SEND_EMAIL_PASSWORD = 'AWmfXRASWHvdcUcR'
SEND_EMAIL_SERVER = 'smtp.163.com'
SEND_EMAIL_PORT = 25

TRACKS = {}
ARXIV_LIST = []

ARXIV_LIST = load(open("./arxiv_config/arxiv_list.yaml", "r"), Loader=Loader)
print(ARXIV_LIST)
