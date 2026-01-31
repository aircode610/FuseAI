"""
Zapier Action Mapper Module

This module provides functionality to map natural language requirements
to Zapier actions, including triggers, read actions, and write actions.
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Enumeration of Zapier action types."""
    TRIGGER = "trigger"
    READ = "read"
    WRITE = "write"


@dataclass
class ZapierAction:
    """
    Represents a Zapier action configuration.
    
    Attributes:
        service: The service name (e.g., "Trello", "Slack")
        action_type: Type of action ("trigger", "read", or "write")
        action_name: Specific Zapier action name
        config: Configuration dictionary for the action
    """
    service: str
    action_type: str
    action_name: str
    config: dict

    def __post_init__(self):
        """Validate action_type after initialization."""
        valid_types = [ActionType.TRIGGER.value, ActionType.READ.value, ActionType.WRITE.value]
        if self.action_type not in valid_types:
            raise ValueError(
                f"Invalid action_type: {self.action_type}. "
                f"Must be one of: {', '.join(valid_types)}"
            )


# Service mappings for supported services
SUPPORTED_SERVICES: Set[str] = {
    # Project Management
    "trello", "asana", "jira",
    # Communication
    "slack", "discord", "microsoft teams", "teams",
    # Development
    "github", "gitlab",
    # CRM
    "salesforce", "hubspot",
    # Other
    "google sheets", "email", "gmail", "webhooks", "webhook"
}

# Trigger name mappings
TRIGGER_PATTERNS: Dict[str, Dict[str, str]] = {
    "trello": {
        "card.*move": "Card Moved to List",
        "card.*create": "New Card",
        "card.*update": "Card Updated",
        "card.*comment": "New Comment on Card",
        "default": "New Card"
    },
    "asana": {
        "task.*complete": "Task Completed",
        "task.*create": "New Task",
        "task.*update": "Task Updated",
        "project.*create": "New Project",
        "default": "New Task"
    },
    "jira": {
        "issue.*create": "New Issue",
        "issue.*update": "Issue Updated",
        "issue.*comment": "New Comment",
        "default": "New Issue"
    },
    "github": {
        "issue.*create": "New Issue",
        "pull.*request": "New Pull Request",
        "push": "New Push",
        "commit": "New Commit",
        "default": "New Issue"
    },
    "gitlab": {
        "issue.*create": "New Issue",
        "merge.*request": "New Merge Request",
        "push": "New Push",
        "default": "New Issue"
    },
    "salesforce": {
        "lead.*create": "New Lead",
        "contact.*create": "New Contact",
        "opportunity.*create": "New Opportunity",
        "default": "New Lead"
    },
    "hubspot": {
        "contact.*create": "New Contact",
        "deal.*create": "New Deal",
        "company.*create": "New Company",
        "default": "New Contact"
    }
}

# Read action mappings
READ_ACTION_MAPPINGS: Dict[str, List[str]] = {
    "trello": ["Get Cards", "Get Board", "Get Lists", "Get Card", "Get Comments"],
    "asana": ["Get Tasks", "Get Project", "Get Task", "Get Projects"],
    "jira": ["Get Issues", "Get Issue", "Get Projects", "Get Project"],
    "github": ["Get Issues", "Get Pull Requests", "Get Repository", "Get Commits"],
    "gitlab": ["Get Issues", "Get Merge Requests", "Get Repository"],
    "salesforce": ["Get Lead", "Get Contact", "Get Opportunity", "Search Records"],
    "hubspot": ["Get Contact", "Get Deal", "Get Company", "Search Contacts"],
    "google sheets": ["Get Spreadsheet", "Get Worksheet", "Get Rows"],
    "slack": ["Get Channel", "Get User", "Get Message"],
    "discord": ["Get Channel", "Get Message"],
    "microsoft teams": ["Get Channel", "Get Message"],
    "email": ["Get Emails", "Search Emails"],
    "gmail": ["Get Emails", "Search Emails"]
}

# Write action mappings
WRITE_ACTION_MAPPINGS: Dict[str, List[str]] = {
    "slack": ["Send Channel Message", "Post to Channel", "Send Direct Message"],
    "discord": ["Send Channel Message", "Send Direct Message"],
    "microsoft teams": ["Send Channel Message", "Post Message"],
    "teams": ["Send Channel Message", "Post Message"],
    "email": ["Send Email"],
    "gmail": ["Send Email"],
    "trello": ["Create Card", "Update Card", "Add Comment"],
    "asana": ["Create Task", "Update Task", "Add Comment"],
    "jira": ["Create Issue", "Update Issue", "Add Comment"],
    "github": ["Create Issue", "Create Comment", "Create Pull Request"],
    "gitlab": ["Create Issue", "Create Merge Request", "Add Comment"],
    "salesforce": ["Create Lead", "Create Contact", "Update Record"],
    "hubspot": ["Create Contact", "Create Deal", "Update Contact"],
    "google sheets": ["Create Row", "Update Row", "Append Row"]
}

