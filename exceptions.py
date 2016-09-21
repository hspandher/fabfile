# inbuild python imports

# third party imports

# local imports


class DeploymentFailureException(Exception):

    pass


class GitFailureException(DeploymentFailureException):

    pass


class MergeFailedException(GitFailureException):

    error_message = "Merge failed when trying to merge {base_branch} with {target_branch}.\nDetail: {error}"

    def __init__(self, scm_branch, other_branch, error):
        self.detail = self.error_message.format(base_branch = scm_branch, target_branch = other_branch, error = error)


class IssueBranchNotFoundException(GitFailureException):

    error_message = "No branch found with issue id {issue_id}.\nDetail:- {error}"

    def __init__(self, hint, error):
        self.detail = self.error_message.format(issue_id = hint, error = error)


class PullFailedException(GitFailureException):

    error_message = "Rebase failed for {branch} branch.\n Detail: {error}"

    def __init__(self, scm_branch, error):
        self.detail = self.error_message.format(branch = scm_branch, error = error)


class FetchFailedException(GitFailureException):

    error_message = "Fetch failed. Detail: {error}"

    def __init__(self, error):
        self.detail = self.error_message.format(error = error)


class PushFailedException(GitFailureException):

    error_message = "Push into remote_branch {branch} failed.\n Detail: {error}"

    def __init__(self, scm_branch, error):
        self.detail = self.error_message.format(branch = scm_branch, error = error)


class TestFailureException(DeploymentFailureException):

    error_message = "Test/Tests failed upon merging {branch} - Detail: {error}"

    def __init__(self, argument_string, scm_branch, error):
        self.detail = self.error_message.format(branch = scm_branch, error = error)
