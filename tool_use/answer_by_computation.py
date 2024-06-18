from fvalues import F
from typing import Tuple
from ice.recipe import recipe # type: ignore


def make_computation_choice_prompt(question: str) -> str:
    return F(
        f"""You've been asked to answer the question "{question}".

You have access to a Python interpreter.

Enter an expression that will help you answer the question.
>>>"""
    )


def make_computations_script_prompt(question: str, context: list = []) -> str:
    prefix_prompt = F(
        f"""You've been asked to answer the question "{question}".
"""
    )
    if context:
        context_str = F("\n").join(context)
        prefix_prompt += F(f"""\nGiven the following context: {context_str}""")

    suffix_prompt = F(
        """
    You have access to a Python interpreter.

    Enter a whole .py file that will help you answer the question. Use ``` as delimiter.
    .py file: \n"""
    )
    prompt = prefix_prompt + suffix_prompt
    return prompt


def make_compute_qa_prompt(question: str, expression: str, result: str) -> str:
    return F(
        f"""A recording of a Python interpreter session:

Script: \n {expression} \n Script Output: \n {result}

Answer the following question, using the Python session if helpful:

Question: "{question}"
Answer: "
"""
    ).strip()


def eval_python(expression: str) -> str:
    try:
        result = eval(expression)
    except Exception as e:
        result = F(f"Error: {e}")
    return str(result)


async def choose_single_computation(question: str) -> str:
    prompt = make_computation_choice_prompt(question)
    answer = await recipe.agent().complete(prompt=prompt, stop='"')
    return answer.split("\n")[0]


async def choose_complex_computation(question: str, context: list = []) -> str:
    prompt = make_computations_script_prompt(question, context=context)
    answer = await recipe.agent().complete(prompt=prompt)
    return answer.split("```")[1].strip()


def save_script_to_file(script_content: str, file_path: str = "./temp/temp_script.py"):
    with open(file_path, "w") as file:
        file.write(script_content)


def execute_script_file(file_path: str = "./temp/temp_script.py"):
    import subprocess

    return subprocess.run(["python", file_path], capture_output=True, text=True).stdout


async def answer_by_computation(question: str, context: list = []) -> Tuple[str, str]:
    # expression = await choose_single_computation(question)
    script_content = await choose_complex_computation(question, context=context)
    save_script_to_file(script_content, file_path="./temp/temp_script.py")
    result = execute_script_file(file_path="./temp/temp_script.py")
    # result = eval_python(expression)
    prompt = make_compute_qa_prompt(question, script_content, result)
    answer = await recipe.agent().complete(prompt=prompt, stop='"')
    return answer, prompt


recipe.main(answer_by_computation)
