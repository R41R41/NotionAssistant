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
        self.project_name = PROJECT_NAME
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.issues_url = f'https://api.github.com/repos/{self.owner}/{self.repo}/issues'
        self.projects_url = f'https://api.github.com/repos/{self.owner}/{self.repo}/projects'
        self.graphql_url = 'https://api.github.com/graphql'

    def get_repository_projects(self):
        query = """
        query {
            repository(owner: "%s", name: "%s") {
                projectsV2(first: 10) {
                    nodes {
                        id
                        title
                        shortDescription
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

    def get_project_short_description(self):
        projects = self.get_repository_projects()
        for project in projects:
            if project['title'] == self.project_name:
                return project['shortDescription']
        print(f"Project not found: {self.project_name}")
        return None

    def get_project_id(self):
        projects = self.get_repository_projects()
        for project in projects:
            if project['title'] == self.project_name:
                return project['id']
        print(f"Project not found: {self.project_name}")
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
                                    updatedAt
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

    def get_project_items_updateAt(self):
        project_id = self.get_project_id()
        if project_id:
            items = self.get_project_items(project_id)
            if items:
                update_status = []
                for item in items:
                    update_status.append({
                        'id': item['id'],
                        'title': item['content']['title'],
                        'updatedAt': item['content']['updatedAt'],
                        'is_updated': False,
                        'is_created': False,
                        'is_deleted': False
                    })
                return update_status
            else:
                print(f"No items found in project: {self.project_name}")
                return None
        else:
            print(f"Project not found: {self.project_name}")
            return None

    def get_project_items_body(self):
        project_id = self.get_project_id()
        if project_id:
            items = self.get_project_items(project_id)
            if items:
                items_body = []
                for item in items:
                    items_body.append({
                        'id': item['id'],
                        'title': item['content']['title'],
                        'body': item['content']['body']
                    })
                return items_body
            else:
                print(f"No items found in project: {self.project_name}")
                return None
        else:
            print(f"Project not found: {self.project_name}")
            return None

    def get_pbi_content(self, pbi_name):
        project_id = self.get_project_id()
        if project_id:
            items = self.get_project_items(project_id)
            for item in items:
                if item['content']['title'] == pbi_name:
                    content = item['content']['body']
                    return project_id, content
        else:
            print(f"Project not found: {self.project_name}")
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
    id = agent.get_project_id()
    items = agent.get_project_items(id)
    print(items)
    # pbi_content = agent.get_pbi_content(project_name, "ユーザーニーズ調査を実施")
    # print(pbi_content)
    