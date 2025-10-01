"""
Custom Gemini Model Client for AutoGen 0.7.x

Wraps google-generativeai SDK to work with AutoGen's ChatCompletionClient interface.
"""

import google.generativeai as genai
from typing import List, Dict, Any, Optional, Sequence
from autogen_core.components.models import (
    ChatCompletionClient,
    CreateResult,
    LLMMessage,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    FunctionExecutionResultMessage,
)
import logging

logger = logging.getLogger(__name__)


class GeminiChatCompletionClient(ChatCompletionClient):
    """
    Custom Gemini client compatible with AutoGen 0.7.x architecture.

    Implements ChatCompletionClient interface using google-generativeai SDK.
    """

    def __init__(
        self,
        model: str = "gemini-2.5-flash-lite",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Initialize Gemini client.

        Args:
            model: Gemini model name (e.g., "gemini-2.5-flash-lite", "gemini-1.5-pro")
            api_key: Google API key
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional configuration options
        """
        self.model_name = model
        self.temperature = temperature

        # Configure Google API
        if api_key:
            genai.configure(api_key=api_key)

        # Create generation config
        self.generation_config = {
            "temperature": temperature,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }

        # Safety settings (permissive for scientific content)
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=model,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
        )

        logger.info(f"Initialized Gemini client with model: {model}")

    def _convert_messages(self, messages: Sequence[LLMMessage]) -> List[Dict[str, Any]]:
        """
        Convert AutoGen messages to Gemini format.

        AutoGen uses: SystemMessage, UserMessage, AssistantMessage, FunctionExecutionResultMessage
        Gemini uses: role="user" or role="model", with parts=[{"text": "..."}]

        Note: Gemini doesn't have a separate "system" role, so we prepend system messages
        to the first user message.
        """
        gemini_messages = []
        system_content = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                # Collect system messages to prepend later
                system_content.append(msg.content)

            elif isinstance(msg, UserMessage):
                content = msg.content
                # Prepend system messages if this is the first user message
                if system_content:
                    content = "\n\n".join(system_content) + "\n\n" + content
                    system_content = []

                gemini_messages.append({
                    "role": "user",
                    "parts": [{"text": content}]
                })

            elif isinstance(msg, AssistantMessage):
                gemini_messages.append({
                    "role": "model",
                    "parts": [{"text": msg.content}]
                })

            elif isinstance(msg, FunctionExecutionResultMessage):
                # Treat function results as user messages
                gemini_messages.append({
                    "role": "user",
                    "parts": [{"text": f"Function result: {msg.content}"}]
                })

        return gemini_messages

    async def create(
        self,
        messages: Sequence[LLMMessage],
        *,
        tools: Sequence[Any] = [],
        json_output: Optional[bool] = None,
        extra_create_args: Dict[str, Any] = {},
        cancellation_token: Optional[Any] = None,
    ) -> CreateResult:
        """
        Create a completion using Gemini API.

        Args:
            messages: List of messages in AutoGen format
            tools: List of tools (not fully supported yet)
            json_output: Whether to force JSON output
            extra_create_args: Additional arguments
            cancellation_token: Cancellation token

        Returns:
            CreateResult with response
        """
        try:
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages(messages)

            # Start chat with history (all but last message)
            chat = self.model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])

            # Send last message
            last_message = gemini_messages[-1]["parts"][0]["text"]
            response = await chat.send_message_async(last_message)

            # Extract response text
            response_text = response.text

            # Calculate token usage (approximate)
            prompt_tokens = sum(len(msg["parts"][0]["text"].split()) for msg in gemini_messages)
            completion_tokens = len(response_text.split())

            # Return CreateResult
            return CreateResult(
                finish_reason="stop",
                content=response_text,
                usage={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
                cached=False,
            )

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    def actual_usage(self) -> Dict[str, int]:
        """Return actual token usage (not tracked in this implementation)."""
        return {}

    def total_usage(self) -> Dict[str, int]:
        """Return total token usage (not tracked in this implementation)."""
        return {}

    def count_tokens(self, messages: Sequence[LLMMessage], *, tools: Sequence[Any] = []) -> int:
        """Estimate token count for messages."""
        # Simple word-based approximation
        total_words = 0
        for msg in messages:
            if hasattr(msg, 'content'):
                total_words += len(str(msg.content).split())
        return int(total_words * 1.3)  # Approximate 1.3 tokens per word

    def remaining_tokens(self, messages: Sequence[LLMMessage], *, tools: Sequence[Any] = []) -> int:
        """Calculate remaining tokens in context window."""
        # Gemini 2.5 Flash Lite has 1M token context
        context_limit = 1_000_000
        used = self.count_tokens(messages, tools=tools)
        return context_limit - used

    @property
    def capabilities(self) -> Dict[str, Any]:
        """Return model capabilities."""
        return {
            "vision": False,
            "function_calling": False,
            "json_output": False,
            "context_window": 1_000_000,  # 1M tokens for most Gemini models
        }