# Action synonym mappings
ACTION_SYNONYMS: Dict[str, List[str]] = {
    "send": ["send", "post", "notify", "message", "deliver"],
    "create": ["create", "add", "new", "make"],
    "update": ["update", "modify", "change", "edit"],
    "get": ["get", "fetch", "retrieve", "read", "load"],
    "move": ["move", "transfer", "shift"],
    "complete": ["complete", "finish", "done", "close"],
    "track": ["track", "monitor", "watch", "follow"]
}


def normalize_service_name(service: str) -> str:
    """
    Normalize service name to lowercase for consistent matching.
    
    Args:
        service: Service name to normalize
        
    Returns:
        Normalized service name
    """
    return service.lower().strip()


def is_service_supported(service: str) -> bool:
    """
    Check if a service is supported by the mapper.
    
    Args:
        service: Service name to check
        
    Returns:
        True if service is supported, False otherwise
    """
    normalized = normalize_service_name(service)
    return normalized in SUPPORTED_SERVICES


def get_available_actions(service: str) -> List[str]:
    """
    Get all available actions for a given service.
    
    Args:
        service: Service name
        
    Returns:
        List of available action names
        
    Raises:
        ValueError: If service is not supported
    """
    normalized = normalize_service_name(service)
    
    if not is_service_supported(normalized):
        raise ValueError(
            f"Service '{service}' is not supported. "
            f"Supported services: {', '.join(sorted(SUPPORTED_SERVICES))}"
        )
    
    actions = []
    
    # Add triggers if available
    if normalized in TRIGGER_PATTERNS:
        trigger_actions = set(TRIGGER_PATTERNS[normalized].values())
        actions.extend(sorted(trigger_actions))
    
    # Add read actions
    if normalized in READ_ACTION_MAPPINGS:
        actions.extend(READ_ACTION_MAPPINGS[normalized])
    
    # Add write actions
    if normalized in WRITE_ACTION_MAPPINGS:
        actions.extend(WRITE_ACTION_MAPPINGS[normalized])
    
    return sorted(list(set(actions))) if actions else []


def infer_trigger_name(requirements: dict) -> str:
    """
    Determine the appropriate Zapier trigger based on requirements.
    
    Handles common patterns like:
    - "when card moves" → "Card Moved to List"
    - "new issue created" → "New Issue"
    - "task completed" → "Task Completed"
    
    Args:
        requirements: Requirements dictionary containing:
            - source_service: Source service name
            - action: Action description (optional)
            - trigger_type: Type of trigger (optional)
            - data_flow: Additional context (optional)
    
    Returns:
        Trigger action name
        
    Raises:
        ValueError: If source_service is not supported or no trigger can be inferred
    """
    source_service = requirements.get("source_service", "").lower()
    action = requirements.get("action", "").lower()
    trigger_type = requirements.get("trigger_type", "").lower()
    data_flow = requirements.get("data_flow", {})
    
    # Normalize service name
    normalized_service = normalize_service_name(source_service)
    
    if not is_service_supported(normalized_service):
        raise ValueError(
            f"Source service '{source_service}' is not supported. "
            f"Supported services: {', '.join(sorted(SUPPORTED_SERVICES))}"
        )
    
    # Check if service has trigger patterns
    if normalized_service not in TRIGGER_PATTERNS:
        logger.warning(
            f"No trigger patterns found for service '{source_service}'. "
            f"Using default webhook trigger."
        )
        return "Webhook" if trigger_type == "webhook" else "Manual Trigger"
    
    patterns = TRIGGER_PATTERNS[normalized_service]
    action_text = f"{action} {data_flow.get('description', '')}".lower()
    
    # Try to match patterns
    for pattern, trigger_name in patterns.items():
        if pattern == "default":
            continue
        
        if re.search(pattern, action_text, re.IGNORECASE):
            logger.info(
                f"Matched trigger pattern '{pattern}' for service '{source_service}': {trigger_name}"
            )
            return trigger_name
    
    # Return default trigger for the service
    default_trigger = patterns.get("default", "New Item")
    logger.info(
        f"Using default trigger for service '{source_service}': {default_trigger}"
    )
    return default_trigger


