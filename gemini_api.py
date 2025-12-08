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
import time

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# Gemini API configuration
GEMINI_API_KEY = "AIzaSyB2TonBhKkGj2ZLujUvyZvryweeUeu1y5Q"

# OpenRouter API configuration (Fallback)
OPENROUTER_API_KEY = "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"  # Replace with your OpenRouter API key
OPENROUTER_MODEL = "google/gemini-2.5-flash"  # You can change to other models like "openai/gpt-4o", "google/gemini-2.0-flash-exp:free"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Try different model names - use the first one that works
# Updated for 2025: Gemini 1.0 and 1.5 models are retired
AVAILABLE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
]

def get_api_url(model_name):
    """Generate API URL for given model"""
    # Using v1beta for better model compatibility (v1 has limited model support)
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"

def test_model(model_name):
    """Test if a model is available"""
    print(GEMINI_API_KEY)
    payload = {
        "contents": [{
            "parts": [{
                "text": "Hi"
            }]
        }]
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            get_api_url(model_name),
            data=data,
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"{YELLOW}Response Status: {response.status}{NC}")
            if response.status == 200:
                return True
            else:
                response_body = response.read().decode('utf-8')
                print(f"{RED}Response Body: {response_body}{NC}")
    except urllib.error.HTTPError as e:
        # Print HTTP error details
        print(f"{RED}HTTP Error {e.code}: {e.reason}{NC}")
        try:
            error_body = e.read().decode('utf-8')
            print(f"{RED}Error Body: {error_body}{NC}")
        except:
            pass
    except Exception as e:
        # Print error for debugging
        print(f"{RED}Error: {type(e).__name__}: {str(e)}{NC}")
        import traceback
        traceback.print_exc()

    return False

def find_working_model():
    """Find first working model from the list"""
    print(f"{BLUE}Searching for available Gemini model...{NC}")
    
    for model in AVAILABLE_MODELS:
        print(f"{YELLOW}Testing {model}...{NC}", end=" ", flush=True)
        if test_model(model):
            print(f"{GREEN}✓ Works!{NC}")
            return model
        else:
            print(f"{RED}✗ Not available{NC}")
    
    return None

# Find working model at startup
WORKING_MODEL = find_working_model()

if WORKING_MODEL:
    GEMINI_API_URL = get_api_url(WORKING_MODEL)
    print(f"{GREEN}Using model: {WORKING_MODEL}{NC}\n")
else:
    print(f"{RED}No working Gemini model found!{NC}")
    print(f"{YELLOW}Possible reasons:{NC}")
    print(f"  1. API key is invalid or expired")
    print(f"  2. API key doesn't have access to these models")
    print(f"  3. You've exceeded the rate limit (wait a few minutes)")
    print(f"  4. Network connectivity issues")
    print(f"{BLUE}Will fallback to OpenRouter API if needed{NC}\n")
    GEMINI_API_URL = get_api_url(AVAILABLE_MODELS[0])

def generate_commit_message_openrouter(git_diff_content):
    """
    Generate commit message using OpenRouter API as fallback
    """
    if OPENROUTER_API_KEY == "sk-or-v1-YOUR_API_KEY_HERE":
        print(f"{RED}Error: OpenRouter API key not configured{NC}")
        print(f"{YELLOW}Please set OPENROUTER_API_KEY in gemini_api.py{NC}")
        return None

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
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }

    try:
        print(f"{YELLOW}Using OpenRouter fallback ({OPENROUTER_MODEL})...{NC}")

        # Prepare request
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            OPENROUTER_API_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://github.com/your-repo",  # Optional
                "X-Title": "Flutter Dev Tools"  # Optional
            }
        )

        # Make request
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))

                if 'choices' in result and len(result['choices']) > 0:
                    commit_message = result['choices'][0]['message']['content'].strip()
                    print(f"{GREEN}✓ Commit message generated successfully (OpenRouter){NC}")
                    return commit_message
                else:
                    print(f"{RED}Error: No content generated from OpenRouter API{NC}")
                    return None
            else:
                print(f"{RED}Error: OpenRouter API request failed with status {response.status}{NC}")
                return None

    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode('utf-8')
        except:
            pass
        print(f"{RED}✗ OpenRouter HTTP Error {e.code}: {e.reason}{NC}")
        print(f"{RED}Details: {error_body}{NC}")
        return None
    except Exception as e:
        print(f"{RED}Error: OpenRouter API failed - {e}{NC}")
        return None

