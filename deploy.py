# inbuild python imports
import datetime
import requests

# third party imports
from fabric.api import local, settings, lcd, sudo, env

# local imports
from . import exceptions


code_directory = 'deploy_data/shinecandidate'
repository_origin = 'https://hspandher:punit1988@github.com/firefly-eventures/shinecandidate.git'
qa_deploy_url = 'http://hspandher:67ce59d90c9c3e3b47cd83d9b80684a0@localhost:8080/job/quality_assurance/buildWithParameters'

def error(operation):
    return operation.stdout or operation.stderr

def tag_branch(branch_name):
    tag_name = datetime.datetime.now().strftime("%d-%m-%y-%H-%M-%s")

    local("git tag {0}".format(tag_name))

    return tag_name

def revert(tag_name):
    local("git reset --hard {0}".format(tag_name))

def clone_directory(branch_name):
    with settings(warn_only = True):
        branch_exists = local("test -d {0}".format(code_directory))

    if branch_exists.failed:
        local("mkdir -p {0}".format(code_directory))
        local("git clone {0} {1}".format(repository_origin, code_directory))

def fetch_branch(branch_name):
    with settings(warn_only = True):
        with lcd(code_directory):
            local('git checkout -f')
            fetch = local('git fetch')

            with settings(warn_only = True):
                checkout = local("git checkout {0}".format(branch_name))

            if checkout.failed:
                create_branch = local("git checkout -b {0}".format(branch_name))

            with settings(warn_only = True):
                merge = local('git merge origin {0}'.format(branch_name), capture = True)

            if merge.failed:
                local('git checkout -f')
                raise exceptions.PullFailedException(branch_name, error(rebase))


    return True

def merge(source_branch, issue_branch):
    with settings(warn_only = True):
        merge = local("git merge origin/{0}".format(issue_branch), capture = True)

    if merge.failed:
        local('git checkout -f')

        raise exceptions.MergeFailedException(source_branch, issue_branch, error(merge))

def get_issue_branch(issue_id):
    with settings(warn_only = True):
        branch_name_guess = local("git remote show origin | grep {0}".format(issue_id), capture = True)

    if branch_name_guess.failed:
        raise exceptions.IssueBranchNotFoundException(issue_id, error(branch_name_guess))

    return branch_name_guess.strip().split(' ')[0]

def test():
    with settings(warn_only = True):
        test_status = local("py.test .", capture = True)

    if test_status.failed:
        print "Test Status: {0}".format(error(test_status))

def push(current_branch):
    local("git push origin {0}".format(current_branch))

def change_permissions():
    local("chmod -R u+w .")

def with_tagging(func):
    def wrapper(source_branch, issue_id, *args, **kwargs):
        with settings(user = 'jenkins'):
            clone_directory(source_branch)
            with lcd(code_directory):
                tag_name = tag_branch(source_branch)

            try:
                return func(source_branch, issue_id, *args, **kwargs)
            except Exception as exp:
                with lcd(code_directory):
                    revert(tag_name)
                raise exp

    return wrapper

def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (exceptions.IssueBranchNotFoundException, exceptions.MergeFailedException, exceptions.PullFailedException) as exp:
            print("Deployment failed - {0}".format(exp.message))

            raise exp

    return wrapper

@with_tagging
@handle_exceptions
def deploy(source_branch, issue_id):
    with settings(user = 'jenkins'):
        fetch_branch(source_branch)

        with lcd(code_directory):
            issue_branch = get_issue_branch(issue_id)
            merge(source_branch, issue_branch)
            push(source_branch)


class GitRepository(object):

    @classmethod
    def clone(cls, scm_url, code_directory):
        local("mkdir -p {0}".format(code_directory))
        local("git clone {0} {1}".format(scm_url, code_directory))

        return cls(scm_url, code_directory)

    def __init__(self, scm_url, code_directory):
        self.scm_url = scm_url
        self.code_directory = code_directory

    def refresh(self):
        with lcd(self.code_directory):
            local("git fetch")
            local("git rebase")


class Deployment(object):

    scm_repository_type = GitRepository

    def __init__(self, code_directory, scm_url, scm_repository_type = None):
        self.code_directory = code_directory
        self.scm_url = scm_url
        self.scm_repository_type = scm_repository_type or self.scm_repository_type

    def does_local_repo_exists(self):
        with settings(warn_only = True):
            repo_exists = local("test -d {0}".format(self.code_directory))

        return not repo_exists.failed

    def start(self):
        if not self.does_local_repo_exists():
            self.scm_repository_type.clone(self.scm_url, self.code_directory)
