import difflib
import os


class MarkdownAgent:
    def __init__(self, projects_path, project_name):
        self.projects_path = projects_path
        self.project_name = project_name
        self.project_path = f"{self.projects_path}/{self.project_name}"
        if not os.path.exists(self.project_path):
            os.makedirs(self.project_path)

    def delete_project_item(self, id):
        file_path = f"{self.project_path}/{id}.md"
        if os.path.exists(file_path):
            os.remove(file_path)

    def get_saved_content(self, id):
        file_path = f"{self.project_path}/{id}.md"
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            print(f"ファイルが存在しません: {file_path}")
            return None

    def save_project_items(self, project_items):
        for item in project_items:
            id = item['id']
            body = self.get_content_without_ai_feedback(item['body'])
            file_path = f"{self.project_path}/{id}.md"

            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(body)

    def get_file_content(self, md_file_path):
        if md_file_path:
            # ページのメタデータを取得
            with open(md_file_path, 'r', encoding='utf-8') as file:
                markdown_content = file.read()
            return markdown_content
        else:
            return None

    def get_content_without_ai_feedback(self, markdown_content):
        lines = markdown_content.splitlines()
        filtered_lines = []
        for line in lines:
            if not line.strip().startswith('>'):
                filtered_lines.append(line)
        return '\n'.join(filtered_lines)

    def get_content_with_ai_feedback(self, markdown_content, comments):
        lines = markdown_content.splitlines()
        for comment in comments:
            position = comment['position']
            text = comment['comment']
            position_found = False
            for i, line in enumerate(lines):
                if position in line:
                    text_lines = text.split('\n')
                    for j, text_line in enumerate(text_lines):
                        lines.insert(i + 1 + j, f"> {text_line}")
                    position_found = True
                    break

            if not position_found:
                print(f"挿入位置が見つかりませんでした: {position}")
                return None

        return '\n'.join(lines)

    def clear_ai_feedback(self):
        with open(self.md_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        lines = self.get_content_without_ai_feedback('\n'.join(lines))

        with open(self.md_file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)

    def add_text_to_markdown(self, position, text):
        with open(self.md_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        position_found = False
        for i, line in enumerate(lines):
            if position in line:
                text_lines = text.split('\n')
                for j, text_line in enumerate(text_lines):
                    lines.insert(i + 1 + j, f"> {text_line}")
                position_found = True
                break

        if not position_found:
            print(f"挿入位置が見つかりませんでした: {position}")
            return None

        with open(self.md_file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)

    def get_diff_content(self, old_content, new_content):
        diff = difflib.ndiff(
            old_content.splitlines(),
            new_content.splitlines()
        )
        diff_content = []
        for line in diff:
            if line.startswith('-'):
                diff_content.append(f"--{line[2:]}")
            elif line.startswith('+'):
                diff_content.append(f"++{line[2:]}")
            elif line.startswith(' '):
                diff_content.append(line[2:])  # 変更されていない行はそのまま出力

        return '\n'.join(diff_content)
