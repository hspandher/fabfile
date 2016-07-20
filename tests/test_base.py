import os
import contextlib
import unittest
import random
import fudge
import copy
from fabric.api import local, settings, env, sudo, lcd

from ..base import BaseDeployment, GitRepository, BranchMergeDeployment
from ..operations import FetchOperation, RebaseOperation, MergeOperation, PushOperation
from ..exceptions import MergeFailedException, PullFailedException, FetchFailedException
from ..testcases import SimpleTestCase


class TestCleanCodeRepositoryMixin(object):

    code_directory = os.path.join(os.path.dirname(__file__), 'test_deploy_dir/shine')
    remote_directory = os.path.join(os.path.dirname(__file__), 'remote_repo')
    scm_url = remote_directory
    scm_branch = 'master'
    other_branch = 'quality_assurance'
    remote_repo_backup = os.path.join(os.path.dirname(__file__), 'remote_repo_backup')

    def _pre_setup(self):
        with lcd(self.remote_repo_backup):
            local('git config --bool core.bare true')

        with lcd(self.remote_directory):
            local('git config --bool core.bare true')

    def _post_teardown(self):
        required_attrs = ['code_directory', 'remote_directory', 'remote_repo_backup']

        for required_attr in required_attrs:
            if not hasattr(self, required_attr):
                raise AttributeError("Any class that means inheriting TestCleanCodeRepositoryMixin should define `{0}` variable.".format(required_attr))

        with lcd(self.remote_repo_backup):
            local('git config --bool core.bare false')

        local("rm -Rf {0}".format(self.code_directory))
        local("rm -Rf {0}".format(self.remote_directory))
        local("cp -Rf {0} {1}".format(self.remote_repo_backup, self.remote_directory))

        super().tearDown()


class GitTestingHelperMixin(object):

    def create_local_repo(self):
        local("mkdir -p {0}".format(self.code_directory))
        local("git clone {0} {1}".format(self.remote_directory, self.code_directory))

    def get_current_branch(self):
        return local('git rev-parse --abbrev-ref HEAD', capture = True).strip()

    def get_random_commit_name(self):
        return "temp_commit_{0}".format(random.randint(1, 1000))

    def delete_file(self, base_path):
        local("rm -Rf {0}".format(os.path.join(base_path, 'sample.py')))

    def make_some_change(self, base_path):
        with open(os.path.join(base_path, 'sample.py'), 'w') as sample_file:
            sample_file.write("Hello * 10")

    def commit_changes(self, commit_name):
        local("git commit -am {0}".format(commit_name))

    def change_local_repository(self, change_method = None):
        commit_name = self.get_random_commit_name()

        with lcd(self.code_directory):
            change_method = change_method or self.make_some_change
            change_method(self.code_directory)
            self.commit_changes(commit_name)

        return commit_name

    def change_remote_repository(self, branch_name = None):
        commit_name = self.get_random_commit_name()

        with lcd(self.scm_url):
            local('git config --bool core.bare false')
            initial_branch = self.get_current_branch()

            if branch_name:
                local("git checkout {0}".format(branch_name))

            self.make_some_change(self.scm_url)

            self.commit_changes(commit_name)
            local("git checkout {0}".format(initial_branch))
            local('git config --bool core.bare true')

        return commit_name

    def make_conflicting_change(self, branch_name = None):
        self.change_local_repository(change_method = self.delete_file)
        self.change_remote_repository(branch_name)

    def commit_erroneous_change(self, repository):
        try:
            with repository.as_atomic_transaction():
                commit_name = self.change_local_repository()
                raise FetchFailedException('Temp error')
        except FetchFailedException:
            return commit_name


class TestBaseDeployment(GitTestingHelperMixin, TestCleanCodeRepositoryMixin, SimpleTestCase):

    def setUp(self):
        self.deployment = BaseDeployment(code_directory = self.code_directory, scm_url = self.scm_url, scm_branch = self.other_branch)

    def test_does_local_repo_exists_return_false_if_repo_does_not_exists(self):
        self.assertFalse(self.deployment.does_local_repo_exists())

    def test_does_local_repo_exists_return_true_if_repo_exists(self):
        local('mkdir -p {0}'.format(self.code_directory))

        self.assertTrue(self.deployment.does_local_repo_exists())

    def test_create_local_repo_if_it_does_not_exists(self):
        self.deployment.start()

        self.assertTrue(os.path.exists(self.code_directory))

    def test_allows_changing_scm_repository(self):
        dummy_repository = type('sample', (object, ), {})

        deployment = BaseDeployment(scm_url = self.scm_url, scm_branch = 'master', code_directory = self.code_directory, scm_repository_type = dummy_repository)

        self.assertEqual(deployment.scm_repository_type, dummy_repository)

    def test_updates_local_repo_if_it_already_exists(self):
        self.create_local_repo()
        commit_name = self.change_remote_repository(branch_name = self.other_branch)

        BaseDeployment(scm_url = self.scm_url, scm_branch = self.other_branch, code_directory = self.code_directory).start()

        with lcd(self.code_directory):
            recent_commit_msgs = local("git log --oneline -2", capture = True)
        self.assertIn(commit_name, recent_commit_msgs)


