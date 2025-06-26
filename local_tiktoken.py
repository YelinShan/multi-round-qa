import os
import tiktoken
from functools import lru_cache
import hashlib

# 这个函数会被用来替代tiktoken.load模块中的read_file函数
@lru_cache()
def read_file_local(blobpath):
    # 如果URL是cl100k_base.tiktoken的下载链接，使用本地文件
    if 'cl100k_base.tiktoken' in blobpath:
        local_path = os.path.expanduser('~/.cache/tiktoken/cl100k_base.tiktoken')
        if os.path.exists(local_path):
            print(f"Loading tiktoken file from local cache: {local_path}")
            with open(local_path, 'rb') as f:
                return f.read()
    
    # 如果没有找到本地文件，抛出异常
    raise FileNotFoundError(f"Cannot load tiktoken file: {blobpath}. 网络连接失败，且本地缓存不可用。")

# 修补tiktoken的加载过程
def patch_tiktoken():
    try:
        import tiktoken.load
        # 保存原始函数
        original_read_file = tiktoken.load.read_file
        # 修补函数
        tiktoken.load.read_file = read_file_local
        print("已成功修补tiktoken加载过程，将使用本地文件")
        return True
    except ImportError:
        print("警告：无法修补tiktoken加载过程")
        return False

# 获取编码器的包装函数
def get_encoding(encoding_name):
    success = patch_tiktoken()
    if success:
        return tiktoken.get_encoding(encoding_name)
    else:
        # 如果修补失败，返回一个简单的token计数器
        return SimpleTokenCounter()

# 根据模型获取编码器的包装函数
def encoding_for_model(model_name):
    success = patch_tiktoken()
    if success:
        return tiktoken.encoding_for_model(model_name)
    else:
        # 如果修补失败，返回一个简单的token计数器
        return SimpleTokenCounter()

# 简单的token计数器作为后备方案
class SimpleTokenCounter:
    """一个简单的token计数器，用于替代tiktoken"""
    def __init__(self):
        pass
    
    def encode(self, text):
        """估算文本中的token数量并返回一个假的token列表"""
        # 计算中文字符数量
        chinese_char_count = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        # 计算非中文字符数量
        non_chinese_char_count = len(text) - chinese_char_count
        
        # 中文字符按1.5个字符/token计算，非中文按4.5个字符/token计算
        estimated_tokens = int(chinese_char_count / 1.5 + non_chinese_char_count / 4.5)
        
        # 返回一个假的token列表，长度为估算的token数量
        return [0] * max(1, estimated_tokens)
