import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
DATABASE_ID = os.getenv('DATABASE_ID')
url = f'https://api.notion.com/v1/databases/{DATABASE_ID}/query'
PAGE_NAME = os.getenv('PAGE_NAME')

headers = {
    'Notion-Version': '2022-06-28',
    'Authorization': 'Bearer ' + NOTION_API_KEY,
    'Content-Type': 'application/json',
}

json_data = {
    'filter': {
        'property': '名前',
        'title': {
            'equals': PAGE_NAME
        }
    }
}

def notion_to_markdown(blocks, indent=0):
    markdown = ""
    indent_str = "    " * indent
    for block in blocks:
        block_type = block['type']
        if block_type == 'paragraph':
            text = block[block_type]['rich_text']
            markdown += indent_str + "".join([t['text']['content'] for t in text]) + "\n\n"
        elif block_type == 'heading_1':
            text = block[block_type]['rich_text']
            markdown += indent_str + "# " + "".join([t['text']['content'] for t in text]) + "\n\n"
            if block[block_type].get('is_toggleable', False) and block['has_children']:
                child_blocks = get_block_children(block['id'])
                markdown += notion_to_markdown(child_blocks, indent + 1)
        elif block_type == 'heading_2':
            text = block[block_type]['rich_text']
            markdown += indent_str + "## " + "".join([t['text']['content'] for t in text]) + "\n\n"
            if block[block_type].get('is_toggleable', False) and block['has_children']:
                child_blocks = get_block_children(block['id'])
                markdown += notion_to_markdown(child_blocks, indent + 1)
        elif block_type == 'heading_3':
            text = block[block_type]['rich_text']
            markdown += indent_str + "### " + "".join([t['text']['content'] for t in text]) + "\n\n"
            if block[block_type].get('is_toggleable', False) and block['has_children']:
                child_blocks = get_block_children(block['id'])
                markdown += notion_to_markdown(child_blocks, indent + 1)
        elif block_type == 'bulleted_list_item':
            text = block[block_type]['rich_text']
            markdown += indent_str + "- " + "".join([t['text']['content'] for t in text]) + "\n"
            if block['has_children']:
                child_blocks = get_block_children(block['id'])
                markdown += notion_to_markdown(child_blocks, indent + 1)
        elif block_type == 'numbered_list_item':
            text = block[block_type]['rich_text']
            markdown += indent_str + "1. " + "".join([t['text']['content'] for t in text]) + "\n"
            if block['has_children']:
                child_blocks = get_block_children(block['id'])
                markdown += notion_to_markdown(child_blocks, indent + 1)
        elif block_type == 'toggle':
            text = block[block_type]['rich_text']
            markdown += indent_str + "".join([t['text']['content'] for t in text]) + "\n"
            if block['has_children']:
                child_blocks = get_block_children(block['id'])
                markdown += notion_to_markdown(child_blocks, indent + 1)
        # 他のブロックタイプも必要に応じて追加
    return markdown

def get_block_children(block_id):
    blocks_url = f'https://api.notion.com/v1/blocks/{block_id}/children'
    blocks_response = requests.get(blocks_url, headers=headers)
    return blocks_response.json().get('results', [])

try:
    response = requests.post(url, headers=headers, json=json_data)
    results = response.json().get('results')
    if results:
        page_id = results[0]['id']
        
        # ページのメタデータを取得
        page_url = f'https://api.notion.com/v1/pages/{page_id}'
        page_response = requests.get(page_url, headers=headers)
        page_data = page_response.json()
        last_edited_time = page_data.get('last_edited_time')
        
        blocks_content = get_block_children(page_id)
        
        # JSONファイルに保存
        with open('./test/page_content.json', 'w', encoding='utf-8') as f:
            json.dump(blocks_content, f, ensure_ascii=False, indent=4)
        
        # マークダウン形式に変換して保存
        markdown_content = notion_to_markdown(blocks_content)
        with open('./test/page_content.md', 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"ページの中身が./test/page_content.jsonと./test/page_content.mdに保存されました。最終更新日時: {last_edited_time}")
    else:
        print("ページが見つかりませんでした。")
except Exception as e:
    print(e)