class TestBranchMergeDeployment(GitTestingHelperMixin, TestCleanCodeRepositoryMixin, SimpleTestCase):

    def setUp(self):
        self.deployment = BranchMergeDeployment(code_directory = self.code_directory, scm_url = self.scm_url, scm_branch = self.scm_branch, other_branch = self.other_branch)

    def test_merges_other_branch_into_current_one(self):
        commit_name = self.change_remote_repository(branch_name = self.other_branch)

        self.deployment.start()

        with lcd(self.code_directory):
            recent_commit_msgs = local("git log --oneline -2", capture = True)
        self.assertIn(commit_name, recent_commit_msgs)

    def test_merge_other_branch_with_branch_hint_works(self):
        deployment = BranchMergeDeployment(code_directory = self.code_directory, scm_url = self.scm_url, scm_branch = self.scm_branch, other_branch_hint = self.other_branch[-7:-3])
        commit_name = self.change_remote_repository(branch_name = self.other_branch)

        deployment.start()

        with lcd(self.code_directory):
            recent_commit_msgs = local("git log --oneline -2", capture = True)
        self.assertIn(commit_name, recent_commit_msgs)

    def test_push_changes_after_merging_other_branch(self):
        deployment = BranchMergeDeployment(code_directory = self.code_directory, scm_url = self.scm_url, scm_branch = self.scm_branch, other_branch_hint = self.other_branch[-7:-3])
        commit_name = self.change_remote_repository(branch_name = self.other_branch)

        deployment.start()

        with lcd(self.code_directory):
            recent_commit_msgs = local("git log origin/{} --oneline -2".format(self.scm_branch), capture = True)
        self.assertIn(commit_name, recent_commit_msgs)


class TestGitRepositoryClassMethods(TestCleanCodeRepositoryMixin, SimpleTestCase):

    def setUp(self):
        self.other_branch = 'quality_assurance'

    def test_clone_method_creates_repository(self):
        repository = GitRepository.clone(scm_url = self.scm_url, scm_branch = self.scm_branch, code_directory = self.code_directory)

        self.assertTrue(os.path.exists(self.code_directory))

    def test_automatically_checkout_out_branch_on_initialization(self):
        repository = GitRepository.clone(scm_url = self.scm_url, scm_branch = self.other_branch, code_directory = self.code_directory)

        with lcd(self.code_directory):
            current_branch = local("git branch | grep '*'", capture = True)

        self.assertIn(self.other_branch, current_branch)

    @fudge.patch(__name__ + '.' + 'GitRepository.refresh')
    def test_automatically_refreshes_branch_on_initialization(self, mock_refresh):
        mock_refresh.expects_call().times_called(1)

        repository = GitRepository.clone(scm_url = self.scm_url, scm_branch = self.other_branch, code_directory = self.code_directory)


class TestFetchOperation(TestCleanCodeRepositoryMixin, GitTestingHelperMixin, SimpleTestCase):

    def setUp(self):
        self.scm_url = os.path.join(os.path.dirname(__file__), 'remote_repo')
        self.create_local_repo()

    def test_fetch_operation_updates_origin(self):
        commit_name = self.change_remote_repository()

        FetchOperation(code_directory = self.code_directory)()

        with lcd(self.code_directory):
            last_commit_msg = local("git log origin/{} --oneline -1".format(self.scm_branch), capture = True)

        self.assertIn(commit_name, last_commit_msg)

    @fudge.patch(__name__ + '.' + 'FetchOperation.act')
    def test_raises_exception_if_fetch_fails(self, mock_fetch):
        mock_fetch.is_callable().raises(SystemExit('Mocked forced fetch failure'))

        with self.assertRaises(FetchFailedException):
            FetchOperation(code_directory = self.code_directory)()

    @fudge.patch(__name__ + '.' + 'FetchOperation.act')
    @fudge.patch(__name__ + '.' + 'FetchOperation.revert')
    def test_revert_is_being_called_when_exception_occurs(self, mock_fetch, mock_revert):
        mock_fetch.expects_call().raises(SystemExit('Mocked forced fetch failure'))
        mock_revert.expects_call().times_called(1)

        try:
            FetchOperation(code_directory = self.code_directory)()
        except BaseException:
            pass


class TestRebaseOperation(TestCleanCodeRepositoryMixin, GitTestingHelperMixin, SimpleTestCase):

    def setUp(self):
        self.scm_url = os.path.join(os.path.dirname(__file__), 'remote_repo')
        self.create_local_repo()

        self.rebase_operation = RebaseOperation(code_directory = self.code_directory, scm_branch = self.scm_branch)
        self.rebase_operation()

    def test_has_failure_exception_set(self):
        self.assertTrue(self.rebase_operation.failure_exception)


