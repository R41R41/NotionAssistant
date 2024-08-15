import difflib


class MarkdownAgent:
    def __init__(self, md_file_path):
        self.md_file_path = md_file_path

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
        i = 0
        while i < len(lines):
            if lines[i].startswith('`'):
                while i < len(lines) and not lines[i].strip().endswith('`'):
                    i += 1
                i += 1
            elif lines[i].strip():
                filtered_lines.append(lines[i])
                i += 1
            else:
                i += 1
        return '\n'.join(filtered_lines)

    def get_content_with_ai_feedback(self, markdown_content, comments):
        lines = markdown_content.splitlines()
        for comment in comments:
            position = comment['position']
            text = comment['comment']
            position_found = False
            for i, line in enumerate(lines):
                if position in line:
                    lines.insert(i + 1, f"`{text}`\n")
                    position_found = True
                    break

            if not position_found:
                return f"挿入位置が見つかりませんでした: {position}"

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
                lines.insert(i + 1, f"`{text}`\n")
                position_found = True
                break

        if not position_found:
            return f"挿入位置が見つかりませんでした: {position}"

        with open(self.md_file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)

    def get_diff_to_file(self, old_content, new_content):
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
