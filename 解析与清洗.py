import os
import json
import re

def process_folder(input_folder, output_folder):
    # 使用os.walk递归遍历文件夹
    for root, dirs, files in os.walk(input_folder):
        print(f"Checking directory: {root}")  # 打印当前检查的目录
        for filename in files:
            input_file_path = os.path.join(root, filename)  # 拼接文件路径
            print(f"Processing file: {input_file_path}")  # 打印当前处理的文件路径
            
            # 获取文件扩展名
            file_extension = os.path.splitext(filename)[1].lower()
            
            # 处理 jsonl 或 json 文件
            if file_extension == ".jsonl" or file_extension == ".json":
                process_json(input_file_path, output_folder, file_extension)
            
            # 处理 txt 和 pt 文件
            elif file_extension == ".txt" or file_extension == ".pt":
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
                        json_data = json.loads(line.strip())
                        extracted_entry = extract_json_fields(json_data)
                        formatted_entry = format_entry(extracted_entry)
                        if formatted_entry:
                            data.append(formatted_entry)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding line in {input_file_path}: {e}")
            elif file_extension == ".json":
                content = file.read().decode('utf-8', errors='ignore')
                try:
                    json_data = json.loads(content)
                    extracted_entry = extract_json_fields(json_data)
                    formatted_entry = format_entry(extracted_entry)
                    if formatted_entry:
                        data.append(formatted_entry)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in {input_file_path}: {e}")

            if data:
                output_file_path = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(input_file_path))[0]}.txt")
                with open(output_file_path, 'w', encoding='utf-8') as outfile:
                    for record in data:
                        cleaned_record = sentence_replacement(record)
                        if cleaned_record:  # 确保只有非空的内容被写入
                            outfile.write(cleaned_record)
                print(f"Processed file: {input_file_path}")
    except Exception as e:
        print(f"Error processing file {input_file_path}: {e}")

# 提取字段
def extract_json_fields(json_data):
    return {
        "title": json_data.get("title", ""),
        "desc": json_data.get("desc", ""),
        "answer": json_data.get("answer", ""),
        "category": json_data.get("category", ""),
        "instruction": json_data.get("instruction", ""),
        "output": json_data.get("output", ""),
        "input": json_data.get("input", ""),
        "问": json_data.get("问", ""),   
        "内容": json_data.get("内容", ""),  
        "回复": json_data.get("回复", ""),  
        "答": json_data.get("答", "")
    }

# 格式化提取数据
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
    if extracted_entry["input"]:
        formatted_entry += f"input: {extracted_entry['input']}\n"
    if extracted_entry["output"]:
        formatted_entry += f"output: {extracted_entry['output']}\n"
    if extracted_entry["问"]:
        formatted_entry += f"问: {extracted_entry['问']}\n"
    if extracted_entry["答"]:
        formatted_entry += f"答: {extracted_entry['答']}\n"
    if extracted_entry["内容"]:
        formatted_entry += f"内容: {extracted_entry['内容']}\n"
    if extracted_entry["回复"]:
        formatted_entry += f"回复: {extracted_entry['回复']}\n"
    
    if formatted_entry:
        formatted_entry += "="*40 + "\n"
    
    return formatted_entry

# 清理句子
def sentence_replacement(line):
    # 替换标点符号为换行
    line = re.sub(r'[。；;!?.，,！？]', '\n', line) 
    # 删除非汉字字符和特定符号
    line = re.sub(r'[、：:《》「」\{\}\[\]()【】（）“”‘’\'\"`___-——_~=^\\1234567890abcdefghijklmnopqrstuvwxyzQWERTYUIOPLKJHGFDSAZXCVBNM]', '', line)
    # 删除无意义的文本
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
    # 删除非汉字字符及不必要的...
    line = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff\u3400-\u4DBF\u20000-\u2A6DF\u2A700-\u2B73F\u2B740-\u2B81F\u2B820-\u3134F]', '', line)
    
    # 确保只有非空行被返回
    return line.strip() if line.strip() else None

# 处理 TXT 文件
def process_txt(input_file_path, output_folder):
    try:
        with open(input_file_path, 'rb') as file:
            data = []
            for line in file:
                cleaned_line = sentence_replacement(line.decode('utf-8', errors='ignore').strip())
                if cleaned_line:  # 只有非空内容才被添加
                    data.append(cleaned_line)

            if data:
                output_file_path = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(input_file_path))[0]}.txt")
                with open(output_file_path, 'w', encoding='utf-8') as outfile:
                    for record in data:
                        outfile.write(record + '\n')  # 每条记录换行
                print(f"Processed file: {input_file_path}")
    except Exception as e:
        print(f"Error processing file {input_file_path}: {e}")


if __name__ == "__main__":
    input_folder = "输入文件夹路径"  # 请替换为输入文件夹的实际路径
    output_folder = "输出文件夹路径"  # 请替换为输出文件夹的实际路径
    
    process_folder(input_folder, output_folder)

    print("所有文件处理完成")
