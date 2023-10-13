# Slow Walk (joint-gitlab-and-runner)

This container contains Gitlab (v14.8.3) + Gitlab Runner (v14.8.3). This version of gitlab is >1 year old, but was selected to maintain compatiability with the Gitlab runner registration script utilized for BSides; Gitlab changed their registration procedures in v15.

In order to access /flags, users will have to gain shell access via the Gitlab Runner. The Gitlab Runner is configured with a shell executor, meaning all commands present in a CI/CD pipeline (*.gilab-ci.yml*) will be executed as shell commands.

Contestants will be provided a "leaked" ssh private key (*keys/key*) along with a repository (**MAY CHANGE TO PROVIDING SSH KEY + PCAP**, PCAP gives the repo+credentials and would make this challenge less trivial if contestants have to dig a little for it - see *repo_credentials.png* and *repo_address.png* for where to find it). Using this key/information, contestants will be able to clone down the repo, update the *.gitlab-ci.yml*, then push their changes to get shell access to the machine.

## Solution

The provided *solution.sh* and *solution_.gitlab-ci.yml* files outline a potential solution. *solution.sh* is responsible for starting a reverse shell listener in addition to pushing up a *.gitlab-ci.yml* file up to the repo (which connects to our listener). We even got a cool separate window for the reverse shell too. This script will also delete the repo after pushing up the code since it'll no longer be needed, the payload is dropped after pushing.

Simply edit the addresses in each of these files to point to the right place. Specifically *<gitlab_ip_address>* in *solution.sh* and *<attacker_ip_address>* in *solution_.gitlab-ci.yml*.

Note: For testing, to get the host/attacker ip-address, use the IP for the *br-XXXXX* interface which is UP while the container is running.

## Static Flag + Solution

What is the name of the git repository?

Answer: testrepo

What are the credentials of the repo user? (username:password)

Answer: battlebot:battlebot

-----

Pre-challenge prep
`ssh-keygen -f key -C battlebot-gitlab` to generate ssh keys
`tar -czf /repos/testrepo.tar.gz test.c .gitlab-ci.yml` to create required .tar.gz for repo creation

For testing
`git -c core.sshCommand="ssh -i {private-key}" clone git@{docker-gitlab-ip}:battlebot/testrepo.git`

------------------------------

Procedure to generate slow-walk-base:
1. Using the Dockerfile in *slow-walk-base-image* of this repo: `docker compose up --build`
2. Wait for full initialization procedure to finish. (`MAKE YOUR IMAGE NOW <3` in stdout of container)
3. Commit+tag the image by either:
    - Doing so locally: `docker commit <container name> slow-walk-base-image:latest`
    - Doing so for a github container registry: `docker commit <container name> ghcr.io/battleofthebots/slow-walk-base-image:latest`. You can then push to the container registry (given your login token has write permissions): `docker push ghcr.io/battleofthebots/slow-walk-base-image`.
4. (Optional) If tagging locally, docker save the image to create a tar to transfer the image between machines: `docker save <tag from step 3> | gzip > slow-walk-base-image.tar.gz`. The image file can later be added to a machine: `docker load < slow-walk-base-image.tar.gz`. 
    - If tagging for a github container registry, you can simply pull down the image using `docker pull ghcr.io/battleofthebots/slow-walk-base-image` without transferring the tarball.
4. Once the commit completes, you can safely shutdown the container.
5. Start the Dockerfile located in the root of this repo: `docker compose up --build`
    - Note: In the root Dockerfile, we can now use `FROM ghcr.io/battleofthebots/slow-walk-base-image:latest` (or `FROM slow-walk-base-image:latest`) to get our preconfigured gitlab environment with the battlebot user + repo. The runner will still have to be reinitialized, but that's still significantly faster than before (gitlab reconfigure was the bottleneck).