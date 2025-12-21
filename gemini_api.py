#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi AI Service API for generating git commit messages
Supports: Groq, Mistral, SambaNova, OpenRouter
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# Load default AI service selection
DEFAULT_AI_SERVICE = os.getenv("DEFAULT_AI_SERVICE", "groq").lower()

# All AI service configurations
AI_CONFIGS = {
    "groq": {
        "api_key": os.getenv("GROQ_API_KEY", ""),
        "api_url": os.getenv("GROQ_API_URL", ""),
        "model": os.getenv("GROQ_MODEL", "")
    },
    "mistral": {
        "api_key": os.getenv("MISTRAL_API_KEY", ""),
        "api_url": os.getenv("MISTRAL_API_URL", ""),
        "model": os.getenv("MISTRAL_MODEL", "")
    },
    "sambanova": {
        "api_key": os.getenv("SAMBANOVA_API_KEY", ""),
        "api_url": os.getenv("SAMBANOVA_API_URL", ""),
        "model": os.getenv("SAMBANOVA_MODEL", "")
    },
    "openrouter": {
        "api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "api_url": os.getenv("OPENROUTER_API_URL", ""),
        "model": os.getenv("OPENROUTER_MODEL", "")
    }
}

# Validate selected service
if DEFAULT_AI_SERVICE not in AI_CONFIGS:
    print(f"{RED}✗ Error: Invalid AI service '{DEFAULT_AI_SERVICE}'{NC}")
    print(f"{YELLOW}→ Available services: {', '.join(AI_CONFIGS.keys())}{NC}")
    exit(1)

# Get current service config
current_config = AI_CONFIGS[DEFAULT_AI_SERVICE]

# Validate API key
if not current_config["api_key"]:
    print(f"{RED}✗ Error: API key not found for {DEFAULT_AI_SERVICE.upper()}{NC}")
    print(f"{YELLOW}→ Please set {DEFAULT_AI_SERVICE.upper()}_API_KEY in .env file{NC}")
    exit(1)

