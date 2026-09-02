import os
from dotenv import load_dotenv

from src.core.logger import setup_logger
from src.core.provider_factory import get_provider

load_dotenv()

logger = setup_logger()
provider_name = os.getenv("JAI_PROVIDER", "ollama")
logger.info(f"Starting app with provider={provider_name}")

def main():
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

if __name__ == "__main__":
    main()
