#!/usr/bin/env python3

import subprocess
import os
import platform

# Use current working directory instead of hardcoded path
folder_path = os.getcwd()

print(f"Working in directory: {folder_path}")

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

# Cross-platform file opening
def open_file(file_path):
    """Open file with default editor based on platform"""
    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.run(['open', file_path])
        elif platform.system() == "Linux":
            subprocess.run(['xdg-open', file_path])
        elif platform.system() == "Windows":
            subprocess.run(['notepad', file_path])
        else:
            print(f"Please manually open: {file_path}")
    except Exception as e:
        print(f"Error opening file: {e}")
        print(f"Please manually open: {file_path}")

# Open the file with default editor
open_file('diff_output.txt')

