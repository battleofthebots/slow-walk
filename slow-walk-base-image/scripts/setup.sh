# Required for populate_gitlab.py to work (and for competitors to clone - they also have http tho)
service ssh start
# Gotta run this before reconfigure or it'll hang: https://gitlab.com/gitlab-org/omnibus-gitlab/-/issues/4257
/opt/gitlab/embedded/bin/runsvdir-start & gitlab-ctl reconfigure
python3 /scripts/populate_gitlab.py root battlingrobotsbattleitoutbattleofthebots http://127.0.0.1 /repos battlebot --wait-for-it
rm /scripts/populate_gitlab.py
gitlab-ctl stop
echo "MAKE YOUR IMAGE NOW <3"
sleep infinity # block container from exiting