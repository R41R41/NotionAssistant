import requests
import difflib


class NotionAgent:
    def __init__(self, api_key, database_id):
        self.api_key = api_key
        self.database_id = database_id
        self.headers = {
            'Notion-Version': '2022-06-28',
            'Authorization': 'Bearer ' + self.api_key,
            'Content-Type': 'application/json',
        }
        self.url = f'https://api.notion.com/v1/databases/{
            self.database_id}/query'

    def get_page_id_by_name(self, page_name):
        json_data = {
            'filter': {
                'property': '名前',
                'title': {
                    'equals': page_name
                }
            }
        }
        response = requests.post(
            self.url, headers=self.headers, json=json_data)
        results = response.json().get('results')
        if results:
            return results[0]['id']
        else:
            print("ページが見つかりませんでした。")
            return None

    def get_block_children(self, block_id):
        blocks_url = f'https://api.notion.com/v1/blocks/{block_id}/children'
        blocks_response = requests.get(blocks_url, headers=self.headers)
        return blocks_response.json().get('results', [])

    def notion_to_markdown(self, blocks, indent=0):
        markdown = ""
        indent_str = "    " * indent
        for block in blocks:
            block_type = block['type']
            if 'rich_text' in block[block_type]:
                text = block[block_type]['rich_text']
                content = "".join([t['text']['content'] for t in text])
            else:
                content = ""

            if block_type == 'paragraph':
                markdown += f"{indent_str}{content}\n"
            elif block_type == 'heading_1':
                markdown += f"{indent_str}# {content}\n"
            elif block_type == 'heading_2':
                markdown += f"{indent_str}## {content}\n"
            elif block_type == 'heading_3':
                markdown += f"{indent_str}### {content}\n"
            elif block_type == 'bulleted_list_item':
                markdown += f"{indent_str}- {content}\n"
            elif block_type == 'numbered_list_item':
                markdown += f"{indent_str}1. {content}\n"
            elif block_type == 'toggle':
                markdown += f"{indent_str}{content}\n"
            # 他のブロックタイプも必要に応じて追加

            if block.get('has_children'):
                child_blocks = self.get_block_children(block['id'])
                markdown += self.notion_to_markdown(child_blocks, indent + 1)

        return markdown

    def get_page_content(self, page_name):
        page_id = self.get_page_id_by_name(page_name)
        if page_id:
            # ページのメタデータを取得
            page_url = f'https://api.notion.com/v1/pages/{page_id}'
            page_response = requests.get(page_url, headers=self.headers)
            page_data = page_response.json()
            last_edited_time = page_data.get('last_edited_time')

            blocks_content = self.get_block_children(page_id)

            # マークダウン形式に変換
            markdown_content = self.notion_to_markdown(blocks_content)
            return markdown_content, last_edited_time, page_id
        else:
            return None, None, None

    def add_text_to_notion(self, page_id, position, text):
        def find_and_add_text(blocks, position, text):
            for i, block in enumerate(blocks):
                block_type = block['type']
                if 'rich_text' in block[block_type]:
                    block_text = "".join([t['text']['content']
                                         for t in block[block_type]['rich_text']])
                else:
                    block_text = ""

                if position in block_text:
                    new_block = {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": text
                                    },
                                    "annotations": {
                                        "color": "gray"
                                    }
                                }
                            ]
                        }
                    }
                    # 新しいブロックを追加
                    append_url = f'https://api.notion.com/v1/blocks/{
                        block["id"]}/children'
                    response = requests.patch(append_url, headers=self.headers, json={
                                              "children": [new_block]})
                    if response.status_code != 200:
                        print(f"テキストの追加に失敗しました: {response.text}")
                    else:
                        print(f"テキストが追加されました: {text}")
                    return True
                if block.get('has_children'):
                    child_blocks = self.get_block_children(block['id'])
                    if find_and_add_text(child_blocks, position, text):
                        return True
            return False

        blocks_url = f'https://api.notion.com/v1/blocks/{page_id}/children'
        blocks_response = requests.get(blocks_url, headers=self.headers)
        blocks = blocks_response.json().get('results', [])

        if not find_and_add_text(blocks, position, "AI:" + text):
            print("指定された位置にテキストを追加できませんでした。")

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
