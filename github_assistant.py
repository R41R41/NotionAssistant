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

prompt_file_path = './test/prompt.txt'
md_file_path = './test/page_content.md'
diff_file_path = './test/page_content_diff.md'


class GitHubAssistant:
    def __init__(self, project_name, pbi_name, prompt_file_path, md_file_path, diff_file_path, auto_mode=True):
        self.github_agent = GitHubAgent()
        self.llm_agent = LLMAgent()
        self.markdown_agent = MarkdownAgent(md_file_path=md_file_path)
        self.project_name = project_name
        self.pbi_name = pbi_name
        self.project_id = None
        self.prompt_file_path = prompt_file_path
        self.md_file_path = md_file_path
        self.diff_file_path = diff_file_path
        self.auto_mode = auto_mode
        self.previous_md_content = None
        self.present_md_content = None
        self.saved_md_content = None
        self.is_updated = False
        self.last_update_time = None
        self.prompt = None
        self.diff_content = None
        with open(self.prompt_file_path, 'r', encoding='utf-8') as file:
            self.prompt = file.read()

    def save_to_file(self, markdown_content, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

    async def assist_github(self):
        print("LLMに送信します。")
        llm_response = await self.llm_agent(system_message=self.prompt, human_message=self.diff_content)
        # コメントを追加
        comments = json.loads(llm_response)
        print(f"コメント: {comments}")
        self.new_md_content = self.markdown_agent.get_content_with_ai_feedback(
            self.present_md_content, comments)
        self.github_agent.add_comment_to_github(
            self.project_id, self.pbi_name, self.new_md_content)
        print(f"ページの中身が保存され、コメントが追加されました。最終更新日時: {
            self.last_update_time}")

    def remove_user_input(self, markdown_content):
        lines = markdown_content.split('\n')
        for i, line in enumerate(lines):
            if "user:" in line and not "!user:" in line:
                lines[i] = line.replace("user:", "!user:")
        return '\n'.join(lines)

    def contains_unmarked_user_input(self, markdown_content):
        return "user:" in markdown_content and "!user:" not in markdown_content

    async def run_schedule(self):
        project_id, previous_markdown_content = self.github_agent.get_pbi_content(
            project_name=self.project_name, pbi_name=self.pbi_name)
        self.project_id = project_id
        self.previous_md_content = self.markdown_agent.get_content_without_ai_feedback(
            previous_markdown_content)
        self.save_to_file(self.previous_md_content, self.md_file_path)
        self.saved_md_content = self.previous_md_content
        self.is_updated = False
        self.last_update_time = time.time()
        print("ページ更新検知開始")
        while True:
            await self.fetch_and_save_content()
            time.sleep(1)

    async def fetch_and_save_content(self):
        try:
            _, markdown_content = self.github_agent.get_pbi_content(
                project_name=self.project_name, pbi_name=self.pbi_name)
            self.present_md_content = self.markdown_agent.get_content_without_ai_feedback(
                markdown_content)
            if not self.present_md_content:
                print("ページが見つかりませんでした。")
                return
            if self.present_md_content != self.previous_md_content:
                print("ページが更新されました。")
                self.is_updated = True
                # 変化があった場合、更新時間を記録
                self.previous_md_content = self.present_md_content
                self.last_update_time = time.time()
            elif self.auto_mode and self.is_updated and time.time() - self.last_update_time >= 3:
                # 3秒間変化がなかった場合、保存してLLMに送信
                self.diff_content = self.markdown_agent.get_diff_to_file(
                    self.saved_md_content, self.present_md_content)
                self.saved_md_content = self.present_md_content
                self.save_to_file(self.present_md_content, self.md_file_path)
                self.save_to_file(self.diff_content, self.diff_file_path)
                await self.assist_github()
                self.is_updated = False
        except Exception as e:
            print(e)

auto_mode = True
project_name = "test"
pbi_name = "ユーザーニーズ調査を実施"
# 非同期関数を実行するためのエントリーポイント
github_assistant = GitHubAssistant(project_name, pbi_name, prompt_file_path, md_file_path, diff_file_path, auto_mode)
asyncio.run(github_assistant.run_schedule())
