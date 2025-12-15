#!/usr/bin/env python3
"""
Groq API service for generating git commit messages
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import sys
import os
import time

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# Groq API configuration
GROQ_API_KEY = ""
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Available Groq models - use the first one by default
# You can change to other models like "mixtral-8x7b-32768", "llama-3.1-70b-versatile"
GROQ_MODEL = "llama-3.3-70b-versatile"

def generate_commit_message(git_diff_content):
    """
    Generate commit message using Groq API based on git diff
    """
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
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }

    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            print(f"{YELLOW}Generating commit message using Groq AI ({GROQ_MODEL})... (Attempt {attempt + 1}/{max_retries}){NC}")

            # Prepare request
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                GROQ_API_URL,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {GROQ_API_KEY}"
                }
            )

            # Make request
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode('utf-8'))

                    if 'choices' in result and len(result['choices']) > 0:
                        commit_message = result['choices'][0]['message']['content'].strip()
                        print(f"{GREEN}✓ Commit message generated successfully{NC}")
                        return commit_message
                    else:
                        print(f"{RED}Error: No content generated from Groq API{NC}")
                        if attempt < max_retries - 1:
                            print(f"{YELLOW}Retrying in {retry_delay} seconds...{NC}")
                            time.sleep(retry_delay)
                            continue
                        return None
                else:
                    print(f"{RED}Error: Groq API request failed with status {response.status}{NC}")
                    print(f"{RED}Response: {response.read().decode('utf-8')}{NC}")
                    if attempt < max_retries - 1:
                        print(f"{YELLOW}Retrying in {retry_delay} seconds...{NC}")
                        time.sleep(retry_delay)
                        continue
                    return None

        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode('utf-8')
            except:
                pass

            if e.code == 429:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"{YELLOW}⚠ Rate limit reached (429). Waiting {wait_time} seconds...{NC}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"{RED}✗ Error 429: Rate limit exceeded.{NC}")
                    return None
            elif e.code == 404:
                print(f"{RED}✗ Error 404: Model not found - {GROQ_MODEL}{NC}")
                print(f"{RED}Error details: {error_body}{NC}")
                return None
            elif e.code == 400:
                print(f"{RED}✗ Bad Request (400): {error_body}{NC}")
                return None
            elif e.code == 401:
                print(f"{RED}✗ Error 401: API key is invalid or unauthorized{NC}")
                print(f"{RED}Error details: {error_body}{NC}")
                return None
            elif e.code == 403:
                print(f"{RED}✗ Error 403: API key doesn't have permission{NC}")
                print(f"{RED}Error details: {error_body}{NC}")
                return None
            else:
                print(f"{RED}✗ HTTP Error {e.code}: {e.reason}{NC}")
                print(f"{RED}Details: {error_body}{NC}")
                if attempt < max_retries - 1:
                    print(f"{YELLOW}Retrying in {retry_delay} seconds...{NC}")
                    time.sleep(retry_delay)
                    continue
                return None

        except urllib.error.URLError as e:
            print(f"{RED}Error: Network request failed - {e}{NC}")
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
    print(f"{RED}✗ Groq API failed after {max_retries} attempts{NC}")
    return None

def test_api_connection():
    """
    Test Groq API connection
    """
    test_prompt = "Hello, respond with 'API connection successful'"

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "user",
                "content": test_prompt
            }
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }

    try:
        print(f"{BLUE}Testing Groq API connection with {GROQ_MODEL}...{NC}")

        # Prepare request
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            GROQ_API_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}"
            }
        )

        # Make request
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                print(f"{GREEN}✓ Groq API connection successful{NC}")

                # Print response for debugging
                if 'choices' in result and len(result['choices']) > 0:
                    text = result['choices'][0]['message']['content']
                    print(f"{BLUE}API Response: {text}{NC}")

                return True
            else:
                print(f"{RED}✗ Groq API connection failed with status {response.status}{NC}")
                return False

    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode('utf-8')
        except:
            pass

        print(f"{RED}✗ HTTP Error {e.code}: {e.reason}{NC}")
        if e.code == 429:
            print(f"{YELLOW}⚠ Rate limit reached. Wait a few minutes and try again.{NC}")
        elif e.code == 404:
            print(f"{RED}Model not found: {GROQ_MODEL}{NC}")
            print(f"{RED}Error details: {error_body}{NC}")
        elif e.code == 400:
            print(f"{RED}Error details: {error_body}{NC}")
        elif e.code == 401:
            print(f"{RED}API key is invalid or unauthorized{NC}")
            print(f"{RED}Error details: {error_body}{NC}")
        elif e.code == 403:
            print(f"{RED}API key doesn't have permission{NC}")
            print(f"{RED}Error details: {error_body}{NC}")
        return False
    except urllib.error.URLError as e:
        print(f"{RED}✗ Network Error: {e.reason}{NC}")
        return False
    except Exception as e:
        print(f"{RED}✗ Groq API connection failed: {e}{NC}")
        return False

if __name__ == "__main__":
    # Test the API connection
    print(f"{BLUE}{'='*50}{NC}")
    print(f"{BLUE}Groq API Connection Test{NC}")
    print(f"{BLUE}{'='*50}{NC}")
    test_api_connection()
