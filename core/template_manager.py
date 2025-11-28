"""
Template Manager for VibeMailing
Handles email template loading and personalization.
"""

from typing import Dict, List, Optional, Any
from core.logger import get_logger
from core.config_loader import load_prompts


logger = get_logger()


def load_templates() -> List[Dict[str, Any]]:
    """
    Load all email templates from configuration.

    Returns:
        List of template dictionaries
    """
    prompts_config = load_prompts()
    templates = prompts_config.get('templates', [])

    logger.debug(f"Loaded {len(templates)} templates")

    return templates


def get_template(name: str) -> Optional[Dict[str, Any]]:
    """
    Get template by name.

    Args:
        name: Template name

    Returns:
        Template dictionary if found, None otherwise
    """
    templates = load_templates()

    for template in templates:
        if template.get('name') == name:
            logger.debug(f"Found template: {name}")
            return template

    logger.warning(f"Template not found: {name}")
    return None


def select_template_interactive() -> Dict[str, Any]:
    """
    Interactive template selection.

    Returns:
        Selected template dictionary

    Raises:
        ValueError: If no templates available
        KeyboardInterrupt: If user cancels
    """
    templates = load_templates()

    if not templates:
        raise ValueError("No templates configured in config/prompts.yaml")

    print("\n" + "="*60)
    print("Email Template Selection")
    print("="*60 + "\n")

    for idx, template in enumerate(templates, 1):
        print(f"  {idx}. {template['name']}")
        subject = template.get('subject_template', 'N/A')
        print(f"     Subject: {subject}")
        print()

    print(f"  {len(templates) + 1}. Cancel")
    print()

    while True:
        try:
            choice = input(f"Select template (1-{len(templates) + 1}): ").strip()

            if not choice:
                continue

            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(templates):
                selected = templates[choice_idx]
                logger.info(f"Selected template: {selected['name']}")
                return selected

            elif choice_idx == len(templates):
                logger.info("Template selection cancelled by user")
                raise KeyboardInterrupt("Template selection cancelled")

            else:
                print(f"Invalid choice. Please enter 1-{len(templates) + 1}")

        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            raise


def inject_data(template_str: str, contact: Dict[str, str]) -> str:
    """
    Inject contact data into template string.
    Replaces placeholders: {name}, {company}, {email}, {linkedin}

    Args:
        template_str: Template string with placeholders
        contact: Contact dictionary

    Returns:
        Template string with placeholders replaced
    """
    replacements = {
        '{name}': contact.get('name', '[Name]'),
        '{company}': contact.get('company', '[Company]'),
        '{email}': contact.get('email', '[Email]'),
        '{linkedin}': contact.get('linkedin', '[LinkedIn Profile]'),
    }

    result = template_str
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)

    return result


def build_personalization_prompt(
    template: Dict[str, Any],
    contact: Dict[str, str]
) -> str:
    """
    Build complete personalization prompt for LLM.

    Args:
        template: Template dictionary
        contact: Contact dictionary

    Returns:
        Complete prompt for LLM
    """
    # Inject contact data into personalization instructions
    personalization = inject_data(
        template.get('personalization_prompt', ''),
        contact
    )

    # Inject contact data into body template
    body_template = inject_data(
        template.get('body_template', ''),
        contact
    )

    # Combine into full prompt
    full_prompt = f"""{personalization}

Original template:
{body_template}

Generate a personalized version of this email. Keep the structure but make it genuine.
Return ONLY the email body, no explanation or meta-commentary.
Do not include the subject line in your response."""

    logger.debug(f"Built personalization prompt for {contact['email']}")

    return full_prompt


def list_template_names() -> List[str]:
    """
    Get list of all template names.

    Returns:
        List of template names
    """
    templates = load_templates()
    return [t['name'] for t in templates]


def get_default_template() -> Dict[str, Any]:
    """
    Get default template (first one in list).

    Returns:
        Default template dictionary

    Raises:
        ValueError: If no templates available
    """
    templates = load_templates()

    if not templates:
        raise ValueError("No templates configured")

    return templates[0]
