# CHAT BOT THEME - MAGIC 8 BALL
# API RULES
# CHAT CAN BE NO LONGER THAN 20 REQUESTS PER MINUTE
# ...
import json
import os
from textwrap import dedent

import cohere
from dotenv import find_dotenv, load_dotenv, set_key
from rich.columns import Columns
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt

from console import console

dotenv_file = find_dotenv()
load_dotenv(dotenv_file)
co_api_key = os.getenv("API_KEY")
co = cohere.ClientV2(api_key=co_api_key)


def get_content(id: int, model: str, model_details: dict) -> str:
    result: str = dedent(
        f"""[b cyan]ID: {id + 1}[/b cyan]\nType: {model}\n[magenta]Name: {model_details.get("name")}[/magenta]\n[yellow]Description: {model_details.get("description")}[/yellow]\n[green]Usage: {model_details.get("usage")}[/green]"""
    )
    return result


def load_models():
    with open("models.json") as content:
        models: dict = json.load(content)
        return models


def show_models(model_renderables: list):
    console.print(
        Columns(
            model_renderables,
            equal=True,
            column_first=True,
            expand=True,
            title="MODELS",
        )
    )


def create_model_panels(models: dict):
    model_renderables = []
    for id, model in enumerate(models):
        model_details = models[model]
        panel = Panel(
            get_content(id, model, model_details),
            title="MODEL",
            title_align="left",
        )
        model_renderables.append(panel)
    return model_renderables


def set_model(models: dict) -> str:
    models_keys_list = list(models.keys())

    choice = IntPrompt.ask("Choose model:", choices=["1", "2", "3", "4"])

    model: str = models_keys_list[choice - 1]

    return model


def process_response(
    model: str,
    user_input: str,
    system_instruction: str,
):
    # response = co.chat_stream(
    response = co.chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_instruction,
            },
            {
                "role": "user",
                "content": user_input,
            },
        ],
        thinking={"type": "disabled"},
    )

    return response.message.content[0].text
    # return response


def select_model(models):
    option = Prompt.ask("View models?", choices=["Yes", "No"], case_sensitive=False)

    if option == "Yes":
        show_models(model_renderables)

    model = set_model(models)

    model_details = models[model]

    return model, model_details


def check_rate_limit():
    # warn on rate limit
    # 20 request per minute
    pass


def check_key_state(curr_count):
    """
    Track key call count. 1000 responses per month. Warn on key limit.
    """
    if curr_count >= 1000:
        console.print("[yellow i]Key is dead. Update your API key.[/yellow i]")


def increment_kcc(count: int):
    """
    Increment key call count (kcc).
    """
    curr_kcc = int(os.getenv("KEY_HP"))
    if count > 0:
        curr_kcc += count

        check_key_state(curr_kcc)

        os.environ["KEY_HP"] = str(curr_kcc)
        set_key(dotenv_file, "KEY_HP", os.environ["KEY_HP"])


if __name__ == "__main__":
    models = load_models()  # load it once
    model_renderables = create_model_panels(models)  # create once

    console.print("Simple Chatbot")

    try:
        user_name = Prompt.ask("[Optional] Enter name", default="User")

        model, model_details = select_model(models)
    except (KeyboardInterrupt, SystemExit):
        exit()

    session_request_counter = -1
    while True:
        try:
            user_input = Prompt.ask(f"[bold yellow]{user_name}[/bold yellow]")
            while user_input == "":
                user_input = Prompt.ask(user_name)
                if user_input:
                    break

            response = process_response(
                model,
                user_input,
                model_details.get("system_instruction"),
            )

            if response and user_input == "quit":
                increment_kcc(session_request_counter)
                break

        except (KeyboardInterrupt, SystemExit):
            increment_kcc(session_request_counter)
            break

        except Exception as e:
            print(e)
            increment_kcc(session_request_counter)
            break

        else:
            session_request_counter += 1  # each response deals 1 damage to KEY_HP
            console.print(f"[magenta]{model_details.get('name')}: 🤔...[/magenta]")
            # display buffer indicator
            # before printing response when response
            # is fully loaded.
            md = Markdown(response)
            console.print(md)
            # for event in response:
            #     if event.type == "content-delta":
            #         md = Markdown(event.delta.message.content.text)
            #         console.print(md, end="")

        finally:
            increment_kcc(session_request_counter)
