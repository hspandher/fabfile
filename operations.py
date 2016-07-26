from fabric.api import local, settings, lcd

from . import exceptions
from .common import executor


class GitOperation(object):

    def __init__(self, code_directory, **parameters):
        self.code_directory = code_directory
        self.parameters = parameters

    def __call__(self):
        with executor.cd(self.code_directory):
            return self.operate()

    def operate(self):
        try:
            return self.act()
        except SystemExit as exp:
            with settings(warn_only = True):
                self.revert()
            raise self.failure_exception(**self.get_exception_params(exp))

    def get_exception_params(self, exception):
        return dict(self.parameters, **{'error': str(exception)})

    def revert(self):
        pass


class FetchOperation(GitOperation):

    failure_exception = exceptions.FetchFailedException

    def act(self):
        executor.run('git fetch')


class RebaseOperation(GitOperation):

    failure_exception = exceptions.PullFailedException

    def act(self):
        executor.run("git rebase origin/{0}".format(self.parameters['scm_branch']))

    def revert(self):
        executor.run('git rebase --abort')


class MergeOperation(GitOperation):

    failure_exception = exceptions.MergeFailedException

    def act(self):
        executor.run("git merge --no-edit origin/{0}".format(self.parameters['other_branch']))

    def revert(self):
        executor.run('git checkout -f')


class PushOperation(GitOperation):

    failure_exception = exceptions.PushFailedException

    def act(self):
        executor.run("git push origin {0}".format(self.parameters['scm_branch']))


class BranchNameGuessOperation(GitOperation):

    failure_exception = exceptions.IssueBranchNotFoundException

    def act(self):
        guess = executor.run("git remote show origin | grep {0}".format(self.parameters['hint']), capture = True)

        return guess.strip().split(' ')[0]


class TagOperation(GitOperation):

    failure_exception = exceptions.GitFailureException

    def act(self):
        executor.run("git tag {0}".format(self.parameters['tag_name']))


class RevertTagOperation(GitOperation):

    failure_exception = exceptions.GitFailureException

    def act(self):
        executor.run("git reset --hard {0}".format(self.parameters['tag_name']))


class DeleteTagOperation(GitOperation):

    failure_exception = exceptions.GitFailureException

    def act(self):
        executor.run("git tag -d {0}".format(self.parameters['tag_name']))
