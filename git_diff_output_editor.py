#!/usr/bin/env python3

import subprocess
import os

# Specify your folder path here
folder_path = '/Users/maxcode/Documents/GitHub/dua-flutter-v4'

# Change the working directory to the specified folder
os.chdir(folder_path)

# Execute the git diff command and write output to diff_output.txt
with open('diff_output.txt', 'w') as file:
    subprocess.run(['git', 'diff'], stdout=file)

# Text to append
text_to_append = '\n================\n\nhere is my changes...give me git push msg and description of changes with using of proper emoticons...dont give any long boring texts, "STRICTLY i dont need any explanations"\n'

# Append the specified text to diff_output.txt
with open('diff_output.txt', 'a') as file:
    file.write(text_to_append)

# Option 1: Open the file in the default text editor (uncomment the line below if desired)
subprocess.run(['open', 'diff_output.txt'])  # For macOS
# subprocess.run(['xdg-open', 'diff_output.txt'])  # For Linux
# subprocess.run(['notepad', 'diff_output.txt'])  # For Windows

