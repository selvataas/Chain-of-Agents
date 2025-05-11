from typing import List, Optional, Dict
import requests
import json
import os

class WorkerAgent:
    """Worker agent that processes individual chunks of text."""
    
    def __init__(self, model: str, system_prompt: str):
        """
        Initialize a worker agent.
        
        Args:
            model: The LLM model to use
            system_prompt: The system prompt that defines the worker's role
        """
        self.model = model
        self.system_prompt = system_prompt
        self.api_key = ""  
        self.base_url = "https://api.studio.nebius.com/v1/"
        
    def process_chunk(self, chunk: str, query: str, previous_cu: Optional[str] = None) -> str:
        """
        Process a single chunk of text.
        
        Args:
            chunk: The text chunk to process
            query: The user's query
            previous_cu: The previous Cognitive Unit (CU) if any
            
        Returns:
            str: The processed output for this chunk
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Chunk: {chunk}\nQuery: {query}\nPrevious CU: {previous_cu or 'None'}"}
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024,
            "top_p": 0.9,
            "top_k": 50
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.base_url}chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"API call failed with status code {response.status_code}: {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]

class ManagerAgent:
    """Manager agent that synthesizes outputs from worker agents."""
    
    def __init__(self, model: str, system_prompt: str):
        """
        Initialize a manager agent.
        
        Args:
            model: The LLM model to use
            system_prompt: The system prompt that defines the manager's role
        """
        self.model = model
        self.system_prompt = system_prompt
        self.api_key = ""
        self.base_url = "https://api.studio.nebius.com/v1/"
    
    def synthesize(self, worker_outputs: List[str], query: str) -> str:
        """
        Synthesize outputs from multiple worker agents.
        
        Args:
            worker_outputs: List of outputs from worker agents
            query: The original user query
            
        Returns:
            str: The final synthesized response
        """
        combined_outputs = "\n\n".join(f"Worker {i+1}: {output}" 
                                    for i, output in enumerate(worker_outputs))
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Worker Outputs:\n{combined_outputs}\n\nQuery: {query}"}
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024,
            "top_p": 0.9,
            "top_k": 50
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.base_url}chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"API call failed with status code {response.status_code}: {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]





















# from typing import List, Optional, Dict
# import requests
# import json
# import os

# class WorkerAgent:
#     """Worker agent that processes individual chunks of text."""
    
#     def __init__(self, model: str, system_prompt: str):
#         """
#         Initialize a worker agent.
        
#         Args:
#             model: The LLM model to use (e.g., "meta-llama/Meta-Llama-3.1-8B-Instruct")
#             system_prompt: The system prompt that defines the worker's role
#         """
#         self.model = model
#         self.system_prompt = system_prompt
#         self.api_key = os.environ.get("NEBIUS_API_KEY", "YOUR_ACTUAL_NEBIUS_API_KEY")  # API anahtarını buraya yazın
#         self.base_url = "https://api.studio.nebius.com/v1/"
        
#     def process_chunk(self, chunk: str, query: str, previous_cu: Optional[str] = None) -> str:
#         """
#         Process a single chunk of text.
        
#         Args:
#             chunk: The text chunk to process
#             query: The user's query
#             previous_cu: The previous Cognitive Unit (CU) if any
            
#         Returns:
#             str: The processed output for this chunk
#         """
#         messages = [
#             {"role": "system", "content": self.system_prompt},
#             {"role": "user", "content": f"Chunk: {chunk}\nQuery: {query}\nPrevious CU: {previous_cu or 'None'}"}
#         ]
        
#         data = {
#             "model": self.model,
#             "messages": messages,
#             "temperature": 0.3,
#             "max_tokens": 512,
#             "top_p": 0.9,
#             "top_k": 50
#         }
        
#         headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json"
#         }
        
#         response = requests.post(
#             f"{self.base_url}chat/completions",
#             headers=headers,
#             json=data
#         )
        
#         if response.status_code != 200:
#             raise Exception(f"API call failed with status code {response.status_code}: {response.text}")
        
#         result = response.json()
#         return result["choices"][0]["message"]["content"]

# class ManagerAgent:
#     """Manager agent that synthesizes outputs from worker agents."""
    
#     def __init__(self, model: str, system_prompt: str):
#         """
#         Initialize a manager agent.
        
#         Args:
#             model: The LLM model to use (e.g., "meta-llama/Meta-Llama-3.1-8B-Instruct")
#             system_prompt: The system prompt that defines the manager's role
#         """
#         self.model = model
#         self.system_prompt = system_prompt
#         self.api_key = os.environ.get("NEBIUS_API_KEY", "YOUR_ACTUAL_NEBIUS_API_KEY")  # API anahtarını buraya yazın
#         self.base_url = "https://api.studio.nebius.com/v1/"
    
#     def synthesize(self, worker_outputs: List[str], query: str) -> str:
#         """
#         Synthesize outputs from multiple worker agents.
        
#         Args:
#             worker_outputs: List of outputs from worker agents
#             query: The original user query
            
#         Returns:
#             str: The final synthesized response
#         """
#         combined_outputs = "\n\n".join(f"Worker {i+1}: {output}" 
#                                     for i, output in enumerate(worker_outputs))
        
#         messages = [
#             {"role": "system", "content": self.system_prompt},
#             {"role": "user", "content": f"Worker Outputs:\n{combined_outputs}\n\nQuery: {query}"}
#         ]
        
#         data = {
#             "model": self.model,
#             "messages": messages,
#             "temperature": 0.3,
#             "max_tokens": 1024,
#             "top_p": 0.9,
#             "top_k": 50
#         }
        
#         headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json"
#         }
        
#         response = requests.post(
#             f"{self.base_url}chat/completions",
#             headers=headers,
#             json=data
#         )
        
#         if response.status_code != 200:
#             raise Exception(f"API call failed with status code {response.status_code}: {response.text}")
        
#         result = response.json()
#         return result["choices"][0]["message"]["content"]

