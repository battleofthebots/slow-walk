from argparse import ArgumentParser, Namespace
from contextlib import contextmanager
from enum import Enum
from os import getcwd, chdir, listdir, makedirs, rmdir, chown, open as osopen, O_WRONLY, O_CREAT, O_TRUNC, walk, remove
from os.path import basename, dirname, isdir, join
from random import choice
from subprocess import check_call
from tarfile import open as taropen
from tempfile import TemporaryDirectory
from time import sleep
from uuid import uuid4

from Crypto.PublicKey import RSA
from git import Repo
from git.util import Actor
from gitlab import Gitlab
from requests import post


@contextmanager
def dircontext(newdir):
    olddir = getcwd()
    chdir(newdir)
    try:
        yield
    finally:
        chdir(olddir)


class LogLevel(Enum):
    success = 0
    info = 1
    debug = 2
    warning = 3
    error = 4


def log_to_console(message: str, level: LogLevel = LogLevel.info, indent: int = 0) -> None: 
    if level == LogLevel.success:
        symbol = '+'
    elif level == LogLevel.info:
        symbol = '='
    elif level == LogLevel.debug:
        symbol = '*'
    elif level == LogLevel.warning:
        symbol = '!'
    elif level == LogLevel.error:
        symbol = '-'
    message = f"[{symbol}] " + ' ' * indent + message
    print(message)


def get_ssh_repo_url(user: str, httpurl: str, project: str, port: int = 22) -> str:
    pieces = httpurl.split("//")
    host = pieces[1].split(':')[0]
    sshurl = f"ssh://[git@{host}:{port}]:/{project}.git"
    return sshurl


def get_user_email(user) -> str:
    return f"{user}@lab.local"


def get_user_ssh_key_path(user, public=False, keysdir: str = "/keys") -> str:
    keypath = join(keysdir, "key")
    if public:
        keypath += ".pub"
    return keypath


def clear_repo_contents(path: str):
    for d, _, fs in walk(path, topdown=False):
        if not d.startswith(join(path, ".git/")) and d != join(path, ".git") and d != path:
            for f in fs:
                remove(join(d,f))
            rmdir(d)

def get_token(url: str, username: str, password: str) -> str:
    body = {
        "grant_type": "password",
        "username": username,
        "password": password
    }
    resp = post(url, json=body)
    token = resp.json()["access_token"]
    return token


def wait_for_token(url, username: str, password: str, delay: int = 5) -> str:
    while True:
        try:
            return get_token(url, username, password)
        except Exception as e:
            log_to_console(f"Error getting token: {e}. Retrying in {delay} seconds...", LogLevel.error)
            sleep(delay)


def create_gitlab_user(
            gitlab: Gitlab,
            username: str,
            keysdir: str = "/keys",
            indent: int = 0
        ) -> None:
    # User creation
    if checkuser := gitlab.users.list(username=username):
        user = checkuser[0]
        log_to_console(f"User {username} already exists in gitlab", LogLevel.warning, indent=indent)
    else:
        userinfo = {
            "name": username,
            "username": username,
            "email": get_user_email(username),
            # "password": str(uuid4()),
            "password": username,
            "skip_confirmation": True
        }
        user = gitlab.users.create(userinfo)
        log_to_console(f"Added user {username} to gitlab", LogLevel.success, indent=indent)
    
    # MODIFIED keys are already generated for this challenge
    # Generate ssh keypair
    #privkey = RSA.generate(2048)
    #descriptor = osopen(get_user_ssh_key_path(username, keysdir=keysdir), O_WRONLY | O_CREAT | O_TRUNC, mode=0o600)
    #with open(descriptor, 'wb') as f:
    #    f.write(privkey.export_key(format="PEM"))
    #log_to_console(f"Created private ssh key for {username}", LogLevel.success, indent=indent)
    # Add public key
    #pubkey = privkey.public_key()
    #pubkeybody = pubkey.export_key(format="OpenSSH")
    #keyinfo = {"title": f"{username}-key", "key": pubkeybody.decode()}
    #key = user.keys.create(keyinfo)
    key = user.keys.create({"title": "key", "key": open(keysdir + "/key.pub").read()})
    
    log_to_console(f"Added ssh key to {username}'s gitlab account", LogLevel.success, indent=indent)


