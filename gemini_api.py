#!/usr/bin/env python3
"""
Gemini API service for generating git commit messages
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import sys
import os

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# Gemini API configuration
GEMINI_API_KEY = "AIzaSyDXNmCaoqqrKzfXOQcsldQzQsu0rwpOAPo"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent"

def generate_commit_message(git_diff_content):
    """
    Generate commit message using Gemini API based on git diff
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
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    try:
        print(f"{YELLOW}Generating commit message using Gemini AI...{NC}")

        # Prepare request
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            GEMINI_API_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            }
        )

        # Make request
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))

                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        commit_message = candidate['content']['parts'][0]['text'].strip()
                        print(f"{GREEN}✓ Commit message generated successfully{NC}")
                        return commit_message
                    else:
                        print(f"{RED}Error: Unexpected API response structure{NC}")
                        return None
                else:
                    print(f"{RED}Error: No content generated from Gemini API{NC}")
                    return None
            else:
                print(f"{RED}Error: Gemini API request failed with status {response.status}{NC}")
                print(f"{RED}Response: {response.read().decode('utf-8')}{NC}")
                return None

    except urllib.error.URLError as e:
        print(f"{RED}Error: Network request failed - {e}{NC}")
        return None
    except json.JSONDecodeError as e:
        print(f"{RED}Error: Failed to parse API response - {e}{NC}")
        return None
    except Exception as e:
        print(f"{RED}Error: Unexpected error - {e}{NC}")
        return None

def test_api_connection():
    """
    Test Gemini API connection
    """
    test_prompt = "Hello, respond with 'API connection successful'"

    payload = {
        "contents": [{
            "parts": [{
                "text": test_prompt
            }]
        }]
    }

    try:
        # Prepare request
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            GEMINI_API_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            }
        )

        # Make request
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                print(f"{GREEN}✓ Gemini API connection successful{NC}")
                return True
            else:
                print(f"{RED}✗ Gemini API connection failed with status {response.status}{NC}")
                return False

    except Exception as e:
        print(f"{RED}✗ Gemini API connection failed: {e}{NC}")
        return False

if __name__ == "__main__":
    # Test the API connection
    test_api_connection()