def infer_read_action(requirements: dict) -> str:
    """
    Determine the read action for on-demand or scheduled agents.
    
    Examples:
    - Trello: "Get Cards", "Get Board"
    - Asana: "Get Tasks", "Get Project"
    - GitHub: "Get Issues", "Get Pull Requests"
    
    Args:
        requirements: Requirements dictionary containing:
            - source_service: Source service name
            - action: Action description (optional)
            - data_flow: Additional context (optional)
    
    Returns:
        Read action name
        
    Raises:
        ValueError: If source_service is not supported or no read action available
    """
    source_service = requirements.get("source_service", "").lower()
    action = requirements.get("action", "").lower()
    data_flow = requirements.get("data_flow", {})
    
    normalized_service = normalize_service_name(source_service)
    
    if not is_service_supported(normalized_service):
        raise ValueError(
            f"Source service '{source_service}' is not supported. "
            f"Supported services: {', '.join(sorted(SUPPORTED_SERVICES))}"
        )
    
    if normalized_service not in READ_ACTION_MAPPINGS:
        raise ValueError(
            f"No read actions available for service '{source_service}'"
        )
    
    available_actions = READ_ACTION_MAPPINGS[normalized_service]
    action_text = f"{action} {data_flow.get('description', '')}".lower()
    
    # Try to match based on keywords
    keyword_mappings = {
        "card": "Get Cards",
        "board": "Get Board",
        "list": "Get Lists",
        "task": "Get Tasks",
        "project": "Get Project",
        "issue": "Get Issues",
        "pull request": "Get Pull Requests",
        "merge request": "Get Merge Requests",
        "contact": "Get Contact",
        "lead": "Get Lead",
        "deal": "Get Deal",
        "company": "Get Company",
        "row": "Get Rows",
        "spreadsheet": "Get Spreadsheet",
        "worksheet": "Get Worksheet",
        "email": "Get Emails",
        "message": "Get Message",
        "channel": "Get Channel"
    }
    
    # Find best match
    for keyword, action_name in keyword_mappings.items():
        if keyword in action_text and action_name in available_actions:
            logger.info(
                f"Matched read action '{action_name}' for service '{source_service}' "
                f"based on keyword '{keyword}'"
            )
            return action_name
    
    # Return first available action as default
    default_action = available_actions[0]
    logger.info(
        f"Using default read action '{default_action}' for service '{source_service}'"
    )
    return default_action


def infer_write_action(requirements: dict) -> str:
    """
    Determine the write/send action for the target service.
    
    Examples:
    - Slack: "Send Channel Message", "Post to Channel"
    - Discord: "Send Channel Message"
    - Email: "Send Email"
    
    Args:
        requirements: Requirements dictionary containing:
            - target_service: Target service name
            - action: Action description (optional)
            - data_flow: Additional context (optional)
    
    Returns:
        Write action name
        
    Raises:
        ValueError: If target_service is not supported or no write action available
    """
    target_service = requirements.get("target_service", "").lower()
    action = requirements.get("action", "").lower()
    data_flow = requirements.get("data_flow", {})
    
    normalized_service = normalize_service_name(target_service)
    
    if not is_service_supported(normalized_service):
        raise ValueError(
            f"Target service '{target_service}' is not supported. "
            f"Supported services: {', '.join(sorted(SUPPORTED_SERVICES))}"
        )
    
    if normalized_service not in WRITE_ACTION_MAPPINGS:
        raise ValueError(
            f"No write actions available for service '{target_service}'"
        )
    
    available_actions = WRITE_ACTION_MAPPINGS[normalized_service]
    action_text = f"{action} {data_flow.get('description', '')}".lower()
    
    # Try to match based on keywords and synonyms
    keyword_mappings = {
        "channel": ["Send Channel Message", "Post to Channel", "Post Message"],
        "direct message": ["Send Direct Message"],
        "email": ["Send Email"],
        "card": ["Create Card", "Update Card"],
        "task": ["Create Task", "Update Task"],
        "issue": ["Create Issue", "Update Issue"],
        "comment": ["Add Comment", "Create Comment"],
        "row": ["Create Row", "Update Row", "Append Row"],
        "contact": ["Create Contact", "Update Contact"],
        "lead": ["Create Lead"],
        "deal": ["Create Deal"]
    }
    
    # Find best match
    for keyword, action_names in keyword_mappings.items():
        if keyword in action_text:
            for action_name in action_names:
                if action_name in available_actions:
                    logger.info(
                        f"Matched write action '{action_name}' for service '{target_service}' "
                        f"based on keyword '{keyword}'"
                    )
                    return action_name
    
    # Check for send/post/notify synonyms
    send_synonyms = ACTION_SYNONYMS.get("send", [])
    if any(synonym in action_text for synonym in send_synonyms):
        for action_name in available_actions:
            if "send" in action_name.lower() or "post" in action_name.lower():
                logger.info(
                    f"Matched write action '{action_name}' for service '{target_service}' "
                    f"based on send/post synonym"
                )
                return action_name
    
    # Return first available action as default
    default_action = available_actions[0]
    logger.info(
        f"Using default write action '{default_action}' for service '{target_service}'"
    )
    return default_action


