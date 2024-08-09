import requests

class GitHubAgent:
    def __init__(self, token, owner, repo):
        self.token = token
        self.owner = owner
        self.repo = repo
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

    def get_repository_projects(self, owner, repo):
        query = """
        query {
            repository(owner: "%s", name: "%s") {
                projectsV2(first: 20) {
                    nodes {
                        id
                        title
                        url
                    }
                }
            }
        }
        """ % (owner, repo)

        response = requests.post(self.graphql_url, headers=self.headers, json={'query': query})
        if response.status_code == 200:
            projects = response.json()
            if 'errors' in projects:
                print("GraphQL errors:", projects['errors'])
            else:
                project_ids = []
                for project in projects['data']['repository']['projectsV2']['nodes']:
                    print(f"Project ID: {project['id']}")
                    print(f"Project Title: {project['title']}")
                    print(f"Project URL: {project['url']}")
                    print('---')
                    project_ids.append(project['id'])
                return project_ids
        else:
            print(f"Failed to fetch projects: {response.status_code}")
            print(response.json())
        return []

    def get_project_v2_details(self, project_id):
        query = """
        query {
            node(id: "%s") {
                ... on ProjectV2 {
                    id
                    title
                    url
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
                project_data = project['data']['node']
                print(f"Project ID: {project_data['id']}")
                print(f"Project Title: {project_data['title']}")
                print(f"Project URL: {project_data['url']}")
        else:
            print(f"Failed to fetch project details: {response.status_code}")
            print(response.json())

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
                for item in items:
                    print(f"Item ID: {item['id']}")
                    if 'title' in item['content']:
                        print(f"Title: {item['content']['title']}")
                    if 'body' in item['content']:
                        print(f"Body: {item['content']['body']}")
                    if 'assignees' in item['content']:
                        assignees = item['content']['assignees']['nodes']
                        assignee_logins = [assignee['login'] for assignee in assignees]
                        print(f"Assignees: {', '.join(assignee_logins)}")
                    print('---')
        else:
            print(f"Failed to fetch project items: {response.status_code}")
            print(response.json())

    def update_project_body(self, project_id, additional_text):
        # プロジェクトの詳細を取得
        print(project_id)
        project_url = f'https://api.github.com/projects/{project_id}'
        response = requests.get(project_url, headers=self.headers)
        if response.status_code == 200:
            project = response.json()
            print(project)
            current_body = project.get('body', '')
            updated_body = current_body + "\n" + additional_text

            # プロジェクトのBodyを更新
            update_data = {'body': updated_body}
            update_response = requests.patch(project_url, headers=self.headers, json=update_data)
            if update_response.status_code == 200:
                print("プロジェクトのBodyが正常に更新されました。")
                updated_project = update_response.json()
                print(f"Updated Project Body: {updated_project['body']}")
            else:
                print(f"Failed to update project body: {update_response.status_code}")
                print(update_response.json())
        else:
            print(f"Failed to fetch project details: {response.status_code}")
            print(response.json())

# 使用例
if __name__ == "__main__":
    token = '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'
    owner = 'R41R41'
    repo = 'NotionAssistant'

    agent = GitHubAgent(token, owner, repo)
    project_ids = agent.get_repository_projects(owner, repo)
    for project_id in project_ids:
        agent.get_project_items(project_id)
        agent.update_project_body(project_id, "追加するテキスト")