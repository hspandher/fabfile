from fabric.api import local, settings, lcd

from . import exceptions


class GitOperation(object):

    def __init__(self, code_directory, **parameters):
        self.code_directory = code_directory
        self.parameters = parameters

    def __call__(self):
        with lcd(self.code_directory):
            return self.operate()

    def operate(self):
        try:
            return self.act()
        except SystemExit as exp:
            with settings(warn_only = True):
                self.revert()
            raise self.failure_exception(**self.get_exception_params(exp))

    def get_exception_params(self, exception):
        return dict(self.parameters, **{'error': exception.message})

    def revert(self):
        pass


class FetchOperation(GitOperation):

    failure_exception = exceptions.FetchFailedException

    def act(self):
        local('git fetch')


class RebaseOperation(GitOperation):

    failure_exception = exceptions.PullFailedException

    def act(self):
        local("git rebase origin/{0}".format(self.parameters['scm_branch']))

    def revert(self):
        local('git rebase --abort')


class MergeOperation(GitOperation):

    failure_exception = exceptions.MergeFailedException

    def act(self):
        local("git merge --no-edit origin/{0}".format(self.parameters['other_branch']))

    def revert(self):
        local('git checkout -f')


class PushOperation(GitOperation):

    failure_exception = exceptions.PushFailedException

    def act(self):
        local("git push origin {0}".format(self.parameters['scm_branch']))


class BranchNameGuessOperation(GitOperation):

    failure_exception = exceptions.IssueBranchNotFoundException

    def act(self):
        guess = local("git remote show origin | grep {0}".format(self.parameters['hint']), capture = True)

        return guess.strip().split(' ')[0]