def generate_commit_message(git_diff_content):
    """
    Generate commit message using selected AI service based on git diff
    """
    # Get current service config
    config = AI_CONFIGS[DEFAULT_AI_SERVICE]

    prompt = f"""Based on the following git diff, generate a commit message following the Angular Conventional Commit format:

<type>(<scope>): <short summary>
<blank line>
<body>
<blank line>
<footer>

Rules:
- Use one of these types: feat, fix, docs, style, refactor, test, chore
- (scope) is optional but should describe the module/component (e.g., auth, cart, ui)
- Summary should be short (max 50 chars) and in imperative form
- Body (optional) should explain what and why, not how
- Footer (optional) should include BREAKING CHANGE or issue references if applicable
- Use proper emoticons where appropriate
- Don't give any long boring texts, STRICTLY no explanations needed

Git diff content:
{git_diff_content}

Return only the commit message without any additional text or explanations."""

    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            print(f"{YELLOW}Generating commit message using {DEFAULT_AI_SERVICE.upper()} AI ({config['model']})... (Attempt {attempt + 1}/{max_retries}){NC}")

            # Make request
            response = requests.post(
                config["api_url"],
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                if 'choices' in result and len(result['choices']) > 0:
                    commit_message = result['choices'][0]['message']['content'].strip()
                    print(f"{GREEN}✓ Commit message generated successfully using {DEFAULT_AI_SERVICE.upper()}{NC}")
                    return commit_message
                else:
                    print(f"{RED}Error: No content generated from {DEFAULT_AI_SERVICE.upper()} API{NC}")
                    if attempt < max_retries - 1:
                        print(f"{YELLOW}Retrying in {retry_delay} seconds...{NC}")
                        time.sleep(retry_delay)
                        continue
                    return None

            elif response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"{YELLOW}⚠ Rate limit reached (429). Waiting {wait_time} seconds...{NC}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"{RED}✗ Error 429: Rate limit exceeded.{NC}")
                    return None

            elif response.status_code == 404:
                print(f"{RED}✗ Error 404: Model not found - {config['model']}{NC}")
                print(f"{RED}Error details: {response.text}{NC}")
                return None

            elif response.status_code == 400:
                print(f"{RED}✗ Bad Request (400): {response.text}{NC}")
                return None

            elif response.status_code == 401:
                print(f"{RED}✗ Error 401: API key is invalid or unauthorized{NC}")
                print(f"{RED}Error details: {response.text}{NC}")
                return None

            elif response.status_code == 403:
                print(f"{RED}✗ Error 403: API key doesn't have permission{NC}")
                print(f"{RED}Error details: {response.text}{NC}")
                return None

            else:
                print(f"{RED}✗ HTTP Error {response.status_code}: {response.reason}{NC}")
                print(f"{RED}Details: {response.text}{NC}")
                if attempt < max_retries - 1:
                    print(f"{YELLOW}Retrying in {retry_delay} seconds...{NC}")
                    time.sleep(retry_delay)
                    continue
                return None

        except requests.exceptions.Timeout:
            print(f"{RED}Error: Request timed out{NC}")
            if attempt < max_retries - 1:
                print(f"{YELLOW}Retrying in {retry_delay} seconds...{NC}")
                time.sleep(retry_delay)
                continue
            return None

        except requests.exceptions.ConnectionError as e:
            print(f"{RED}Error: Network connection failed - {e}{NC}")
            if attempt < max_retries - 1:
                print(f"{YELLOW}Retrying in {retry_delay} seconds...{NC}")
                time.sleep(retry_delay)
                continue
            return None

        except json.JSONDecodeError as e:
            print(f"{RED}Error: Failed to parse API response - {e}{NC}")
            if attempt < max_retries - 1:
                print(f"{YELLOW}Retrying in {retry_delay} seconds...{NC}")
                time.sleep(retry_delay)
                continue
            return None

        except Exception as e:
            print(f"{RED}Error: Unexpected error - {e}{NC}")
            if attempt < max_retries - 1:
                print(f"{YELLOW}Retrying in {retry_delay} seconds...{NC}")
                time.sleep(retry_delay)
                continue
            return None

    # All retries exhausted
    print(f"{RED}✗ {DEFAULT_AI_SERVICE.upper()} API failed after {max_retries} attempts{NC}")
    return None

def test_api_connection():
    """
    Test selected AI service API connection
    """
    # Get current service config
    config = AI_CONFIGS[DEFAULT_AI_SERVICE]

    test_prompt = "Hello, respond with 'API connection successful'"

    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "user",
                "content": test_prompt
            }
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        print(f"{BLUE}Testing {DEFAULT_AI_SERVICE.upper()} API connection with {config['model']}...{NC}")

        # Make request
        response = requests.post(
            config["api_url"],
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print(f"{GREEN}✓ {DEFAULT_AI_SERVICE.upper()} API connection successful{NC}")

            # Print response for debugging
            if 'choices' in result and len(result['choices']) > 0:
                text = result['choices'][0]['message']['content']
                print(f"{BLUE}API Response: {text}{NC}")

            return True

        elif response.status_code == 429:
            print(f"{RED}✗ HTTP Error 429: Rate limit reached{NC}")
            print(f"{YELLOW}⚠ Wait a few minutes and try again.{NC}")
            return False

        elif response.status_code == 404:
            print(f"{RED}✗ HTTP Error 404: Model not found - {config['model']}{NC}")
            print(f"{RED}Error details: {response.text}{NC}")
            return False

        elif response.status_code == 400:
            print(f"{RED}✗ HTTP Error 400: Bad Request{NC}")
            print(f"{RED}Error details: {response.text}{NC}")
            return False

        elif response.status_code == 401:
            print(f"{RED}✗ HTTP Error 401: API key is invalid or unauthorized{NC}")
            print(f"{RED}Error details: {response.text}{NC}")
            return False

        elif response.status_code == 403:
            print(f"{RED}✗ HTTP Error 403: API key doesn't have permission{NC}")
            print(f"{RED}Error details: {response.text}{NC}")
            return False

        else:
            print(f"{RED}✗ {DEFAULT_AI_SERVICE.upper()} API connection failed with status {response.status_code}{NC}")
            print(f"{RED}Response: {response.text}{NC}")
            return False

    except requests.exceptions.Timeout:
        print(f"{RED}✗ Request timed out{NC}")
        return False

    except requests.exceptions.ConnectionError as e:
        print(f"{RED}✗ Network Error: {e}{NC}")
        return False

    except Exception as e:
        print(f"{RED}✗ {DEFAULT_AI_SERVICE.upper()} API connection failed: {e}{NC}")
        return False

if __name__ == "__main__":
    # Test the API connection
    print(f"{BLUE}{'='*50}{NC}")
    print(f"{BLUE}{DEFAULT_AI_SERVICE.upper()} API Connection Test{NC}")
    print(f"{BLUE}{'='*50}{NC}")
    test_api_connection()
