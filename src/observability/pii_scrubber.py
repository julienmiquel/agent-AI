"""PII Redaction & Sanitization Mechanism.

Provides active scrubbing mechanisms to redact sensitive personal identifiable information
(PII) such as email addresses, phone numbers, credit card numbers, national identification
numbers, and authentication bearer tokens before logging or persistent database storage.
"""

import re
from typing import Any, Dict, List, Union

# Regex patterns for common PII and sensitive tokens
PII_PATTERNS = [
    # Authentication / Bearer Tokens
    (r'(?i)(bearer\s+)[a-zA-Z0-9\-\._~\+/]+=*', r'\1[REDACTED_TOKEN]'),
    (r'(?i)(api[_-]?key[\s:=]+)[a-zA-Z0-9\-\._~\+/]{16,}', r'\1[REDACTED_API_KEY]'),
    (r'(?i)(token[\s:=]+)[a-zA-Z0-9\-\._~\+/]{16,}', r'\1[REDACTED_TOKEN]'),
    # Email addresses
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', '[REDACTED_EMAIL]'),
    # Credit / Debit Card numbers (major formats)
    (r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b', '[REDACTED_CREDIT_CARD]'),
    # Phone numbers (international and French/European formats)
    (r'\b(?:\+33|\+31|\+49|\+44|\+1|0)(?:\s*\d{1,2}){4,5}\b', '[REDACTED_PHONE]'),
    # IBAN / Bank Account numbers
    (r'\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z\d]?){0,16}\b', '[REDACTED_IBAN]'),
    # Social Security / National Identity numbers (e.g. French NIR / US SSN)
    (r'\b\d{1}\s*\d{2}\s*\d{2}\s*\d{2}\s*\d{3}\s*\d{3}\s*\d{2}\b', '[REDACTED_NATIONAL_ID]'),
    (r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]'),
]

# Pre-compile regexes for performance
COMPILED_PATTERNS = [(re.compile(pattern), repl) for pattern, repl in PII_PATTERNS]


def scrub_string(text: str) -> str:
    """Sanitizes a string by replacing detected PII patterns with redaction placeholders."""
    if not text or not isinstance(text, str):
        return text
    scrubbed = text
    for regex, repl in COMPILED_PATTERNS:
        scrubbed = regex.sub(repl, scrubbed)
    return scrubbed


def scrub_pii(data: Any) -> Any:
    """Recursively traverses dictionaries, lists, and strings to scrub PII and sensitive data.
    
    Args:
        data: Arbitrary data structure (dict, list, str, int, etc.) to sanitize.

    Returns:
        A copy of the data structure with all string values scrubbed of PII.
    """
    if isinstance(data, str):
        return scrub_string(data)
    elif isinstance(data, dict):
        scrubbed_dict = {}
        for k, v in data.items():
            # If the key itself indicates a secret or token, redact value immediately
            key_lower = str(k).lower()
            if any(secret_word in key_lower for secret_word in ["token", "secret", "password", "apikey", "api_key", "authorization", "auth_token"]):
                if isinstance(v, str) and len(v) > 8:
                    scrubbed_dict[k] = "[REDACTED_SECRET]"
                else:
                    scrubbed_dict[k] = scrub_pii(v)
            else:
                scrubbed_dict[k] = scrub_pii(v)
        return scrubbed_dict
    elif isinstance(data, (list, tuple)):
        scrubbed_list = [scrub_pii(item) for item in data]
        return type(data)(scrubbed_list)
    elif hasattr(data, "to_dict") and callable(getattr(data, "to_dict")):
        return scrub_pii(data.to_dict())
    else:
        return data
