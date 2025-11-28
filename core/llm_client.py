"""
LLM Client for VibeMailing
Handles LLM API calls for email personalization (Groq integration).
"""

import time
from typing import Dict, Any, Optional
from openai import OpenAI
from core.logger import get_logger
from core.config_loader import load_settings, load_prompts
from core.template_manager import build_personalization_prompt, inject_data


logger = get_logger()


def load_llm_config() -> Dict[str, Any]:
    """
    Load LLM configuration from settings.

    Returns:
        LLM configuration dictionary
    """
    settings = load_settings()
    llm_config = settings.get('llm', {})

    logger.debug(f"LLM config loaded: model={llm_config.get('model')}")

    return llm_config


def create_llm_client() -> OpenAI:
    """
    Create OpenAI client configured for Groq.

    Returns:
        OpenAI client instance
    """
    config = load_llm_config()

    client = OpenAI(
        api_key=config['api_key'],
        base_url=config['base_url']
    )

    logger.debug("LLM client created")

    return client


def call_llm_api(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = None,
    max_tokens: int = None,
    retry: int = 3
) -> str:
    """
    Call LLM API with retry logic.

    Args:
        prompt: User prompt
        system_prompt: System prompt (optional, uses default from config)
        temperature: Temperature for generation (optional)
        max_tokens: Max tokens for response (optional)
        retry: Number of retry attempts

    Returns:
        Generated text from LLM

    Raises:
        Exception: If all retry attempts fail
    """
    config = load_llm_config()

    # Use config defaults if not specified
    if temperature is None:
        temperature = config.get('temperature', 0.7)
    if max_tokens is None:
        max_tokens = config.get('max_tokens', 500)
    if system_prompt is None:
        prompts_config = load_prompts()
        system_prompt = prompts_config.get('system_prompt', '')

    client = create_llm_client()

    # Build messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    # Retry loop
    last_error = None
    for attempt in range(retry):
        try:
            logger.debug(
                f"LLM API call (attempt {attempt + 1}/{retry}): "
                f"model={config['model']}, temp={temperature}, "
                f"max_tokens={max_tokens}"
            )

            response = client.chat.completions.create(
                model=config['model'],
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Extract text from response
            text = response.choices[0].message.content.strip()

            logger.debug(f"LLM response received: {len(text)} characters")

            return text

        except Exception as e:
            last_error = e
            logger.warning(
                f"LLM API call failed (attempt {attempt + 1}/{retry}): {e}"
            )

            # Exponential backoff
            if attempt < retry - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.debug(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

    # All retries failed
    error_msg = f"LLM API call failed after {retry} attempts: {last_error}"
    logger.error(error_msg)
    raise Exception(error_msg)


def generate_email_content(
    template: Dict[str, Any],
    contact: Dict[str, str],
    use_llm: bool = True
) -> Dict[str, str]:
    """
    Generate complete email content (subject + body) for a contact.

    Args:
        template: Template dictionary
        contact: Contact dictionary
        use_llm: Whether to use LLM for personalization (if False, use template as-is)

    Returns:
        Dictionary with 'subject' and 'body' keys

    Raises:
        Exception: If LLM generation fails and use_llm=True
    """
    logger.info(f"Generating email for {contact['email']}")

    # Generate subject (simple injection, no LLM)
    subject = inject_data(template['subject_template'], contact)

    if use_llm:
        try:
            # Build personalization prompt
            user_prompt = build_personalization_prompt(template, contact)

            # Call LLM
            body = call_llm_api(user_prompt)

            logger.info(f"✓ Email generated (LLM) for {contact['email']}")

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")

            # Fallback to template without personalization
            logger.warning("Falling back to template without LLM personalization")
            body = inject_data(template['body_template'], contact)

    else:
        # Use template directly
        body = inject_data(template['body_template'], contact)
        logger.info(f"✓ Email generated (template) for {contact['email']}")

    return {
        'subject': subject,
        'body': body
    }


def test_llm_connection() -> bool:
    """
    Test LLM API connection.

    Returns:
        True if connection successful, False otherwise
    """
    logger.info("Testing LLM connection...")

    try:
        response = call_llm_api(
            prompt="Say 'Hello' in one word.",
            system_prompt="You are a helpful assistant.",
            max_tokens=10
        )

        logger.info(f"✓ LLM connection test successful: {response}")
        return True

    except Exception as e:
        logger.error(f"✗ LLM connection test failed: {e}")
        return False


def get_llm_info() -> Dict[str, str]:
    """
    Get LLM configuration info (for display).

    Returns:
        Dictionary with LLM info
    """
    config = load_llm_config()

    return {
        'provider': 'Groq',
        'model': config.get('model', 'Unknown'),
        'base_url': config.get('base_url', 'Unknown'),
        'temperature': config.get('temperature', 'Unknown'),
        'max_tokens': config.get('max_tokens', 'Unknown')
    }
