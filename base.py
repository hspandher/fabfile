# inbuild python imports
import datetime
import operator
import requests
import contextlib

# third party imports
from fabric.api import local, settings, lcd, sudo, env

# local imports
from . import exceptions
from .common import executor
from .operations import FetchOperation, RebaseOperation, MergeOperation, PushOperation, BranchNameGuessOperation, TagOperation, RevertTagOperation, DeleteTagOperation


class AtomicTransaction(object):

    def __init__(self, code_directory, tag_operation, revert_tag_operation, delete_tag_operation):
        self.code_directory = code_directory
        self.tag_operation = tag_operation
        self.revert_tag_operation = revert_tag_operation
        self.delete_tag_operation = delete_tag_operation

    def __enter__(self):
        self.tag_name = datetime.datetime.now().strftime("%d-%m-%y-%H-%M-%s")
        self.tag_operation(self.code_directory, tag_name = self.tag_name)()

    def __exit__(self, type, value, traceback):
        if isinstance(value, BaseException):
            self.revert_tag_operation(self.code_directory, tag_name = self.tag_name)()
            self.delete_tag_operation(self.code_directory, tag_name = self.tag_name)()


class GitRepository(object):

    @classmethod
    def clone(cls, code_directory, scm_url, scm_branch):
        executor.run("mkdir -p {0}".format(code_directory))
        executor.run("git clone {0} {1}".format(scm_url, code_directory))

        return cls(code_directory, scm_url, scm_branch)

    def __init__(self, code_directory, scm_url, scm_branch):
        self.code_directory = code_directory
        self.scm_url = scm_url
        self.scm_branch = scm_branch

        self.checkout_branch(self.scm_branch)
        self.refresh()

    def guess_branch_name(self, branch_hint):
        return BranchNameGuessOperation(self.code_directory, hint = branch_hint)()

    def refresh(self):
        FetchOperation(self.code_directory)()
        RebaseOperation(self.code_directory, scm_branch = self.scm_branch)()

    def checkout_branch(self, branch_name):
        with executor.cd(self.code_directory):
            executor.run("git checkout -f {0}".format(branch_name))

    def merge(self, other_branch = None, other_branch_hint = None):
        if not operator.xor(bool(other_branch), bool(other_branch_hint)):
            raise ValueError("One and only one of the `other_branch` and `other_branch_hint` must be provided.")

        self.refresh()
        other_branch = other_branch or self.guess_branch_name(other_branch_hint)

        MergeOperation(self.code_directory, scm_branch = self.scm_branch, other_branch = other_branch)()

    def push(self):
        PushOperation(self.code_directory, scm_branch = self.scm_branch)()

    def as_atomic_transaction(self):
        return AtomicTransaction(self.code_directory, tag_operation = TagOperation, revert_tag_operation = RevertTagOperation, delete_tag_operation = DeleteTagOperation)


class BaseDeployment(object):

    scm_repository_type = GitRepository

    def __init__(self, code_directory, scm_url, scm_branch, scm_repository_type = None):
        self.code_directory = code_directory
        self.scm_url = scm_url
        self.scm_branch = scm_branch
        self.scm_repository_type = scm_repository_type or self.scm_repository_type

    def does_local_repo_exists(self):
        with settings(warn_only = True):
            repo_exists = executor.run("test -d {0}".format(self.code_directory))

        return not repo_exists.failed

    def initialize_repo(self):
        repo_initializer = self.scm_repository_type if self.does_local_repo_exists() else self.scm_repository_type.clone

        return repo_initializer(
            code_directory = self.code_directory,
            scm_url = self.scm_url,
            scm_branch =  self.scm_branch
        )

    def start(self):
        return self.initialize_repo()


class BranchMergeDeployment(BaseDeployment):

    def __init__(self, code_directory, scm_url, scm_branch, other_branch = None, other_branch_hint = None, scm_repository_type = None):
        super().__init__(code_directory, scm_url, scm_branch, scm_repository_type)

        self.other_branch = other_branch
        self.other_branch_hint = other_branch_hint

    def start(self):
        repo = super().start()

        with repo.as_atomic_transaction():
            repo.merge(other_branch = self.other_branch, other_branch_hint = self.other_branch_hint)
            repo.push()
