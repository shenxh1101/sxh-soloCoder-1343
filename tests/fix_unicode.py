"""修复测试文件中的Unicode字符问题。"""
import os

test_files = [
    'tests/test_parsers.py',
    'tests/test_pipeline.py', 
    'tests/test_api.py',
    'tests/run_all_tests.py'
]

replacements = {
    '\u2713': '[OK]',
    '\u274c': '[FAIL]', 
    '\u23f3': '[WAIT]',
    '\U0001f4c4': '[DOC]',
    '\U0001f389': '[PASS]',
    '\u26a0\ufe0f': '[WARN]',
    '\U0001f4ca': '[STAT]',
    '\U0001f3af': '[INFO]',
}

for fpath in test_files:
    full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), fpath)
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for unicode_char, ascii_repl in replacements.items():
        if unicode_char in content:
            content = content.replace(unicode_char, ascii_repl)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Fixed: {fpath}')

print('All files fixed!')
