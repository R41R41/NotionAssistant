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

    def clear_ai_feedback(self):
        with open(self.md_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for i, line in enumerate(lines):
            if line.startswith('<!--'):
                while not lines[i].strip().endswith('-->'):
                    lines[i] = ''
                    i += 1
                lines[i] = ''

        with open(self.md_file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)

    def add_text_to_markdown(self, position, text):
        with open(self.md_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        position_found = False
        for i, line in enumerate(lines):
            if position in line:
                lines.insert(i + 1, f"<!-- {text} -->\n")
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
