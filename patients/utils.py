"""
Utility functions for patient management.
"""

import re
import secrets
import string
from users.models import User


def sanitize_username(text):
    """
    Sanitize text for username use.
    - Convert to lowercase
    - Remove special characters
    - Replace spaces with nothing
    """
    if not text:
        return ""

    # Convert to lowercase and remove special characters
    text = text.lower()
    text = re.sub(r"[^a-z0-9]", "", text)
    return text


def generate_username(first_name, last_name):
    """
    Generate a unique username from patient's name.
    Format: {first_initial}{last_name}
    If duplicate exists, append numbers: jsmith2, jsmith3, etc.

    Args:
        first_name (str): Patient's first name
        last_name (str): Patient's last name

    Returns:
        str: Unique username
    """
    if not first_name or not last_name:
        raise ValueError("First name and last name are required to generate username")

    # Get first initial and full last name
    first_initial = sanitize_username(first_name[0])
    sanitized_last_name = sanitize_username(last_name)

    # Base username
    base_username = f"{first_initial}{sanitized_last_name}"

    # Ensure it's not empty
    if not base_username:
        base_username = "patient"

    # Check if username exists
    username = base_username
    counter = 2

    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    return username


def generate_random_password(length=12):
    """
    Generate a secure random password.

    Args:
        length (int): Password length (default: 12)

    Returns:
        str: Random password with letters, numbers, and symbols
    """
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%&*"

    # Ensure at least one of each type
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(symbols),
    ]

    # Fill remaining length with random characters from all sets
    all_chars = lowercase + uppercase + digits + symbols
    password += [secrets.choice(all_chars) for _ in range(length - 4)]

    # Shuffle to avoid predictable pattern
    secrets.SystemRandom().shuffle(password)

    return "".join(password)
