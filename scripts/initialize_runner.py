import requests
import time
import json
import os
import traceback

# Script to initialize gitlab runner on other host
# user: root
# password: secretformula
# Runner Registration token: tokensauce

# address = "http://cve-2019-18634-test_gitlab-1"
# address = "http://gitlab"
address = "http://127.0.0.1"
registrationToken = "tokensauce"


# Loop until gitlab is up (30s polling)
request = None
while request == None or request.status_code != 200:
    time.sleep(30)
    try:
        request = requests.get(address)
        print(request.status_code)
        print(request.reason)
        print(request.text)
    except:
        continue

# 2 sets of tokens required: https://docs.gitlab.com/ee/api/runners.html#register-a-new-runner
# Registration Token (used to register a new runner)
# Authentication Token (used to authenticate and link runner with GitLab), obtained with Registration Token

os.system('gitlab-runner register --non-interactive --url "' + address + '" --clone-url "' + address + '" --executor "shell" --registration-token "' + registrationToken + '"')
os.system('gitlab-runner verify')
os.system('gitlab-runner run')