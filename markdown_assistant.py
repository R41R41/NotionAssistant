import os
import time
import asyncio
import json
from markdown_agent import MarkdownAgent
from llm_agent import LLMAgent
from dotenv import load_dotenv
import pytz
from datetime import datetime

tokyo_tz = pytz.timezone('Asia/Tokyo')


load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

prompt_file_path = './test/prompt.txt'
md_file_path = './test/page_content.md'
diff_file_path = './test/page_content_diff.md'


class MarkdownAssistant:
    def __init__(self, openai_api_key, input_md_file_path, prompt_file_path, md_file_path, diff_file_path, auto_mode=True):
        self.markdown_agent = MarkdownAgent(md_file_path=md_file_path)
        self.llm_agent = LLMAgent()
        self.input_md_file_path = input_md_file_path
        self.prompt_file_path = prompt_file_path
        self.md_file_path = md_file_path
        self.diff_file_path = diff_file_path
        self.auto_mode = auto_mode
        self.previous_md_content = None
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

    async def assist_markdown(self):
        print("LLMに送信します。")
        llm_response = await self.llm_agent(system_message=self.prompt, human_message=self.diff_content)
        # コメントを追加
        comments = json.loads(llm_response)
        self.markdown_agent.clear_ai_feedback()
        print(f"コメント: {comments}")
        self.new_md_content = self.markdown_agent.get_content_with_ai_feedback(
            self.present_md_content, comments)
        self.save_to_file(self.new_md_content, self.input_md_file_path)
        tokyo_time = datetime.fromtimestamp(
            self.last_update_time, tokyo_tz).strftime('%Y-%m-%d %H:%M:%S')
        print(f"ページの中身が保存され、コメントが追加されました。最終更新日時: {tokyo_time} (東京の時間)")

    def remove_user_input(self, markdown_content):
        lines = markdown_content.split('\n')
        for i, line in enumerate(lines):
            if "user:" in line and not "!user:" in line:
                lines[i] = line.replace("user:", "!user:")
        return '\n'.join(lines)

    def contains_unmarked_user_input(self, markdown_content):
        return "user:" in markdown_content and "!user:" not in markdown_content

    async def run_schedule(self):
        previous_markdown_content = self.markdown_agent.get_file_content(
            md_file_path=self.input_md_file_path)
        self.previous_md_content = self.markdown_agent.get_content_without_ai_feedback(
            previous_markdown_content)
        self.saved_md_content = self.previous_md_content
        self.save_to_file(self.previous_md_content, self.md_file_path)
        self.is_updated = False
        self.last_update_time = time.time()
        print(f"ページ更新検知開始 自動モード:{self.auto_mode}")
        while True:
            await self.fetch_and_save_content()
            await asyncio.sleep(1)

    async def fetch_and_save_content(self):
        try:
            markdown_content = self.markdown_agent.get_file_content(
                md_file_path=self.input_md_file_path)
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
            elif self.auto_mode and self.is_updated and time.time() - self.last_update_time >= 1:
                # 1秒間変化がなかった場合、保存してLLMに送信
                self.diff_content = self.markdown_agent.get_diff_to_file(
                    self.saved_md_content, self.present_md_content)
                self.saved_md_content = self.present_md_content
                await self.assist_markdown()
                self.save_to_file(self.diff_content, self.diff_file_path)
                self.is_updated = False
        except Exception as e:
            print(e)

auto_mode = True
input_md_file_path = './test/input_and_output_content.md'

# 非同期関数を実行するためのエントリーポイント
markdown_assistant = MarkdownAssistant(
    OPENAI_API_KEY, input_md_file_path, prompt_file_path, md_file_path, diff_file_path, auto_mode)
asyncio.run(markdown_assistant.run_schedule())
