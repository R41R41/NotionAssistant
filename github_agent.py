import requests
import os
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_OWNER = os.getenv('GITHUB_OWNER')
GITHUB_REPO = os.getenv('GITHUB_REPO')
PROJECT_NAME = os.getenv('PROJECT_NAME')

class GitHubAgent:
    def __init__(self):
        self.token = GITHUB_TOKEN
        self.owner = GITHUB_OWNER
        self.repo = GITHUB_REPO
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.issues_url = f'https://api.github.com/repos/{self.owner}/{self.repo}/issues'
        self.projects_url = f'https://api.github.com/repos/{self.owner}/{self.repo}/projects'
        self.graphql_url = 'https://api.github.com/graphql'

    def get_issue_number_by_title(self, title):
        response = requests.get(self.issues_url, headers=self.headers)
        if response.status_code == 200:
            issues = response.json()
            for issue in issues:
                if issue['title'] == title:
                    return issue['number']
        else:
            print(f"Failed to fetch issues: {response.status_code}")
            print(response.json())
        return None

    def update_issue_description(self, issue_number, new_description):
        update_url = f'https://api.github.com/repos/{self.owner}/{self.repo}/issues/{issue_number}'
        update_data = {'body': new_description}
        update_response = requests.patch(update_url, headers=self.headers, json=update_data)
        if update_response.status_code == 200:
            print("説明が正常に更新されました。")
            updated_issue = update_response.json()
            print(f"Issue ID: {updated_issue['id']}")
            print(f"Issue Body: {updated_issue['body']}")
        else:
            print(f"Failed to update issue: {update_response.status_code}")
            print(update_response.json())

    def get_repository_projects(self):
        query = """
        query {
            repository(owner: "%s", name: "%s") {
                projectsV2(first: 10) {
                    nodes {
                        id
                        title
                    }
                }
            }
        }
        """ % (self.owner, self.repo)

        response = requests.post(self.graphql_url, headers=self.headers, json={'query': query})
        if response.status_code == 200:
            result = response.json()
            if 'errors' in result:
                print("GraphQL errors:", result['errors'])
            else:
                projects = result['data']['repository']['projectsV2']['nodes']
                return projects
        else:
            print(f"Failed to fetch projects: {response.status_code}")
            print(response.json())

    def get_project_id(self, project_name):
        projects = self.get_repository_projects()
        for project in projects:
            if project['title'] == project_name:
                return project['id']
        print(f"Project not found: {project_name}")
        return None

    def get_project_items(self, project_id):
        query = """
        query {
            node(id: "%s") {
                ... on ProjectV2 {
                    items(first: 20) {
                        nodes {
                            id
                            content {
                                ... on Issue {
                                    title
                                    assignees(first: 10) {
                                        nodes {
                                            login
                                        }
                                    }
                                }
                                ... on PullRequest {
                                    title
                                    assignees(first: 10) {
                                        nodes {
                                            login
                                        }
                                    }
                                }
                                ... on DraftIssue {
                                    title
                                    body
                                }
                            }
                        }
                    }
                }
            }
        }
        """ % project_id

        response = requests.post(self.graphql_url, headers=self.headers, json={'query': query})
        if response.status_code == 200:
            project = response.json()
            if 'errors' in project:
                print("GraphQL errors:", project['errors'])
            else:
                items = project['data']['node']['items']['nodes']
                return items
        else:
            print(f"Failed to fetch project items: {response.status_code}")
            print(response.json())

    def get_draft_issue_id(self, project_id, item_title):
        query = """
        query {
            node(id: "%s") {
                ... on ProjectV2 {
                    items(first: 20) {
                        nodes {
                            id
                            content {
                                ... on DraftIssue {
                                    id
                                    title
                                }
                            }
                        }
                    }
                }
            }
        }
        """ % project_id

        response = requests.post(self.graphql_url, headers=self.headers, json={'query': query})
        if response.status_code == 200:
            project = response.json()
            if 'errors' in project:
                print("GraphQL errors:", project['errors'])
            else:
                items = project['data']['node']['items']['nodes']
                for item in items:
                    if 'content' in item and 'title' in item['content'] and item['content']['title'] == item_title:
                        return item['content']['id']
        else:
            print(f"Failed to fetch project items: {response.status_code}")
            print(response.json())
        return None

    def get_pbi_content(self, project_name, pbi_name):
        project_id = self.get_project_id(project_name)
        if project_id:
            items = self.get_project_items(project_id)
            for item in items:
                if item['content']['title'] == pbi_name:
                    content = item['content']['body']
                    return project_id, content
        else:
            print(f"Project not found: {project_name}")
            return None

    def update_draft_issue(self, draft_issue_id, new_title, new_body):
        mutation = """
        mutation {
            updateProjectV2DraftIssue(input: {draftIssueId: "%s", title: "%s", body: "%s"}) {
                draftIssue {
                    id
                    title
                    body
                }
            }
        }
        """ % (draft_issue_id, new_title, new_body)

        response = requests.post(self.graphql_url, headers=self.headers, json={'query': mutation})
        if response.status_code == 200:
            result = response.json()
            if 'errors' in result:
                print("GraphQL errors:", result['errors'])
            else:
                draft_issue = result['data']['updateProjectV2DraftIssue']['draftIssue']
                print(f"Draft Issue ID: {draft_issue['id']}")
                print(f"Title: {draft_issue['title']}")
                print(f"Body: {draft_issue['body']}")
        else:
            print(f"Failed to update draft issue: {response.status_code}")
            print(response.json())

    def add_comment_to_github(self, project_id, title, new_body):
        draft_issue_id = self.get_draft_issue_id(project_id, title)
        if draft_issue_id:
            self.update_draft_issue(draft_issue_id, title, new_body)
        else:
            print("Draft issue not found.")
        pass

# 使用例
if __name__ == "__main__":
    token = GITHUB_TOKEN
    owner = GITHUB_OWNER
    repo = GITHUB_REPO
    project_name = PROJECT_NAME
    print(token, owner, repo)
    # project_id = 'PVT_kwHOCG31Mc4Al6q3'
    # item_id = 'PVTI_lAHOCG31Mc4Al6q3zgRokis'
    # additional_text = "additional text"
    # new_title = "test2"

    agent = GitHubAgent()
    pbi_content = agent.get_pbi_content(project_name, "test2")
    print(pbi_content)
    