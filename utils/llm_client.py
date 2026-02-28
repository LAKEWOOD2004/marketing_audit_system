import os
import json
from typing import Optional, Dict, Any, List
from openai import OpenAI
from config.settings import LLM_CONFIG


class LLMClient:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or LLM_CONFIG
        self.provider = self.config.get("provider", "openai")
        self.client = self._init_client()
    
    def _init_client(self):
        api_key = self.config.get("api_key") or os.getenv("ZHIPU_API_KEY") or os.getenv("OPENAI_API_KEY", "")
        base_url = self.config.get("base_url")
        
        if self.provider == "zhipu":
            try:
                from zhipuai import ZhipuAI
                return ZhipuAI(api_key=api_key)
            except ImportError:
                return OpenAI(
                    api_key=api_key,
                    base_url=base_url or "https://open.bigmodel.cn/api/paas/v4"
                )
        else:
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            return OpenAI(**client_kwargs)
    
    def chat(self, 
             messages: List[Dict[str, str]], 
             temperature: Optional[float] = None,
             max_tokens: Optional[int] = None,
             response_format: Optional[Dict] = None) -> str:
        
        model = self.config.get("model", "glm-4")
        temp = temperature or self.config.get("temperature", 0.1)
        tokens = max_tokens or self.config.get("max_tokens", 4096)
        
        if self.provider == "zhipu" and hasattr(self.client, 'chat'):
            try:
                from zhipuai import ZhipuAI
                if isinstance(self.client, ZhipuAI):
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temp,
                        max_tokens=tokens
                    )
                    return response.choices[0].message.content
            except Exception:
                pass
        
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
        }
        
        if response_format and self.provider != "zhipu":
            kwargs["response_format"] = response_format
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    def chat_with_system(self,
                         system_prompt: str,
                         user_message: str,
                         temperature: Optional[float] = None) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        return self.chat(messages, temperature=temperature)
    
    def chat_json(self,
                  system_prompt: str,
                  user_message: str,
                  temperature: Optional[float] = None) -> Dict[str, Any]:
        enhanced_prompt = system_prompt + "\n\n请确保返回有效的JSON格式。"
        
        messages = [
            {"role": "system", "content": enhanced_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = self.chat(messages, temperature=temperature)
            
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()
            
            if json_str.startswith("[") or json_str.startswith("{"):
                return json.loads(json_str)
            else:
                return {"raw_response": response, "error": "Not valid JSON format"}
                
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse JSON response: {str(e)}", "raw": response}
        except Exception as e:
            return {"error": str(e)}


llm_client = LLMClient()
