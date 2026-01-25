#!/usr/bin/env python3

import subprocess
import os

# Import common utilities
from common_utils import open_file_with_default_app, BLUE, NC

# Use current working directory instead of hardcoded path
folder_path = os.getcwd()

print(f"{BLUE}Working in directory: {folder_path}{NC}")

# Change the working directory to the specified folder (already current directory)
os.chdir(folder_path)

# Execute the git diff command and write output to diff_output.txt
with open('diff_output.txt', 'w') as file:
    subprocess.run(['git', 'diff'], stdout=file)

# Text to append
text_to_append = '\n================\n\nhere is my changes...give me git push msg and description of changes with using of proper emoticons...dont give any long boring texts, "STRICTLY i dont need any explanations"\n'

# Append the specified text to diff_output.txt
with open('diff_output.txt', 'a') as file:
    file.write(text_to_append)

# Open the file with default editor
open_file_with_default_app('diff_output.txt')

