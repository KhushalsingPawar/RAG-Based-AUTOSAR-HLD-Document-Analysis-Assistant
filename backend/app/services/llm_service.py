import requests


OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL_NAME = "llama3.2"


def generate_llm_response(
    prompt: str
):
    """
    Send a prompt to the local Ollama LLM.
    """

    if not prompt or not prompt.strip():
        return ""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

        return result.get(
            "response",
            ""
        ).strip()

    except requests.exceptions.ConnectionError:

        raise RuntimeError(
            "Ollama is not running. "
            "Please start Ollama and try again."
        )

    except requests.exceptions.Timeout:

        raise RuntimeError(
            "LLM request timed out."
        )

    except requests.exceptions.RequestException as error:

        raise RuntimeError(
            f"LLM request failed: {str(error)}"
        )