def create_repository(
            gitlab: Gitlab,
            user: str,
            tarfile: str,
            sshport: int = 22,
            keysdir: str = "/keys",
            indent: int = 0
        ) -> None:
    # Make remote repository if it doesn't exist
    projectname = basename(tarfile).split('.')[0]
    gitlabuser = gitlab.users.list(username=user)[0]
    if matchedprojects := [p for p in gitlabuser.projects.list() if p.name == projectname]:
        project = matchedprojects[0]
        log_to_console(f"{project.path_with_namespace} project already exists in gitlab", LogLevel.warning, indent=indent)
    else:
        projectinfo = {"name": projectname}
        project = gitlabuser.projects.create(projectinfo)
        log_to_console(f"Created {project.path_with_namespace} gitlab project", LogLevel.success, indent=indent)
    projecturl = get_ssh_repo_url(user, gitlab.url, project.path_with_namespace, sshport)
    # Make tempdir
    with TemporaryDirectory() as tempdir:
        # Clone repository
        ssh_key_path = get_user_ssh_key_path(user, keysdir=keysdir)
        env = {"GIT_SSH_COMMAND": f"ssh -o StrictHostKeyChecking=no -i {ssh_key_path}"}
        # MODIFIED keys are already generated for this challenge
        #env = {"GIT_SSH_COMMAND": f"ssh -o StrictHostKeyChecking=no -i " + keysdir + "/key"}
        repo = Repo.clone_from(projecturl, tempdir, env=env)
        log_to_console(f"Cloned {project.path_with_namespace} project", LogLevel.success, indent=indent)
        clear_repo_contents(tempdir)
        # Untar contents
        with taropen(tarfile, "r:gz") as tarball:
            tarball.extractall(tempdir)
        log_to_console(f"Unpacked {tarfile}", LogLevel.success, indent=indent)
        with repo.config_writer() as config:
            config.set_value("user", "name", user)
            config.set_value("user", "email", get_user_email(user))
        with dircontext(tempdir):
            # Add, commit, and push content
            repo.git.add(all=True)
            repo.index.commit("Made some changes") #TODO better
            repo.remotes.origin.push()
            log_to_console(f"Pushed code to {project.path_with_namespace} project", LogLevel.success, indent=indent)


def main(args: Namespace):
    if not isdir(args.keysdir):
        makedirs(args.keysdir)
        log_to_console("Connecting to gitlab...")
    if args.wait_for_it:
        token = wait_for_token(f"{args.url}/oauth/token", args.username, args.password)
    else:
        token = get_token(f"{args.url}/oauth/token", args.username, args.password)
    with Gitlab(args.url, oauth_token=token) as gl:
        log_to_console("Populating users...")
        for user in args.users:
            # Create gitlab user
            try:
                create_gitlab_user(gl, user, keysdir=args.keysdir, indent=2)
            except Exception as e:
                log_to_console(f"Error adding user {user}: {e}", LogLevel.error)
        log_to_console("Populating repos")
        for tarball in listdir(args.repodir):
            # Create repos
            try:
                create_repository(
                    gl,
                    choice(args.users),
                    join(args.repodir, tarball),
                    sshport=args.gitlab_ssh_port,
                    keysdir=args.keysdir,
                    indent=2
                )
            except Exception as e:
                log_to_console(f"Error adding user {user}: {e}", LogLevel.error)
        log_to_console("Done")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("url")
    parser.add_argument("repodir")
    parser.add_argument("users", nargs="+")
    parser.add_argument("--gitlab-ssh-port", type=int, default=22)
    parser.add_argument("--keysdir", default="/keys", help="Absolute path to keys folder")
    parser.add_argument("--wait-for-it", action="store_true")
    args = parser.parse_args()
    main(args)

