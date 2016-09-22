from .base import BranchMergeDeployment
from .configuration import config
from .handlers import DeploymentStatusHandler

SUCCESS_MESSAGE = "Deployment of issue {issue_id} on {branch_name} branch successful."
FAILURE_MESSAGE = "Deployment of issue {issue_id} on {branch_name} branch failed."

def qa_deploy(issue_id, old_assignee_email, new_assignee_email):
    success_message = SUCCESS_MESSAGE.format(issue_id = issue_id, branch_name = 'Quality Assurance')
    failure_message = FAILURE_MESSAGE.format(issue_id = issue_id, branch_name = 'Quality Assurance')

    with DeploymentStatusHandler(issue_id, old_assignee_email, new_assignee_email, success_message, failure_message, old_status = 'new', new_status = 'resolved'):
        BranchMergeDeployment(
            code_directory = config.QA_CODE_DIRECTORY,
            scm_url = config.SCM_URL,
            scm_branch = config.QA_BRANCH_NAME,
            other_branch_hint = issue_branch_hint
        ).start()

def staging_deploy(issue_id, old_assignee_email, new_assignee_email):
    success_message = SUCCESS_MESSAGE.format(issue_id = issue_id, branch_name = 'Staging')
    failure_message = FAILURE_MESSAGE.format(issue_id = issue_id, branch_name = 'Staging')

    with DeploymentStatusHandler(issue_id, old_assignee_email, new_assignee_email, success_message, failure_message, old_status = 'resolved', new_status = 'verified'):
        BranchMergeDeployment(
            code_directory = config.STAGING_CODE_DIRECTORY,
            scm_url = config.SCM_URL,
            scm_branch = config.STAGING_BRANCH_NAME,
            other_branch_hint = issue_branch_hint
        ).start()
