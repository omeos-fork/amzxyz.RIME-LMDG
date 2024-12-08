import os
import json
import re

# 句子替换和清理
def sentence_replacement(line):
    line = re.sub(r'[。；;.?!,，！？]', '\n', line)
    line = re.sub(r'\\n', '\n', line)
    line = re.sub(r'[、：:《》「」\{\}\[\]()【】（）“”‘’\'\"`___-——_~=^\\1234567890abcdefghijklmnopqrstuvwxyzQWERTYUIOPLKJHGFDSAZXCVBNM]', '', line)
    line = re.sub(r'翻译成文言文', '', line)
    line = re.sub(r'翻译成现代文', '', line)
    line = re.sub(r'是否重复文件', '', line)
    line = re.sub(r'文件大小', '', line)
    line = re.sub(r'最长段落长度', '', line)
    line = re.sub(r'段落数', '', line)
    line = re.sub(r'去重段落数', '', line)
    line = re.sub(r'低质量段落数', '', line)
    line = re.sub(r'段落行号', '', line)
    line = re.sub(r'是否重复', '', line)
    line = re.sub(r'是否跨文件重复', '', line)
    line = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff\u3400-\u4DBF\u20000-\u2A6DF\u2A700-\u2B73F\u2B740-\u2B81F\u2B820-\u2CEAF\u2CEB0-\u2EBEF\u30000-\u3134F]', '', line)
    return line.strip()  # 去除两端空白字符

# 递归提取文件夹中所有文件
def process_folder(input_folder, output_folder):
    # 遍历文件夹中的每个文件
    for root, dirs, files in os.walk(input_folder):  # 使用os.walk来递归遍历文件夹
        for filename in files:
            input_file_path = os.path.join(root, filename)
            file_extension = os.path.splitext(filename)[1].lower()  # 获取文件扩展名并转小写
            
            # 处理 JSONL 或 JSON 文件
            if file_extension == ".jsonl" or file_extension == ".json":
                process_json(input_file_path, output_folder, file_extension)
            
            # 处理 TXT 文件或没有扩展名的文件
            elif file_extension == ".txt" or file_extension == "":
                process_txt(input_file_path, output_folder)
            else:
                print(f"Skipping unsupported file type: {filename}")

# 处理 JSON 文件
def process_json(input_file_path, output_folder, file_extension):
    try:
        with open(input_file_path, 'rb') as file:
            data = []
            if file_extension == ".jsonl":
                for line in file:
                    try:
                        json_data = json.loads(line.strip())  # 逐行处理JSONL
                        extracted_entry = extract_json_fields(json_data)
                        formatted_entry = format_entry(extracted_entry)
                        if formatted_entry:
                            data.append(formatted_entry)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding line in {input_file_path}: {e}")
            elif file_extension == ".json":
                content = file.read().decode('utf-8', errors='ignore')
                try:
                    json_data = json.loads(content)  # 读取整个JSON文件
                    extracted_entry = extract_json_fields(json_data)
                    formatted_entry = format_entry(extracted_entry)
                    if formatted_entry:
                        data.append(formatted_entry)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in {input_file_path}: {e}")

            if data:
                # 清理每个条目并保存为 .txt 文件
                output_file_path = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(input_file_path))[0]}.txt")
                with open(output_file_path, 'w', encoding='utf-8') as outfile:
                    for record in data:
                        outfile.write(sentence_replacement(record))  # 对数据进行句子替换和清理
                print(f"Processed file: {input_file_path}")
    except Exception as e:
        print(f"Error processing file {input_file_path}: {e}")

# 提取所需字段
def extract_json_fields(json_data):
    return {
        "title": json_data.get("title", ""),
        "desc": json_data.get("desc", ""),
        "answer": json_data.get("answer", ""),
        "category": json_data.get("category", ""),
        "instruction": json_data.get("instruction", ""),
        "output": json_data.get("output", ""),
        "问": json_data.get("问", ""),        
        "答": json_data.get("答", "")
    }

# 格式化提取的字段为可读文本
def format_entry(extracted_entry):
    formatted_entry = ""
    if extracted_entry["title"]:
        formatted_entry += f"Title: {extracted_entry['title']}\n"
    if extracted_entry["desc"]:
        formatted_entry += f"Description: {extracted_entry['desc']}\n"
    if extracted_entry["answer"]:
        formatted_entry += f"Content: {extracted_entry['answer']}\n"
    if extracted_entry["category"]:
        formatted_entry += f"Category: {extracted_entry['category']}\n"
    if extracted_entry["instruction"]:
        formatted_entry += f"instruction: {extracted_entry['instruction']}\n"
    if extracted_entry["output"]:
        formatted_entry += f"output: {extracted_entry['output']}\n"
    if extracted_entry["问"]:
        formatted_entry += f"问: {extracted_entry['问']}\n"
    if extracted_entry["答"]:
        formatted_entry += f"答: {extracted_entry['答']}\n"

    # 如果有内容，添加分隔符
    if formatted_entry:
        formatted_entry += "="*40 + "\n"
    
    return formatted_entry

# 处理 TXT 文件
def process_txt(input_file_path, output_folder):
    try:
        with open(input_file_path, 'rb') as file:
            data = []
            for line in file:
                # 解码并清理每一行文本
                cleaned_line = sentence_replacement(line.decode('utf-8', errors='ignore').strip())
                if cleaned_line:
                    data.append(cleaned_line)

            if data:
                # 保存为 .txt 文件
                output_file_path = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(input_file_path))[0]}.txt")
                with open(output_file_path, 'w', encoding='utf-8') as outfile:
                    for cleaned_line in data:
                        outfile.write(cleaned_line + '\n')  # 每行末尾添加换行符
                print(f"Processed TXT file: {input_file_path}")
    except Exception as e:
        print(f"Error processing TXT file {input_file_path}: {e}")

# 主程序
if __name__ == "__main__":
    input_folder = "autodl-tmp/语料输入"  # 输入文件夹路径
    output_folder = "autodl-tmp/语料清洗后"  # 输出文件夹路径

    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 递归处理文件夹中的所有文件
    process_folder(input_folder, output_folder)
    print("Extraction completed.")
