import re

def contains_chinese(text):
    # 判断字符串是否包含中文字符
    return bool(re.search(r'[\u4e00-\u9fff]', text))
