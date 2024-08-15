from llm_agent import LLMAgent
import asyncio
import time

llm = LLMAgent()


def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


async def monitor_files(input_file_path, prompt_file_path, output_file_path):
    last_input_content = read_file(input_file_path)
    last_prompt_content = read_file(prompt_file_path)
    last_change_time = None
    print("Start monitoring text...")

    while True:
        try:
            current_input_content = read_file(input_file_path)
            current_prompt_content = read_file(prompt_file_path)

            if current_input_content != last_input_content or current_prompt_content != last_prompt_content:
                print("File change detected.")
                last_change_time = time.time()
                last_input_content = current_input_content
                last_prompt_content = current_prompt_content

            if last_change_time and (time.time() - last_change_time) >= 3:
                print("No changes detected for 3 seconds. Running LLMAgent...")
                last_change_time = None
                text = await llm(current_input_content, current_prompt_content)
                last_input_content = text
                with open(output_file_path, 'w', encoding='utf-8') as file:
                    file.write(text)

            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(0.1)


async def main():
    input_file_path = 'test/input_and_output.txt'
    prompt_file_path = 'default_prompt.txt'
    output_file_path = 'test/input_and_output.txt'
    await monitor_files(input_file_path, prompt_file_path, output_file_path)

# 非同期関数を実行
asyncio.run(main())
