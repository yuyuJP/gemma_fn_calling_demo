from datetime import datetime
import random
from zoneinfo import ZoneInfo, available_timezones
import ollama

def _normalize_timezone_with_llm(user_input: str) -> str:
    """Use LLM to convert user timezone input to proper IANA timezone identifier."""
    
    # Get available timezones for context
    available_zones = list(available_timezones())
    
    # Create a prompt for the LLM to normalize timezone
    prompt = f"""Convert the user's timezone input to a proper IANA timezone identifier.

User input: "{user_input}"

Available IANA timezone identifiers include examples like:
- Asia/Tokyo, Asia/Shanghai, Asia/Kolkata
- America/New_York, America/Los_Angeles, America/Chicago
- Europe/London, Europe/Paris, Europe/Berlin
- Australia/Sydney, Australia/Melbourne
- UTC

Rules:
1. If the input is already a valid IANA timezone (like "Asia/Tokyo"), return it exactly
2. Convert city/country names to proper IANA format (e.g., "Tokyo" → "Asia/Tokyo")
3. Convert abbreviations (e.g., "JST" → "Asia/Tokyo", "EST" → "America/New_York")
4. Handle misspellings (e.g., "T0kyo" → "Asia/Tokyo")
5. If unclear or invalid, return "UTC"

Respond with ONLY the IANA timezone identifier, nothing else."""

    try:
        client = ollama.Client()
        response = client.chat(
            model="gemma3:12b",
            messages=[{"role": "user", "content": prompt}]
        )
        
        normalized_tz = response["message"]["content"].strip()
        
        # Validate the result is a real timezone
        if normalized_tz in available_zones:
            return normalized_tz
        else:
            return "UTC"  # Fallback if LLM returns invalid timezone
            
    except Exception:
        return "UTC"  # Fallback if LLM call fails

def get_time(timezone: str = "UTC") -> str:
    """Return current time string for a specific timezone."""
    try:
        # Use LLM to normalize timezone input
        normalized_tz = _normalize_timezone_with_llm(timezone)
        
        # Get current time in the normalized timezone
        tz = ZoneInfo(normalized_tz)
        current_time = datetime.now(tz)
        
        # Format time nicely
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        return f"Current time in {timezone} ({normalized_tz}): {formatted_time}"
        
    except Exception as e:
        # Fallback to UTC if anything goes wrong
        utc_time = datetime.now(ZoneInfo("UTC"))
        return f"Error getting time for '{timezone}'. Current UTC time: {utc_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"

def random_joke() -> str:
    """Return a canned dad joke."""
    jokes = [
        "I told my computer I needed a break, and it said ‘no problem — I’ll go to sleep.’",
        "Why do programmers prefer dark mode? Because light attracts bugs.",
    ]
    return random.choice(jokes)
