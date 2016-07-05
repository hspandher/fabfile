import os
import unittest
from fabric.api import local, settings, env, sudo, lcd

from ..deploy import Deployment, GitRepository


class TestCleanCodeRepositoryMixin(object):

    code_directory = os.path.join(os.path.dirname(__file__), 'test_deploy_dir/shine')
    remote_directory = os.path.join(os.path.dirname(__file__), 'remote_repo')
    scm_url = remote_directory
    remote_repo_backup = os.path.join(os.path.dirname(__file__), 'remote_repo_backup')

    def tearDown(self):
        required_attrs = ['code_directory', 'remote_directory', 'remote_repo_backup']

        for required_attr in required_attrs:
            if not hasattr(self, required_attr):
                raise AttributeError("Any class that means inheriting TestCleanCodeRepositoryMixin should define `{0}` variable.".format(required_attr))

        local("rm -Rf {0}".format(self.code_directory))
        local("rm -Rf {0}".format(self.remote_directory))
        local("cp -Rf {0} {1}".format(self.remote_repo_backup, self.remote_directory))

        super(TestCleanCodeRepositoryMixin, self).tearDown()


class TestDeployment(TestCleanCodeRepositoryMixin, unittest.TestCase):

    def setUp(self):
        super(TestDeployment, self).setUp()

        self.deployment = Deployment(scm_url = self.scm_url, code_directory = self.code_directory)

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

        deployment = Deployment(scm_url = self.scm_url, code_directory = self.code_directory, scm_repository_type = dummy_repository)

        self.assertEqual(deployment.scm_repository_type, dummy_repository)


class TestGitRepositoryClassMethods(TestCleanCodeRepositoryMixin, unittest.TestCase):

    def test_clone_method_creates_repository(self):
        repository = GitRepository.clone(scm_url = self.scm_url, code_directory = self.code_directory)

        self.assertTrue(os.path.exists(self.code_directory))


class TestGitRepository(TestCleanCodeRepositoryMixin, unittest.TestCase):

    def setUp(self):
        self.scm_url = os.path.join(os.path.dirname(__file__), 'remote_repo')

        self.repository = GitRepository.clone(scm_url = self.scm_url, code_directory = self.code_directory)

    def test_refresh_repository(self):
        with open(os.path.join(self.scm_url, 'sample.py'), 'w') as sample_file:
            sample_file.write("Hello * 10")
        with lcd(self.scm_url):
            local("git commit -am temp_commit")

        self.repository.refresh()

        with lcd(self.code_directory):
            last_commit_msg = local("git log --oneline -1", capture = True)

        self.assertIn('temp_commit', last_commit_msg)




