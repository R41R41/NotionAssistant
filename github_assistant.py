import os
import time
import asyncio
import json
from github_agent import GitHubAgent
from markdown_agent import MarkdownAgent
from llm_agent import LLMAgent
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

assist_updated_task_prompt_file_path = './prompt/assist_updated_task_prompt.txt'
assist_created_task_prompt_file_path = './prompt/assist_created_task_prompt.txt'
pbi_format_file_path = './prompt/pbi_format.txt'
projects_path = './projects'

class GitHubAssistant:
    def __init__(self, project_name):
        self.github_agent = GitHubAgent()
        self.llm_agent = LLMAgent()
        self.markdown_agent = MarkdownAgent(projects_path=projects_path, project_name=project_name)
        self.project_name = project_name
        self.project_id = self.github_agent.get_project_id()
        self.tasks_update_status = []
        self.diff_content = []
        with open(assist_updated_task_prompt_file_path, 'r', encoding='utf-8') as file:
            self.assist_updated_task_prompt = file.read()
        with open(assist_created_task_prompt_file_path, 'r', encoding='utf-8') as file:
            self.assist_created_task_template = file.read()
        with open(pbi_format_file_path, 'r', encoding='utf-8') as file:
            self.pbi_format = file.read()
        self.project_short_description = self.github_agent.get_project_short_description()

    def save_to_file(self, markdown_content, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

    async def assist_updated_task(self, title,present_md_content,previous_md_content):
        diff_content = self.markdown_agent.get_diff_content(previous_md_content, present_md_content)
        human_message = f"PBI名: {title}\nプロジェクトの概要: {self.project_short_description}\nPBIの内容: {present_md_content}\n前回からの差分: {diff_content}"
        print("LLMに送信します。")
        llm_response = await self.llm_agent(system_message=self.assist_updated_task_prompt, human_message=human_message)
        # コメントを追加
        comments = json.loads(llm_response)
        new_md_content = self.markdown_agent.get_content_with_ai_feedback(
            present_md_content, comments)
        if new_md_content:
            self.github_agent.add_comment_to_github(
                self.project_id, title, new_md_content)
            print(f"PBI「{title}」にコメントが追加されました。")

    async def assist_created_task(self, title):
        human_message = f"PBI名: {title}\nプロジェクトの概要: {self.project_short_description}\nPBIのフォーマット: {self.pbi_format}"
        print("LLMに送信します。")
        llm_response = await self.llm_agent(system_message=self.assist_created_task_template, human_message=human_message)
        self.github_agent.add_comment_to_github(
            self.project_id, title, llm_response)
        print(f"PBI「{title}」にコメントが追加されました。")
        
    def remove_user_input(self, markdown_content):
        lines = markdown_content.split('\n')
        for i, line in enumerate(lines):
            if "user:" in line and not "!user:" in line:
                lines[i] = line.replace("user:", "!user:")
        return '\n'.join(lines)

    def contains_unmarked_user_input(self, markdown_content):
        return "user:" in markdown_content and "!user:" not in markdown_content

    def init_update_status(self):
        for task in self.tasks_update_status:
            task['is_updated'] = False
            task['is_created'] = False
            task["is_deleted"] = False

    def update_status(self):
        tasks_update_status = self.github_agent.get_project_items_updateAt()  
        for task in tasks_update_status:
            is_created = True
            for existing_task in self.tasks_update_status:
                if existing_task["id"] == task["id"]:
                    is_created = False
                    if task['updatedAt'] != existing_task['updatedAt']:
                        existing_task['is_updated'] = True
                    break
            if is_created:
                task['is_created'] = True
                self.tasks_update_status.append(task)
        # 削除されたタスクを検出
        for existing_task in self.tasks_update_status:
            if not any(task["id"] == existing_task["id"] for task in tasks_update_status):
                existing_task["is_deleted"] = True
        return

    async def run_schedule(self):
        # プロジェクトの初期状態を取得
        project_items = self.github_agent.get_project_items_body()
        # プロジェクトの初期状態を保存
        self.markdown_agent.save_project_items(
            project_items=project_items)
        # プロジェクト各タスクの更新日時を取得
        self.tasks_update_status = self.github_agent.get_project_items_updateAt()
        print("ページ更新検知開始")
        while True:
            await self.detect_update()
            time.sleep(1)

    async def detect_update(self):
        try:
            self.update_status()
            project_items = self.github_agent.get_project_items_body()
            for task in self.tasks_update_status:
                if task["is_deleted"]:
                    print(f"PBI「{task['title']}」が削除されました。{task['updatedAt']}")
                    self.markdown_agent.delete_project_item(task['id'])
                    self.tasks_update_status.remove(task)
                elif task["is_created"]:
                    item = next((item for item in project_items if item['id'] == task['id']), None)
                    if item:
                        if item['body'] == "":
                            print(f"PBI「{task['title']}」が作成されました。{task['updatedAt']}")
                            await self.assist_created_task(title=item['title'])
                        else:
                            present_md_content = self.markdown_agent.get_content_without_ai_feedback(item['body'])
                            previous_md_content = self.markdown_agent.get_saved_content(item['id'])
                            if present_md_content != previous_md_content:
                                print(f"PBI「{item['title']}」が更新されました。{task['updatedAt']}")
                                await self.assist_updated_task(title=item['title'],present_md_content=present_md_content,previous_md_content=previous_md_content)
                    else:
                        print(f"ID {task['id']} に一致するアイテムが見つかりませんでした。")
                        continue
                elif task["is_updated"]:
                    item = next((item for item in project_items if item['id'] == task['id']), None)
                    if item:
                        present_md_content = self.markdown_agent.get_content_without_ai_feedback(item['body'])
                        previous_md_content = self.markdown_agent.get_saved_content(item['id'])
                        if present_md_content != previous_md_content:
                            print(f"PBI「{item['title']}」が更新されました。{task['updatedAt']}")
                            await self.assist_updated_task(title=item['title'],present_md_content=present_md_content,previous_md_content=previous_md_content)
                    else:
                        print(f"ID {task['id']} に一致するアイテムが見つかりませんでした。")
                        continue
            self.markdown_agent.save_project_items(
                project_items=project_items)
            self.init_update_status()
        except Exception as e:
            print(e)

project_name = "test"
# 非同期関数を実行するためのエントリーポイント
github_assistant = GitHubAssistant(project_name)
asyncio.run(github_assistant.run_schedule())
