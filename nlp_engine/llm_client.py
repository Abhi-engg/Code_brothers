"""
Ollama LLM Client Wrapper

Custom client for interacting with local Ollama API.
Handles connection management, retries, timeouts, and response parsing.

This is a CUSTOM-BUILT component - all logic is implemented by the team.
External dependency: Ollama API (local LLM server)
"""

import json
import time
import logging
from typing import Optional, Dict, Any, Generator, List
from dataclasses import dataclass
from enum import Enum

import httpx

# Configure logging
logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Base exception for Ollama client errors"""
    pass


class ConnectionError(OllamaError):
    """Raised when cannot connect to Ollama server"""
    pass


class ModelNotFoundError(OllamaError):
    """Raised when requested model is not available"""
    pass


class GenerationError(OllamaError):
    """Raised when text generation fails"""
    pass


class TaskType(str, Enum):
    """Task types with recommended temperature settings"""
    REWRITE = "rewrite"           # Low creativity - faithful corrections
    STYLE_TRANSFORM = "transform"  # Medium creativity - style changes
    STORY_CONTINUE = "story"       # High creativity - narrative generation
    EXPLANATION = "explain"        # Low creativity - clear explanations


# Temperature presets per task type (custom configuration)
TASK_TEMPERATURES = {
    TaskType.REWRITE: 0.3,
    TaskType.STYLE_TRANSFORM: 0.6,
    TaskType.STORY_CONTINUE: 0.85,
    TaskType.EXPLANATION: 0.4,
}


@dataclass
class LLMConfig:
    """Configuration for LLM client"""
    base_url: str = "http://localhost:11434"
    model: str = "llama3.2:3b"  # Llama 3.2 3B - fits in 4GB VRAM, excellent for writing tasks
    default_temperature: float = 0.7
    default_max_tokens: int = 512
    timeout_seconds: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class GenerationResult:
    """Result from text generation"""
    text: str
    model: str
    total_duration_ms: float
    prompt_tokens: int
    completion_tokens: int
    success: bool
    error: Optional[str] = None


class OllamaClient:
    """
    Custom Ollama API Client
    
    Provides:
    - Connection health checking
    - Synchronous and streaming generation
    - JSON-structured output mode
    - Task-specific temperature presets
    - Automatic retry with exponential backoff
    - Response parsing and validation
    
    All client logic is custom-built. Only the Ollama API itself is external.
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize client with configuration"""
        self.config = config or LLMConfig()
        self._client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None
        
    def _get_client(self) -> httpx.Client:
        """Get or create synchronous HTTP client"""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout_seconds)
            )
        return self._client
    
    async def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout_seconds)
            )
        return self._async_client
    
    def close(self):
        """Close HTTP client connections"""
        if self._client:
            self._client.close()
            self._client = None
    
    async def aclose(self):
        """Close async HTTP client connections"""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None
    
    # ==================== Health & Status ====================
    
    def check_status(self) -> Dict[str, Any]:
        """
        Check Ollama server status and model availability.
        
        Returns:
            Dict with status, model info, and response time
        """
        start_time = time.time()
        
        try:
            client = self._get_client()
            response = client.get("/api/tags")
            response.raise_for_status()
            
            elapsed_ms = (time.time() - start_time) * 1000
            data = response.json()
            
            # Check if our model is available
            models = data.get("models", [])
            model_names = [m.get("name", "") for m in models]
            model_available = self.config.model in model_names
            
            # Get model details if available
            model_info = None
            for m in models:
                if m.get("name") == self.config.model:
                    model_info = {
                        "name": m.get("name"),
                        "size_gb": round(m.get("size", 0) / (1024**3), 2),
                        "parameter_size": m.get("details", {}).get("parameter_size", "unknown"),
                        "quantization": m.get("details", {}).get("quantization_level", "unknown")
                    }
                    break
            
            return {
                "status": "ok" if model_available else "model_not_found",
                "connected": True,
                "model": self.config.model,
                "model_available": model_available,
                "model_info": model_info,
                "available_models": model_names,
                "response_time_ms": round(elapsed_ms, 2)
            }
            
        except httpx.ConnectError:
            return {
                "status": "error",
                "connected": False,
                "model": self.config.model,
                "model_available": False,
                "error": "Cannot connect to Ollama server. Is it running?",
                "hint": "Run 'ollama serve' to start the server"
            }
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "model": self.config.model,
                "error": str(e)
            }
    
    async def check_status_async(self) -> Dict[str, Any]:
        """Async version of check_status"""
        start_time = time.time()
        
        try:
            client = await self._get_async_client()
            response = await client.get("/api/tags")
            response.raise_for_status()
            
            elapsed_ms = (time.time() - start_time) * 1000
            data = response.json()
            
            models = data.get("models", [])
            model_names = [m.get("name", "") for m in models]
            model_available = self.config.model in model_names
            
            model_info = None
            for m in models:
                if m.get("name") == self.config.model:
                    model_info = {
                        "name": m.get("name"),
                        "size_gb": round(m.get("size", 0) / (1024**3), 2),
                        "parameter_size": m.get("details", {}).get("parameter_size", "unknown"),
                        "quantization": m.get("details", {}).get("quantization_level", "unknown")
                    }
                    break
            
            return {
                "status": "ok" if model_available else "model_not_found",
                "connected": True,
                "model": self.config.model,
                "model_available": model_available,
                "model_info": model_info,
                "available_models": model_names,
                "response_time_ms": round(elapsed_ms, 2)
            }
            
        except httpx.ConnectError:
            return {
                "status": "error",
                "connected": False,
                "model": self.config.model,
                "model_available": False,
                "error": "Cannot connect to Ollama server. Is it running?"
            }
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "model": self.config.model,
                "error": str(e)
            }
    
    def is_available(self) -> bool:
        """Quick check if LLM is available"""
        status = self.check_status()
        return status.get("status") == "ok"
    
    # ==================== Text Generation ====================
    
    def _build_generate_payload(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        json_mode: bool = False,
        stop_sequences: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Build request payload for generation endpoint"""
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature or self.config.default_temperature,
                "num_predict": max_tokens or self.config.default_max_tokens,
            }
        }
        
        if json_mode:
            payload["format"] = "json"
        
        if stop_sequences:
            payload["options"]["stop"] = stop_sequences
        
        return payload
    
    def generate(
        self,
        prompt: str,
        task_type: Optional[TaskType] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> GenerationResult:
        """
        Generate text completion synchronously.
        
        Args:
            prompt: The input prompt
            task_type: Optional task type for automatic temperature selection
            temperature: Override temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stop_sequences: List of strings that stop generation
            
        Returns:
            GenerationResult with generated text and metadata
        """
        # Use task-specific temperature if not overridden
        if temperature is None and task_type:
            temperature = TASK_TEMPERATURES.get(task_type, self.config.default_temperature)
        
        payload = self._build_generate_payload(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            stop_sequences=stop_sequences
        )
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                client = self._get_client()
                response = client.post("/api/generate", json=payload)
                response.raise_for_status()
                
                data = response.json()
                
                return GenerationResult(
                    text=data.get("response", "").strip(),
                    model=data.get("model", self.config.model),
                    total_duration_ms=data.get("total_duration", 0) / 1_000_000,  # ns to ms
                    prompt_tokens=data.get("prompt_eval_count", 0),
                    completion_tokens=data.get("eval_count", 0),
                    success=True
                )
                
            except httpx.ConnectError as e:
                last_error = f"Connection failed: {e}"
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP error: {e.response.status_code}"
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
            
            # Wait before retry (exponential backoff)
            if attempt < self.config.max_retries - 1:
                time.sleep(self.config.retry_delay * (2 ** attempt))
        
        return GenerationResult(
            text="",
            model=self.config.model,
            total_duration_ms=0,
            prompt_tokens=0,
            completion_tokens=0,
            success=False,
            error=last_error
        )
    
    async def generate_async(
        self,
        prompt: str,
        task_type: Optional[TaskType] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> GenerationResult:
        """Async version of generate"""
        if temperature is None and task_type:
            temperature = TASK_TEMPERATURES.get(task_type, self.config.default_temperature)
        
        payload = self._build_generate_payload(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            stop_sequences=stop_sequences
        )
        
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                client = await self._get_async_client()
                response = await client.post("/api/generate", json=payload)
                response.raise_for_status()
                
                data = response.json()
                
                return GenerationResult(
                    text=data.get("response", "").strip(),
                    model=data.get("model", self.config.model),
                    total_duration_ms=data.get("total_duration", 0) / 1_000_000,
                    prompt_tokens=data.get("prompt_eval_count", 0),
                    completion_tokens=data.get("eval_count", 0),
                    success=True
                )
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Async attempt {attempt + 1} failed: {last_error}")
            
            if attempt < self.config.max_retries - 1:
                import asyncio
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
        
        return GenerationResult(
            text="",
            model=self.config.model,
            total_duration_ms=0,
            prompt_tokens=0,
            completion_tokens=0,
            success=False,
            error=last_error
        )
    
    def generate_stream(
        self,
        prompt: str,
        task_type: Optional[TaskType] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Generator[str, None, None]:
        """
        Generate text with streaming output.
        
        Yields tokens as they are generated for real-time display.
        
        Args:
            prompt: The input prompt
            task_type: Optional task type for temperature
            temperature: Override temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            String tokens as they are generated
        """
        if temperature is None and task_type:
            temperature = TASK_TEMPERATURES.get(task_type, self.config.default_temperature)
        
        payload = self._build_generate_payload(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        try:
            client = self._get_client()
            with client.stream("POST", "/api/generate", json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield token
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Stream generation failed: {e}")
            yield f"[Error: {e}]"
    
    async def generate_stream_async(
        self,
        prompt: str,
        task_type: Optional[TaskType] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Async streaming generation.
        
        Yields tokens as they are generated.
        """
        if temperature is None and task_type:
            temperature = TASK_TEMPERATURES.get(task_type, self.config.default_temperature)
        
        payload = self._build_generate_payload(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        try:
            client = await self._get_async_client()
            async with client.stream("POST", "/api/generate", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield token
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Async stream generation failed: {e}")
            yield f"[Error: {e}]"
    
    # ==================== JSON Structured Output ====================
    
    def generate_json(
        self,
        prompt: str,
        schema_hint: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output.
        
        Uses Ollama's JSON mode to force valid JSON responses.
        
        Args:
            prompt: The input prompt (should describe expected JSON structure)
            schema_hint: Optional hint about expected schema to append to prompt
            task_type: Task type for temperature
            temperature: Override temperature
            
        Returns:
            Parsed JSON as dictionary, or {"error": "..."} on failure
        """
        if temperature is None and task_type:
            temperature = TASK_TEMPERATURES.get(task_type, self.config.default_temperature)
        
        # Append schema hint if provided
        full_prompt = prompt
        if schema_hint:
            full_prompt = f"{prompt}\n\nExpected JSON format:\n{schema_hint}"
        
        payload = self._build_generate_payload(
            prompt=full_prompt,
            temperature=temperature,
            max_tokens=self.config.default_max_tokens,
            stream=False,
            json_mode=True
        )
        
        try:
            client = self._get_client()
            response = client.post("/api/generate", json=payload)
            response.raise_for_status()
            
            data = response.json()
            response_text = data.get("response", "").strip()
            
            # Parse JSON response
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {"error": f"Invalid JSON response: {e}", "raw": response_text}
        except Exception as e:
            logger.error(f"JSON generation failed: {e}")
            return {"error": str(e)}
    
    # ==================== Chat Interface ====================
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        task_type: Optional[TaskType] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> GenerationResult:
        """
        Multi-turn chat completion.
        
        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
            task_type: Task type for temperature
            temperature: Override temperature
            max_tokens: Maximum tokens
            
        Returns:
            GenerationResult with assistant's response
        """
        if temperature is None and task_type:
            temperature = TASK_TEMPERATURES.get(task_type, self.config.default_temperature)
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.default_temperature,
                "num_predict": max_tokens or self.config.default_max_tokens,
            }
        }
        
        try:
            client = self._get_client()
            response = client.post("/api/chat", json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            return GenerationResult(
                text=data.get("message", {}).get("content", "").strip(),
                model=data.get("model", self.config.model),
                total_duration_ms=data.get("total_duration", 0) / 1_000_000,
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0),
                success=True
            )
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return GenerationResult(
                text="",
                model=self.config.model,
                total_duration_ms=0,
                prompt_tokens=0,
                completion_tokens=0,
                success=False,
                error=str(e)
            )


# ==================== Global Instance ====================

# Default client instance (lazy initialized)
_default_client: Optional[OllamaClient] = None


def get_client(config: Optional[LLMConfig] = None) -> OllamaClient:
    """Get or create the default Ollama client instance"""
    global _default_client
    if _default_client is None:
        _default_client = OllamaClient(config)
    return _default_client


def reset_client():
    """Reset the default client (useful for testing)"""
    global _default_client
    if _default_client:
        _default_client.close()
        _default_client = None


# ==================== Convenience Functions ====================

def check_ollama_status() -> Dict[str, Any]:
    """Check Ollama server status using default client"""
    return get_client().check_status()


def generate_completion(
    prompt: str,
    task_type: Optional[TaskType] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> str:
    """
    Generate text completion using default client.
    
    Returns the generated text, or empty string on error.
    """
    result = get_client().generate(
        prompt=prompt,
        task_type=task_type,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return result.text if result.success else ""


def generate_json_response(
    prompt: str,
    schema_hint: Optional[str] = None
) -> Dict[str, Any]:
    """Generate structured JSON using default client"""
    return get_client().generate_json(prompt, schema_hint)


def stream_completion(
    prompt: str,
    task_type: Optional[TaskType] = None,
    temperature: Optional[float] = None
) -> Generator[str, None, None]:
    """Stream text generation using default client"""
    return get_client().generate_stream(
        prompt=prompt,
        task_type=task_type,
        temperature=temperature
    )


# ==================== Testing ====================

if __name__ == "__main__":
    """Test the Ollama client"""
    print("Testing Ollama Client...")
    print("=" * 50)
    
    # Test 1: Status check
    print("\n1. Checking Ollama status...")
    status = check_ollama_status()
    print(f"   Status: {status.get('status')}")
    print(f"   Model: {status.get('model')}")
    print(f"   Available: {status.get('model_available')}")
    if status.get('model_info'):
        print(f"   Size: {status['model_info'].get('size_gb')} GB")
    
    if status.get('status') != 'ok':
        print(f"\n   Error: {status.get('error')}")
        print("   Cannot proceed with generation tests.")
        exit(1)
    
    # Test 2: Simple generation
    print("\n2. Testing simple generation...")
    result = get_client().generate(
        prompt="Complete this sentence in exactly 5 words: The weather today is",
        task_type=TaskType.REWRITE,
        max_tokens=20
    )
    print(f"   Success: {result.success}")
    print(f"   Response: {result.text}")
    print(f"   Duration: {result.total_duration_ms:.0f}ms")
    
    # Test 3: JSON generation
    print("\n3. Testing JSON generation...")
    json_result = get_client().generate_json(
        prompt="List 3 colors as a JSON array with key 'colors'",
        schema_hint='{"colors": ["red", "blue", "green"]}'
    )
    print(f"   Result: {json_result}")
    
    # Test 4: Streaming (show first 50 chars)
    print("\n4. Testing streaming generation...")
    print("   Output: ", end="")
    char_count = 0
    for token in stream_completion("Write a haiku about coding:", TaskType.STORY_CONTINUE):
        print(token, end="", flush=True)
        char_count += len(token)
        if char_count > 100:
            print("...")
            break
    print()
    
    print("\n" + "=" * 50)
    print("All tests completed!")
