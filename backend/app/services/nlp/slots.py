"""
Slot-filling for category-specific information extraction.

For each category, defines required slots (e.g., printer model, error code)
and attempts to extract them from user message for clarification requests.
"""

from typing import Dict, List, Optional


# Category-specific slots (required info for resolution)
CATEGORY_SLOTS = {
    "network": {
        "slots": ["device_type", "error_message"],
        "questions": [
            "What device are you using (desktop, laptop, mobile)?",
            "What error message do you see?",
        ],
    },
    "account": {
        "slots": ["account_type", "error_code"],
        "questions": [
            "Is this a domain account or application account?",
            "What error do you see when logging in?",
        ],
    },
    "hardware": {
        "slots": ["device_type", "device_model", "symptom"],
        "questions": [
            "What hardware is affected (printer, monitor, keyboard, etc.)?",
            "What is the model number?",
            "What exactly is happening?",
        ],
    },
    "printer": {
        "slots": ["printer_model", "error_message"],
        "questions": [
            "What is your printer model?",
            "What error message appears?",
        ],
    },
    "email": {
        "slots": ["client_type", "symptom"],
        "questions": [
            "Which email client are you using (Outlook, Gmail, etc.)?",
            "What is the specific issue?",
        ],
    },
    "software": {
        "slots": ["software_name", "os"],
        "questions": [
            "Which software do you need?",
            "What operating system?",
        ],
    },
}


def extract_slots(message: str, category: str) -> Dict[str, Optional[str]]:
    """
    Attempt to extract slot values from a user message.
    
    Returns:
        Dict mapping slot name -> extracted value (or None if not found)
    """
    slots_def = CATEGORY_SLOTS.get(category, {})
    slots = slots_def.get("slots", [])
    
    extracted = {slot: None for slot in slots}
    
    # Simple keyword-based extraction
    lower = message.lower()
    
    # Extract device types
    if "device_type" in extracted:
        for device in ["laptop", "desktop", "computer", "pc", "mac", "mobile", "phone", "tablet"]:
            if device in lower:
                extracted["device_type"] = device
                break
    
    # Extract error code/message (look for error patterns)
    if "error_message" in extracted or "error_code" in extracted:
        import re
        error_patterns = [
            r"error[:\s]+(.+?)(?:\.|,|$)",
            r"code[:\s]+(\d+)",
            r"message[:\s]+(.+?)(?:\.|,|$)",
        ]
        for pattern in error_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                extracted["error_message"] = match.group(1).strip()
                break
    
    # Extract software name
    if "software_name" in extracted:
        software_list = ["slack", "teams", "python", "visual studio", "git", "docker", "vscode", "chrome"]
        for soft in software_list:
            if soft in lower:
                extracted["software_name"] = soft
                break
    
    # Extract OS
    if "os" in extracted:
        for os_name in ["windows", "linux", "macos", "mac"]:
            if os_name in lower:
                extracted["os"] = os_name
                break
    
    return extracted


def get_missing_slots(message: str, category: str) -> List[str]:
    """
    Determine which slots are missing for a category.
    
    Returns:
        List of clarification questions for missing slots
    """
    extracted = extract_slots(message, category)
    slots_def = CATEGORY_SLOTS.get(category, {})
    questions = slots_def.get("questions", [])
    
    missing = []
    for slot in extracted:
        if extracted[slot] is None:
            # Find corresponding question
            for q in questions:
                if slot.replace("_", " ") in q.lower() or any(
                    key in q.lower() for key in ["device", "error", "software", "operating"]
                ):
                    missing.append(q)
                    break
    
    return missing
