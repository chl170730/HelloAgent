"""
ELIZA practice script

Goals:
1. Implement a simplified ELIZA without looking at the answer.
2. Fill the skeleton first, then progressively refine details.
3. Run tests after completing each TODO.

Practice suggestions:
- First pass: implement a minimal working version
- Second pass: add pronoun swapping
- Third pass: expand rules
"""

import re
import random

# TODO 1:
# Define the rule base `rules` with the structure:
# {
#     regex_pattern: [response_template1, response_template2, ...],
#     ...
# }
# Include at least these rules:
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
# Define the pronoun conversion dictionary `pronoun_swap` with at least:
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
    Swap first/second person pronouns in the input phrase.

    Example:
    "I need my rest" -> "you need your rest"
    """
    # TODO 3:
    # 1. Lowercase the phrase
    phrase = phrase.lower()
    # 2. Split into words with split()
    words = phrase.split()
    # 3. Replace each word if it's in pronoun_swap, otherwise keep it
    swapped_words = [pronoun_swap.get(word,word) for word in words]
    # 4. Join back into a string
    return " ".join(swapped_words)


def respond(user_input):
    """
    Generate a response based on the rule base.
    """
    # TODO 4:
    # Call memory_response first; if it returns a reply, return it directly. Otherwise perform rule matching.
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
    You can uncomment and run this to perform quick tests.
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


# Main chat loop
if __name__ == '__main__':
    print("Therapist: Hello! How can I help you today?")


    while True:
        user_input = input("You: ")

        # TODO 11:
        # If user input is quit / exit / bye, print farewell and break
        if user_input.lower() in ["quit", "exit","bye"]:
            print("Therapist: Goodbye. It was nice talking to you.")
            break
        update_memory(user_input)

        # TODO 12:
        response = respond(user_input)
        print(f"Therapist: {response}")
        # Call respond(user_input) to get a reply
        # Then print:
        # Therapist: xxx


    # After finishing you can run the quick tests
    run_manual_tests()

"""
========================
Self-test checklist
========================

Level 1: Basic
- Program starts
- Replies to an input
- Input 'quit' exits cleanly

Level 2: Pattern matching
- "I need a rest" triggers I need rule
- "I am tired" triggers I am rule
- Sentences containing 'mother' trigger mother rule
- Other inputs fall back to wildcard rule r'.*'

Level 3: Pronoun swapping
- captured_group = "my book"
- swap_pronouns(captured_group) -> "your book"

Level 4: Extensions
Add any two of the following:
- r'I feel (.*)'
- r'.* father .*'
- special handling for empty input
- support more pronoun replacements
- support Chinese prompts
"""
