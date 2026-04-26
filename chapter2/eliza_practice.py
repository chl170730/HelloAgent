"""
ELIZA 练习脚本

目标：
1. 不看答案，自己把这个简化版 ELIZA 写出来
2. 先把骨架补全，再逐步补细节
3. 每完成一个 TODO，就运行一次测试

建议练法：
- 第一遍：只写能跑通的最小版本
- 第二遍：补全代词替换
- 第三遍：补全更多规则
"""

import re
import random

# TODO 1:
# 定义规则库 rules
# 结构应为：
# {
#     正则表达式: [回复模板1, 回复模板2, ...],
#     ...
# }
#
# 至少包含下面这些规则：
# 1. r'I need (.*)'
# 2. r'I am (.*)'
# 3. r'.* mother .*'
# 4. r'.*'
rules = {

    r'I need (.*)': [
        "Why do you need {0}?",
        "Would it really help you to get {0}?",
        "Are you sure you need {0}?"
    ],
    r'Why don\'t you (.*)\?': [
        "Do you really think I don't {0}?",
        "Perhaps eventually I will {0}.",
        "Do you really want me to {0}?"
    ],
    r'Why can\'t I (.*)\?': [
        "Do you think you should be able to {0}?",
        "If you could {0}, what would you do?",
        "I don't know -- why can't you {0}?"
    ],
    r'.*job.*': [
        "Are you currently employed?",
        "Tell me more about your job.",
        "What do you like or dislike about your job?"
    ],
    r'I am (.*)': [
        "Did you come to me because you are {0}?",
        "How long have you been {0}?",
        "How do you feel about being {0}?"
    ],
    r'.* mother .*': [
        "Tell me more about your mother.",
        "What was your relationship with your mother like?",
        "How do you feel about your mother?"
    ],
    r'.* father .*': [
        "Tell me more about your father.",
        "How did your father make you feel?",
        "What has your father taught you?"
    ],
    r'.*\bfriend\b.*|.*\bfriends\b.*': [
        "Do you have many friends?",
        "Tell me more about your friends.",
        "What do you value most in a friend?"
    ],
    r'.*\bhobby\b.*|.*\bhobbies\b.*': [
        "What are your hobbies?",
        "How did you get into that hobby?",
        "What do you enjoy most about your hobby?"
    ],
    r'.*\bstudy\b.*|.*\bstudies\b.*|.*\bstudying\b.*': [
        "Why are you studying?",
        "What subjects do you find most interesting?",
        "How do you feel about your studies?"
    ],
    r'.*\bwork\b.*|.*\bworking\b.*': [
        "Tell me more about your work.",
        "How do you feel about your work?",
        "What is your work like these days?"
    ],
    r'My job is (.*)': [
        "How do you feel about your job as {0}?",
        "What is it like to work as {0}?",
        "Do you enjoy being {0}?"
    ],
    r'I am a[n]? (.*)': [
        "How do you feel about being {0}?",
        "What does being {0} mean to you?",
        "Do you enjoy being {0}?"
    ],
    r'.*': [
        "Please tell me more.",
        "Let's change focus a bit... Tell me about your family.",
        "Can you elaborate on that?"
    ],
}


# TODO 2:
# 定义代词转换字典 pronoun_swap
# 至少包含：
# i -> you
# you -> i
# me -> you
# my -> your
pronoun_swap = {
    "i": "you", "you": "i", "me": "you", "my": "your",
    "am": "are", "are": "am", "was": "were", "i'd": "you would",
    "i've": "you have", "i'll": "you will", "yours": "mine",
    "mine": "yours"
}

memory = {
    "name":None,
    "age":None,
    "job":None,
}

def memory_response(user_input):
    lowered = user_input.lower().strip()

    if re.search(r'what is my name\??|do you remember my name\??', lowered):
        if memory['name']:
            return f"Your name is {memory['name']}."
        return "I don't know your name yet. What is your name?"

    if re.search(r'how old am i\??|do you remember my age\??', lowered):
        if memory['age']:
            return f"You told me that you are {memory['age']} years old."
        return "I don't know your age yet. How old are you?"

    if re.search(r'what is my job\??|do you remember my job\??', lowered):
        if memory['job']:
            return f"You told me that you work as a {memory['job']}."
        return "I don't know your job yet. What do you do?"

    if memory['job'] and re.search(r'work|job|career', lowered):
        return random.choice([
            f"How do you feel about working as a {memory['job']}?",
            f"Does being a {memory['job']} affect how you feel right now?"
        ])

    if memory['name'] and re.search(r'i feel|i am|i need', lowered):
        return random.choice([
            f"{memory['name']}, can you tell me more about that?",
            f"How does that make you feel, {memory['name']}?"
        ])

    return None

