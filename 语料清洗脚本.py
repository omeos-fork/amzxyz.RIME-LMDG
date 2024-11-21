import os
import json
import gc
import re
import regex  # 使用 regex 支持更复杂的正则
from opencc import OpenCC  # 导入 OpenCC 用于繁简转换
from concurrent.futures import ThreadPoolExecutor, as_completed

# ======= 配置参数 =======
CORPUS_INPUT = "autodl-tmp/语料输入"          # 输入目录
CLEANED_CORPUS = "autodl-tmp/语料清洗后"         # 输出目录
STOPWORDS_PATH = "停用词表"          # 停用词表路径
SUPPORTED_FORMATS = ["txt", "yaml", "json", "xml", "csv", "jsonl"]  # 支持的文件格式
STOPWORDS_ENABLED = False           # 是否启用停用词表
USE_OPENCC = True  # 开关：是否进行繁简转换
MAX_LINE_LENGTH = 30000             # 行内最大汉字数量
MAX_FILE_SIZE = 500 * 1024 * 1024    # 输出文件的最大大小（50MB）
CHUNK_THRESHOLD = 5000 * 1024 * 1024  # 内存分块大小（10MB）
MAX_WORKERS = min(4, os.cpu_count())        # 自动检测 CPU 核心数设定

opencc = OpenCC('t2s') if USE_OPENCC else None  # t2s 表示繁体到简体转换

# ======= 停用词加载 =======
def load_stopwords():
    if not STOPWORDS_ENABLED:
        return set()
    with open(STOPWORDS_PATH, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

STOPWORDS = load_stopwords()

# ======= 文本处理功能 =======  这里是顺序处理，处理前其它json xml格式最好先打开判断格式元素，然后将有效字段解析出来，再去进这个脚本
def sentence_replacement(line):
    """句中符号替换和关键词删除"""
    line = re.sub(r'[。：、；;:.?!,，！？]', '\n', line)
    line = re.sub(r'是否待查文件', '', line)
    line = re.sub(r'是否重复文件', '', line)
    line = re.sub(r'文件大小', '', line)
    line = re.sub(r'最长段落长度', '', line)
    line = re.sub(r'段落数', '', line)
    line = re.sub(r'去重段落数', '', line)
    line = re.sub(r'低质量段落数', '', line)
    line = re.sub(r'段落行号', '', line)
    line = re.sub(r'是否重复', '', line)
    line = re.sub(r'是否跨文件重复', '', line)
    return line.strip()  # 去除前后多余空格和换行

def line_replacement(line):
    """整行替换或删除"""
    line = re.sub(r'\b(title|category|})\b', '\n', line)
    line = re.sub(r'"id":\s*".*?",\s*"问":\s*".*?"', '', line)
    return line.strip()

def keep_cjk_only(line):
    """只保留 CJK 汉字和换行符"""
    return regex.sub(r'[^\u4e00-\u9fff\n]', '', line).strip()    #制作词库的时候用

def truncate_long_lines(lines):
    """截断超长行"""
    result = []
    for line in lines:
        while len(line) > MAX_LINE_LENGTH:
            result.append(line[:MAX_LINE_LENGTH])
            line = line[MAX_LINE_LENGTH:]
        result.append(line)
    return result

def filter_stopwords(lines):
    """根据停用词表过滤停用词"""
    if not STOPWORDS:
        return lines
    filtered = []
    for line in lines:
        words = line.split()
        filtered_line = ' '.join([word for word in words if word not in STOPWORDS])
        if filtered_line:
            filtered.append(filtered_line)
    return filtered

def remove_empty_lines(lines):
    """删除所有空行"""
    return [line for line in lines if line.strip()]

# ======= 文件处理逻辑 =======
def process_file(input_file, output_path):
    base_filename = os.path.splitext(os.path.basename(input_file))[0]
    temp_content = []

    try:
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:  # 使用错误处理方式'replace'
            for line in f:
                line = sentence_replacement(line)
                line = line_replacement(line)
                line = keep_cjk_only(line)
                if line:
                    temp_content.append(line)

                if sum(map(len, temp_content)) > CHUNK_THRESHOLD:
                    save_chunk(temp_content, output_path, base_filename)
                    temp_content.clear()
                    gc.collect()

        if temp_content:
            save_chunk(temp_content, output_path, base_filename)
    except UnicodeDecodeError as e:
        print(f"读取文件 {input_file} 时出现编码错误: {e}")
    except Exception as e:
        print(f"处理文件 {input_file} 时出错：{e}")

def save_chunk(temp_content, output_path, base_filename):
    lines = remove_empty_lines(temp_content)
    lines = truncate_long_lines(lines)
    lines = filter_stopwords(lines)

    text = '\n'.join(lines)  # 确保只有一层换行
    text = apply_opencc_conversion(text)
    split_and_save(text, output_path, base_filename)

def split_and_save(content, output_path, base_filename):
    file_num = 1
    while content:
        chunk = content[:MAX_FILE_SIZE]
        content = content[MAX_FILE_SIZE:]
        file_path = os.path.join(output_path, f"{base_filename}_{file_num}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(chunk.strip())  # 去除块首尾多余换行
        file_num += 1

# ======= OpenCC 转换功能 =======
def apply_opencc_conversion(text):
    """应用 OpenCC 转换，如果启用"""
    return opencc.convert(text) if USE_OPENCC and opencc else text

# ======= 主处理逻辑 =======
def process_files(input_path, output_path):
    files_to_process = [
        os.path.join(root, filename)
        for root, _, files in os.walk(input_path)
        for filename in files if filename.split('.')[-1] in SUPPORTED_FORMATS
    ]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_file, file, output_path): file for file in files_to_process
        }

        for future in as_completed(futures):
            file = futures[future]
            try:
                # 设置超时时间以避免卡住
                future.result(timeout=300)
                print(f"处理完成：{file}")
            except Exception as e:
                print(f"处理文件 {file} 时出错：{e}")

# ======= 程序入口 =======
if __name__ == "__main__":
    os.makedirs(CLEANED_CORPUS, exist_ok=True)
    process_files(CORPUS_INPUT, CLEANED_CORPUS)