def map_to_zapier(requirements: dict) -> List[ZapierAction]:
    """
    Map requirements dictionary to a list of Zapier actions.
    
    Takes a requirements dictionary and returns a list of Zapier actions needed
    to fulfill the requirements.
    
    Args:
        requirements: Requirements dictionary with structure:
            {
                "trigger_type": str,  # "webhook", "scheduled", or "on_demand"
                "source_service": str,  # e.g., "Trello", "Asana", "GitHub"
                "target_service": str,  # e.g., "Slack", "Discord", "Email"
                "action": str,  # e.g., "summarize and send", "track issues"
                "data_flow": dict  # Additional context about data transformation
            }
    
    Returns:
        List of ZapierAction objects representing the workflow
    
    Raises:
        ValueError: If requirements are invalid or services are not supported
    
    Example:
        >>> requirements = {
        ...     "trigger_type": "webhook",
        ...     "source_service": "Trello",
        ...     "target_service": "Slack",
        ...     "action": "summarize and send",
        ...     "data_flow": {}
        ... }
        >>> actions = map_to_zapier(requirements)
        >>> len(actions)
        2
    """
    if not isinstance(requirements, dict):
        raise ValueError("Requirements must be a dictionary")
    
    trigger_type = requirements.get("trigger_type", "").lower()
    source_service = requirements.get("source_service", "")
    target_service = requirements.get("target_service", "")
    action = requirements.get("action", "")
    data_flow = requirements.get("data_flow", {})
    
    if not source_service:
        raise ValueError("source_service is required in requirements")
    
    if not target_service:
        raise ValueError("target_service is required in requirements")
    
    actions = []
    
    # Validate services
    if not is_service_supported(source_service):
        raise ValueError(
            f"Source service '{source_service}' is not supported. "
            f"Supported services: {', '.join(sorted(SUPPORTED_SERVICES))}"
        )
    
    if not is_service_supported(target_service):
        raise ValueError(
            f"Target service '{target_service}' is not supported. "
            f"Supported services: {', '.join(sorted(SUPPORTED_SERVICES))}"
        )
    
    # Determine trigger/read action based on trigger_type
    if trigger_type == "webhook":
        # Webhook trigger from source service
        try:
            trigger_name = infer_trigger_name(requirements)
            actions.append(ZapierAction(
                service=source_service,
                action_type=ActionType.TRIGGER.value,
                action_name=trigger_name,
                config=data_flow.get("trigger_config", {})
            ))
        except Exception as e:
            logger.error(f"Error inferring trigger: {e}")
            # Fallback to webhook
            actions.append(ZapierAction(
                service=source_service,
                action_type=ActionType.TRIGGER.value,
                action_name="Webhook",
                config=data_flow.get("trigger_config", {})
            ))
    
    elif trigger_type in ["scheduled", "on_demand"]:
        # Read action from source service
        try:
            read_action = infer_read_action(requirements)
            actions.append(ZapierAction(
                service=source_service,
                action_type=ActionType.READ.value,
                action_name=read_action,
                config=data_flow.get("read_config", {})
            ))
        except Exception as e:
            logger.error(f"Error inferring read action: {e}")
            raise ValueError(f"Cannot determine read action for service '{source_service}': {e}")
    
    else:
        # Default to manual trigger
        logger.warning(f"Unknown trigger_type '{trigger_type}', defaulting to manual trigger")
        actions.append(ZapierAction(
            service=source_service,
            action_type=ActionType.TRIGGER.value,
            action_name="Manual Trigger",
            config={}
        ))
    
    # Determine write action for target service
    try:
        write_action = infer_write_action(requirements)
        actions.append(ZapierAction(
            service=target_service,
            action_type=ActionType.WRITE.value,
            action_name=write_action,
            config=data_flow.get("write_config", {})
        ))
    except Exception as e:
        logger.error(f"Error inferring write action: {e}")
        raise ValueError(f"Cannot determine write action for service '{target_service}': {e}")
    
    # Handle multi-step workflows if specified in data_flow
    additional_steps = data_flow.get("additional_steps", [])
    for step in additional_steps:
        if isinstance(step, dict):
            step_service = step.get("service", "")
            step_action_type = step.get("action_type", "").lower()
            step_action_name = step.get("action_name", "")
            step_config = step.get("config", {})
            
            if step_service and step_action_type and step_action_name:
                try:
                    actions.append(ZapierAction(
                        service=step_service,
                        action_type=step_action_type,
                        action_name=step_action_name,
                        config=step_config
                    ))
                except Exception as e:
                    logger.warning(f"Error adding additional step: {e}")
    
    logger.info(
        f"Mapped requirements to {len(actions)} Zapier actions: "
        f"{[f'{a.service}:{a.action_name}' for a in actions]}"
    )
    
    return actions
