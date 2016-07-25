from .base import BranchMergeDeployment
from . import config

def qa_deploy(issue_branch_hint):
    BranchMergeDeployment(
        code_directory = config.QA_CODE_DIRECTORY,
        scm_url = config.SCM_URL,
        scm_branch = config.QA_BRANCH_NAME,
        other_branch_hint = issue_branch_hint
    ).start()

def staging_deploy(issue_branch_hint):
    BranchMergeDeployment(
        code_directory = config.STAGING_CODE_DIRECTORY,
        scm_url = config.SCM_URL,
        scm_branch = config.STAGING_BRANCH_NAME,
        other_branch_hint = issue_branch_hint
    ).start()
