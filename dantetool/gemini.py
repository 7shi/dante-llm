import sys, time
from llm7shi.compat import generate_with_schema
from . import common

# Set up the model
generation_config = {
    "max_length": 4096,
    "temperature": 0.1,
}

chat_history = None
chat_count = -1
roles = ["user", "assistant"]

MAX_CONSECUTIVE_ERRORS = 3
error_count = 0

def init(model, history=None, system=None, think=None):
    global chat_history, chat_count
    generation_config["model"] = model
    chat_history = []
    if system:
        # Gemma 3 via Gemini API does not support system prompts.
        chat_history.append({"role": "user", "content": system.strip()})
    if history:
        for i, h in enumerate(history):
            chat_history.append({"role": roles[i % 2], "content": h.strip()})
    if think is None:
        if "include_thoughts" in generation_config:
            del generation_config["include_thoughts"]
    else:
        generation_config["include_thoughts"] = think
    chat_count = 0

def query(prompt, info=None, show=False, retry=True, check=None):
    global chat_history, chat_count, error_count
    q = common.query()
    q.prompt = prompt.replace("\r\n", "\n").rstrip()
    history = chat_history + [{"role": roles[0], "content": q.prompt}]
    if info:
        q.info = info.strip()
    if show:
        print()
        if info:
            print(info)
        for line in prompt.split("\n"):
            print(">", line)
        if "file" in generation_config:
            del generation_config["file"]
    else:
        generation_config["file"] = None
    for i in range(3):
        if q.retry:
            if show:
                print()
            for j in range(5, -1, -1):
                print(f"\rRetrying... {j}s ", end="", file=sys.stderr, flush=True)
                if j:
                    time.sleep(1)
            print(file=sys.stderr)
        try:
            response = generate_with_schema(history, show_params=False, **generation_config)
            r = response.text.rstrip()
            if check and (e := check(r)):
                raise(Exception(e))
            q.result = r
            chat_count += 1
            chat_history = history
            chat_history.append({"role": roles[1], "content": response.text})
            break
        except Exception as e:
            err = str(e).rstrip()
            if show:
                print()
            print(err)
            q.error = err
            if not retry:
                break
            q.retry = True
    if q.result:
        error_count = 0
    else:
        error_count += 1
        if 0 < MAX_CONSECUTIVE_ERRORS <= error_count:
            raise Exception(f"Maximum consecutive errors reached: {MAX_CONSECUTIVE_ERRORS}")
    return q
