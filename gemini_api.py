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
GEMINI_API_KEY = "AIzaSyAWux-EKBJZKlpjmdSg0mKzajyYjdVEVZU"

# Try different model names - use the first one that works
AVAILABLE_MODELS = [
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-pro",
]

def get_api_url(model_name):
    """Generate API URL for given model"""
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"

def test_model(model_name):
    """Test if a model is available"""
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
            if response.status == 200:
                return True
    except Exception as e:
        # Silently fail during testing
        pass
    
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
    GEMINI_API_URL = get_api_url(AVAILABLE_MODELS[0])

def generate_commit_message(git_diff_content):
    """
    Generate commit message using Gemini API based on git diff
    """
    if not WORKING_MODEL:
        print(f"{RED}Error: No working model available{NC}")
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
                            return None
                    else:
                        print(f"{RED}Error: No content generated from Gemini API{NC}")
                        return None
                else:
                    print(f"{RED}Error: Gemini API request failed with status {response.status}{NC}")
                    print(f"{RED}Response: {response.read().decode('utf-8')}{NC}")
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
                    print(f"{RED}✗ Error 429: Rate limit exceeded. Please try again later.{NC}")
                    return None
            elif e.code == 404:
                print(f"{RED}✗ Error 404: Model not found - {WORKING_MODEL}{NC}")
                print(f"{RED}Error details: {error_body}{NC}")
                return None
            elif e.code == 400:
                print(f"{RED}✗ Bad Request (400): {error_body}{NC}")
                return None
            elif e.code == 403:
                print(f"{RED}✗ Error 403: API key may be invalid or doesn't have permission{NC}")
                print(f"{RED}Error details: {error_body}{NC}")
                return None
            else:
                print(f"{RED}✗ HTTP Error {e.code}: {e.reason}{NC}")
                print(f"{RED}Details: {error_body}{NC}")
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
            return None
        except Exception as e:
            print(f"{RED}Error: Unexpected error - {e}{NC}")
            return None

    return None

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