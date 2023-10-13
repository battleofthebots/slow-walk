# Required for populate_gitlab.py to work (and for competitors to clone - they also have http tho)
service ssh start
# Gotta run this before reconfigure or it'll hang: https://gitlab.com/gitlab-org/omnibus-gitlab/-/issues/4257
/opt/gitlab/embedded/bin/runsvdir-start & gitlab-ctl start
python3 /scripts/initialize_runner.py