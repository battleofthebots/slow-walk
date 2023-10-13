FROM ghcr.io/battleofthebots/botb-base-image:latest

# Environment variables for gitlab install (hopefully it works)
ENV DEBUG=false \
    GITLAB_HTTPS=false \
    GITLAB_SELF_SIGNED=false \
    GITLAB_PORT=8080 \
    GITLAB_SSH_PORT=22222 \
    GITLAB_SECRETS_DB_KEY_BASE=beepboopboopboopboopbeepboopboopbeepbeepbeepboop \
    GITLAB_SECRETS_SECRET_KEY_BASE=boopboopbeepbeepbeepbeepboopboopbeepboopboop \
    GITLAB_SECRETS_OTP_KEY_BASE=beepboopboopbeepboopbeepboopboopbeepboopbeepbeep \
    GITLAB_ROOT_PASSWORD=battlingrobotsbattleitoutbattleofthebots \
    GITLAB_SHARED_RUNNERS_REGISTRATION_TOKEN=tokensauce

RUN curl -s https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.deb.sh | bash
RUN apt-get install gitlab-ce=14.8.3-ce.0
RUN apt-get -y install git

# Install gitlab runner (to link with gitlab challenge for lateral movement)
# Gitlab runner registration token deprecated since v15.6
# Additionally, GitlabRunner v15+ can't communicate with gitlab < 14.8
RUN apt-get -y install git
RUN curl -LJO "https://gitlab-runner-downloads.s3.amazonaws.com/v14.8.3/deb/gitlab-runner_amd64.deb"
RUN dpkg -i gitlab-runner_amd64.deb
RUN rm gitlab-runner_amd64.deb

# Required for python auth script
# Already in golden image
# RUN pip install requests
# Ok so all of a sudden now python is complaining, we gotta do this
RUN pip3 install requests
RUN pip3 install gitpython
RUN pip3 install python-gitlab
RUN pip3 install pycryptodome

# Taking out since we'll only need to do the runner in post_base, gitlab-runner install stays here though
#COPY scripts/initialize_runner.py scripts/initialize_runner.py
COPY scripts/populate_gitlab.py scripts/populate_gitlab.py
COPY scripts/setup.sh scripts/setup.sh
RUN chmod +x scripts/setup.sh
RUN chown -R user:user /scripts

COPY keys/key /keys/key
COPY keys/key.pub /keys/key.pub
RUN chmod 600 keys/*
COPY repos/testrepo.tar.gz repos/testrepo.tar.gz

# So gitlab-runner can properly begin executing
RUN rm /home/user/.bash_logout

CMD /scripts/setup.sh

HEALTHCHECK --interval=60s --timeout=30s --retries=5 \
CMD /opt/gitlab/bin/gitlab-healthcheck --fail --max-time 10