def generate_commit_message(git_diff_content):
    """
    Generate commit message using Gemini API based on git diff
    Automatically falls back to OpenRouter if Gemini fails
    """
    if not WORKING_MODEL:
        print(f"{YELLOW}Gemini model not available, trying OpenRouter fallback...{NC}")
        return generate_commit_message_openrouter(git_diff_content)
    
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
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500
        }
    }

    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            print(f"{YELLOW}Generating commit message using Gemini AI ({WORKING_MODEL})... (Attempt {attempt + 1}/{max_retries}){NC}")

            # Prepare request
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                GEMINI_API_URL,
                data=data,
                headers={
                    "Content-Type": "application/json"
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
                            print(f"{YELLOW}Trying OpenRouter fallback...{NC}")
                            return generate_commit_message_openrouter(git_diff_content)
                    else:
                        print(f"{RED}Error: No content generated from Gemini API{NC}")
                        print(f"{YELLOW}Trying OpenRouter fallback...{NC}")
                        return generate_commit_message_openrouter(git_diff_content)
                else:
                    print(f"{RED}Error: Gemini API request failed with status {response.status}{NC}")
                    print(f"{RED}Response: {response.read().decode('utf-8')}{NC}")
                    print(f"{YELLOW}Trying OpenRouter fallback...{NC}")
                    return generate_commit_message_openrouter(git_diff_content)

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
                    print(f"{YELLOW}Trying OpenRouter fallback...{NC}")
                    return generate_commit_message_openrouter(git_diff_content)
            elif e.code == 404:
                print(f"{RED}✗ Error 404: Model not found - {WORKING_MODEL}{NC}")
                print(f"{RED}Error details: {error_body}{NC}")
                print(f"{YELLOW}Trying OpenRouter fallback...{NC}")
                return generate_commit_message_openrouter(git_diff_content)
            elif e.code == 400:
                print(f"{RED}✗ Bad Request (400): {error_body}{NC}")
                print(f"{YELLOW}Trying OpenRouter fallback...{NC}")
                return generate_commit_message_openrouter(git_diff_content)
            elif e.code == 403:
                print(f"{RED}✗ Error 403: API key may be invalid or doesn't have permission{NC}")
                print(f"{RED}Error details: {error_body}{NC}")
                print(f"{YELLOW}Trying OpenRouter fallback...{NC}")
                return generate_commit_message_openrouter(git_diff_content)
            else:
                print(f"{RED}✗ HTTP Error {e.code}: {e.reason}{NC}")
                print(f"{RED}Details: {error_body}{NC}")
                print(f"{YELLOW}Trying OpenRouter fallback...{NC}")
                return generate_commit_message_openrouter(git_diff_content)
                
        except urllib.error.URLError as e:
            print(f"{RED}Error: Network request failed - {e}{NC}")
            if attempt < max_retries - 1:
                print(f"{YELLOW}Retrying in {retry_delay} seconds...{NC}")
                time.sleep(retry_delay)
                continue
            return None
        except json.JSONDecodeError as e:
            print(f"{RED}Error: Failed to parse API response - {e}{NC}")
            print(f"{YELLOW}Trying OpenRouter fallback...{NC}")
            return generate_commit_message_openrouter(git_diff_content)
        except Exception as e:
            print(f"{RED}Error: Unexpected error - {e}{NC}")
            if attempt == max_retries - 1:
                # Last attempt failed, try OpenRouter fallback
                print(f"{YELLOW}All Gemini attempts failed, trying OpenRouter fallback...{NC}")
                return generate_commit_message_openrouter(git_diff_content)
            return None

    # All retries exhausted, try OpenRouter fallback
    print(f"{YELLOW}Gemini API failed after {max_retries} attempts, trying OpenRouter fallback...{NC}")
    return generate_commit_message_openrouter(git_diff_content)

def test_api_connection():
    """
    Test Gemini API connection
    """
    if not WORKING_MODEL:
        print(f"{RED}✗ No working model found during initialization{NC}")
        return False
    
    test_prompt = "Hello, respond with 'API connection successful'"

    payload = {
        "contents": [{
            "parts": [{
                "text": test_prompt
            }]
        }]
    }

    try:
        print(f"{BLUE}Testing Gemini API connection with {WORKING_MODEL}...{NC}")
        
        # Prepare request
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            GEMINI_API_URL,
            data=data,
            headers={
                "Content-Type": "application/json"
            }
        )

        # Make request
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                print(f"{GREEN}✓ Gemini API connection successful{NC}")
                
                # Print response for debugging
                if 'candidates' in result and len(result['candidates']) > 0:
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    print(f"{BLUE}API Response: {text}{NC}")
                
                return True
            else:
                print(f"{RED}✗ Gemini API connection failed with status {response.status}{NC}")
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
            print(f"{RED}Model not found: {WORKING_MODEL}{NC}")
            print(f"{RED}Error details: {error_body}{NC}")
        elif e.code == 400:
            print(f"{RED}Error details: {error_body}{NC}")
        elif e.code == 403:
            print(f"{RED}API key may be invalid or lacks permissions{NC}")
            print(f"{RED}Error details: {error_body}{NC}")
        return False
    except urllib.error.URLError as e:
        print(f"{RED}✗ Network Error: {e.reason}{NC}")
        return False
    except Exception as e:
        print(f"{RED}✗ Gemini API connection failed: {e}{NC}")
        return False

if __name__ == "__main__":
    # Test the API connection
    print(f"{BLUE}{'='*50}{NC}")
    print(f"{BLUE}Gemini API Connection Test{NC}")
    print(f"{BLUE}{'='*50}{NC}")
    test_api_connection()
