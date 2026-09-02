import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def ask_ollama(prompt: str, model: str = "llama3") -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code} {response.text}")

    data = response.json()
    return data["response"]


if __name__ == "__main__":
    user_prompt = input("Enter prompt: ")
    result = ask_ollama(user_prompt)
    print("\nResponse:\n")
    print(result)
