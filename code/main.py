import os
import json
from dotenv import load_dotenv

from src.core.logger import setup_logger
from src.core.provider_factory import get_provider

from jai.eval.runner import run_all


load_dotenv()

logger = setup_logger()
provider_name = os.getenv("JAI_PROVIDER", "ollama")
logger.info(f"Starting app with provider={provider_name}")


def chat_mode():
    provider = get_provider()
    print("J_AI Local Assistant (type 'exit' to quit)\n")

    while True:
        user_input = input("You: ")
        logger.info(f"Prompt: {user_input}")

        if user_input.lower() == "exit":
            break

        try:
            response = provider.generate(user_input)
            logger.info("Response generated successfully")
            print("\nAI:\n")
            print(response)
            print("\n")
        except Exception:
            logger.exception("Error during generation")
            print("\nError: something went wrong. Check logs/j_ai.log\n")


def eval_mode():
    data_path = os.getenv("JAI_EVAL_ANSWERS", "")
    if not data_path:
        print("Set JAI_EVAL_ANSWERS to a JSON file path that contains your answers.")
        print("Example content: {\"REQ_001\": \"your answer here\", \"LOG_001\": \"...\"}")
        return

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            student_answers = json.load(f)
    except Exception:
        print("Could not read JAI_EVAL_ANSWERS file. Make sure it is valid JSON.")
        return

    if not isinstance(student_answers, dict):
        print("JAI_EVAL_ANSWERS must be a JSON object mapping case ids to answers, e.g. {\"REQ_001\": \"...\"}.")
        return

    run_all(student_answers)


def main():
    mode = os.getenv("JAI_MODE", "chat").lower()
    if mode == "eval":
        eval_mode()
    else:
        chat_mode()


if __name__ == "__main__":
    main()
