# inbuild python imports

# third party imports
from fabric.api import local, settings, lcd

# local imports
from . import exceptions


code_directory = 'deploy_data/shinedjango'

def error(operation):
    return operation.stdout or operation.stderr

def fetch_branch(branch_name):
    with settings(warn_only = True):
        if local("test -d {0}".format(code_directory)).failed:
            local("git clone https://github.com/hspandher/continuous_integration_testing.git {0}".format(code_directory))

        with lcd(code_directory):
            with settings(warn_only = True):
                rebase = local('git pull --rebase origin {0}'.format(branch_name), capture = True)

            if rebase.failed:
                local('git rebase --abort')
                return False

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

def deploy(issue_id):
    source_branch = 'master'

    fetch_branch(source_branch)

    with lcd(code_directory):
        issue_branch = get_issue_branch(issue_id)
        merge(source_branch, issue_branch)
        test()
        push(source_branch)