def update_memory(user_input):
    name_match = re.search(r'my name is (\w+)', user_input, re.IGNORECASE)
    if name_match:
        memory['name'] = name_match.group(1)

    age_match = re.search(r'i am (\d+) years old', user_input, re.IGNORECASE)
    if age_match:
        memory['age'] = age_match.group(1)

    job_match = re.search(r'i work as a[n]? (\w+)', user_input, re.IGNORECASE)
    if job_match:
        memory['job'] = job_match.group(1)

def swap_pronouns(phrase):
    """
    对输入短语中的代词进行第一/第二人称转换

    例子：
    "I need my rest" -> "you need your rest"
    """
    # TODO 3:
    # 1. 把 phrase 转成小写
    phrase = phrase.lower()
    # 2. 用 split() 拆成单词列表
    words = phrase.split()
    # 3. 对每个单词做字典替换：如果在 pronoun_swap 中，就替换；否则保持原样
    swapped_words = [pronoun_swap.get(word,word) for word in words]
    # 4. 用 " ".join(...) 拼回字符串
    return " ".join(swapped_words)


def respond(user_input):
    """
    根据规则库生成响应
    """
    # TODO 4:
    # 调用记忆模块回复，如果记忆模块返回了回复，就直接返回这个回复，否则执行下面的规则匹配
    # 遍历 rules 中的每一条规则
    mem_reply = memory_response(user_input)
    if mem_reply:
        return mem_reply
    for pattern,responses in rules.items():
        match = re.search(pattern,user_input,re.IGNORECASE)
        if match:
            captured_group = match.group(1) if match.groups() else ''
            swapped_p = swap_pronouns(captured_group)
            response = random.choice(responses).format(swapped_p)
            return response
    return random.choice(rules['.*'])


def run_manual_tests():
    """
    你可以在写完后取消注释，快速测试
    """
    test_inputs = [
        "My name is Tom",
        "I am 20 years old",
        "I work as an engineer",
        "What is my name?",
        "How old am I?",
        "What is my job?",
        "My hobby is tennis",
        "I have many friends",
        "My job is firefighter",
        "I am studying math",
        "I feel tired",
        "My mother is strict",
        "Hello",
    ]

    print("=== Manual Tests ===")
    for text in test_inputs:
        update_memory(text)
        print(f"You: {text}")
        print(f"Therapist: {respond(text)}")
        print()


# 主聊天循环
if __name__ == '__main__':
    print("Therapist: Hello! How can I help you today?")


    while True:
        user_input = input("You: ")

        # TODO 11:
        # 如果用户输入是 quit / exit / bye，则打印告别语并退出循环
        if user_input.lower() in ["quit", "exit","bye"]:
            print("Therapist: Goodbye. It was nice talking to you.")
            break
        update_memory(user_input)

        # TODO 12:
        response = respond(user_input)
        print(f"Therapist: {response}")
        # 调用 respond(user_input) 得到回复
        # 然后打印：
        # Therapist: xxx


    # 写完后可以打开这行测试
    run_manual_tests()


"""
========================
自测标准
========================

第 1 级：能运行
- 程序能启动
- 输入一句话后能返回一句回复
- 输入 quit 能正常退出

第 2 级：能匹配
- "I need a rest" 能触发 I need 规则
- "I am tired" 能触发 I am 规则
- 包含 mother 的句子能触发 mother 规则
- 其他内容能落到兜底规则 r'.*'

第 3 级：能替换
- captured_group = "my book"
- swap_pronouns(captured_group) 后得到 "your book"

第 4 级：能扩展
你自己加下面任意两个：
- r'I feel (.*)'
- r'.* father .*'
- 空输入特殊处理
- 支持更多代词替换
- 支持中文提示
"""