class TestMergeOperation(TestCleanCodeRepositoryMixin, GitTestingHelperMixin, SimpleTestCase):

    def setUp(self):
        self.scm_url = os.path.join(os.path.dirname(__file__), 'remote_repo')

        self.create_local_repo()

    def test_has_failure_exception_set(self):
        self.merge_operation = MergeOperation(code_directory = self.code_directory, scm_branch = self.scm_branch, other_branch = self.other_branch)
        self.merge_operation()
        self.assertTrue(self.merge_operation.failure_exception)


class TestPushOperation(TestCleanCodeRepositoryMixin, GitTestingHelperMixin, SimpleTestCase):

    def setUp(self):
        self.scm_url = os.path.join(os.path.dirname(__file__), 'remote_repo')

        self.create_local_repo()

    def test_has_failure_exception_set(self):
        self.push_operation = PushOperation(code_directory = self.code_directory, scm_branch = self.scm_branch)
        self.push_operation()
        self.assertTrue(self.push_operation.failure_exception)


class TestGitRepository(TestCleanCodeRepositoryMixin, GitTestingHelperMixin, SimpleTestCase):

    def setUp(self):
        self.scm_url = os.path.join(os.path.dirname(__file__), 'remote_repo')

        self.create_local_repo()
        self.repository = GitRepository(scm_url = self.scm_url, scm_branch = self.scm_branch, code_directory = self.code_directory)

        self.other_branch = 'quality_assurance'

    def test_refresh_repository(self):
        commit_name = self.change_remote_repository()

        self.repository.refresh()

        with lcd(self.code_directory):
            last_commit_msg = local("git log --oneline -1", capture = True)

        self.assertIn(commit_name, last_commit_msg)

    @fudge.patch(__name__ + '.' + 'FetchOperation.act')
    def test_raises_exception_if_fetch_fails(self, mock_fetch):
        mock_fetch.is_callable().raises(SystemExit('Mocked forced fetch failure'))

        with self.assertRaises(FetchFailedException):
            self.repository.refresh()

    @fudge.patch(__name__ + '.' + 'RebaseOperation.act')
    def test_raises_exception_if_refresh_fails(self, mock_rebase):
        mock_rebase.is_callable().raises(SystemExit('Mocked forced exit'))

        with self.assertRaises(PullFailedException):
            self.repository.refresh()

    def test_checkout_branch_with_existing_branch(self):
        self.repository.checkout_branch(self.other_branch)

        with lcd(self.code_directory):
            current_branch = local("git branch | grep '*'", capture = True)

        self.assertIn(self.other_branch, current_branch)

    def test_merge_another_branch_into_current_branch(self):
        commit_name = self.change_remote_repository(self.other_branch)

        self.repository.merge(other_branch = self.other_branch)

        with lcd(self.code_directory):
            recent_commit_msgs = local("git log --oneline -2", capture = True)

        self.assertIn(commit_name, recent_commit_msgs)

    def test_raises_error_if_both_scm_branch_and_branch_hint_are_missing(self):
        with self.assertRaises(ValueError):
            self.repository.merge()

    def test_raises_error_if_both_scm_branch_and_branch_hint_are_provided(self):
        with self.assertRaises(ValueError):
            self.repository.merge(other_branch = self.other_branch, other_branch_hint = self.other_branch)

    def test_raises_exception_if_merge_fails(self):
        self.make_conflicting_change(self.other_branch)

        with self.assertRaises(MergeFailedException):
            self.repository.merge(self.other_branch)

    def test_push_changes_to_the_remote_repository(self):
        commit_name = self.change_local_repository()

        self.repository.push()

        with lcd(self.remote_directory):
            last_commit_msg = local("git log --oneline -1".format(self.scm_branch), capture = True)

        self.assertIn(commit_name, last_commit_msg)

    def test_guess_branch_name(self):
        self.assertEqual(self.repository.guess_branch_name(branch_hint = self.other_branch[-8:-3]), self.other_branch)

    def test_as_atomic_transaction_reverts_changes_if_error_occurs(self):
        commit_name = self.commit_erroneous_change(self.repository)

        with lcd(self.code_directory):
            last_commit_msg = local("git log --oneline -1".format(self.scm_branch), capture = True)
        self.assertNotIn(commit_name, last_commit_msg)

    def test_deletes_tag_after_reverting(self):
        self.commit_erroneous_change(self.repository)

        with lcd(self.code_directory):
            self.assertFalse(local('git tag', capture = True).strip())

    def test_as_atomic_transaction_does_not_revert_change_if_no_error(self):
        with self.repository.as_atomic_transaction():
            commit_name = self.change_local_repository()

        with lcd(self.code_directory):
            last_commit_msg = local("git log --oneline -1".format(self.scm_branch), capture = True)
        self.assertIn(commit_name, last_commit_msg)







