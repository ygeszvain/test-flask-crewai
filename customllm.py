import litellm
from crewai import LLM, Agent, Task, Crew

class CustomLiteLLM(LLM):
    def __init__(self, api_url: str, api_key: str, model: str = "gpt-4", **kwargs):
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        super().__init__(model=self.model, **kwargs)

    def call(self, prompt: str, **kwargs) -> str:
        """Sends a request to the external LLM API and returns the response."""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 512)
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        except requests.exceptions.RequestException as e:
            print(f"Error calling LLM API: {e}")
            return ""

# Initialize the custom LLM with your API details
custom_llm = CustomLiteLLM(api_url="https://api.openai.com/v1/chat/completions", api_key="your_api_key")
