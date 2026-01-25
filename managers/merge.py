#!/usr/bin/env python3
"""
File Merge Tool - Merges multiple files into a single output file
"""

import os

from common_utils import (
    timer_decorator,
    open_file_with_default_app,
    RED,
    GREEN,
    YELLOW,
    BLUE,
    NC,
)


def merge_files_recursively(source_folder, output_file, base_path=""):
    processed_files = 0
    failed_files = 0

    if not os.path.exists(source_folder):
        print(f"{RED}❌ Error: Source folder '{source_folder}' does not exist!{NC}")
        return 0, 1

    print(f"{BLUE}📁 Processing folder: {source_folder}{NC}")

    for root, dirs, files in os.walk(source_folder):
        relative_path = os.path.relpath(root, base_path) if base_path else ""
        for filename in files:
            file_path = os.path.join(root, filename)
            rel_file_path = os.path.join(relative_path, filename) if base_path else filename
            try:
                append_file_content(file_path, output_file, rel_file_path)
                processed_files += 1
                print(f"{GREEN}✅ Processed: {rel_file_path}{NC}")
            except Exception as e:
                failed_files += 1
                print(f"{RED}❌ Failed to process {rel_file_path}: {e}{NC}")

    return processed_files, failed_files


def append_file_content(file_path, output_file, display_name):
    try:
        with open(output_file, "a", encoding="utf-8") as outfile:
            outfile.write(f"File Name : {display_name}\n\n")
            with open(file_path, "r", encoding="utf-8") as infile:
                content = infile.read()
                outfile.write(content)
            outfile.write("\n\n=====================\n\n")
    except UnicodeDecodeError:
        # Try with different encoding for binary files
        with open(output_file, "a", encoding="utf-8") as outfile:
            outfile.write(f"File Name : {display_name} [Binary file - content skipped]\n\n")
            outfile.write("\n\n=====================\n\n")
        raise Exception("Binary file - content skipped")
    except Exception as e:
        with open(output_file, "a", encoding="utf-8") as outfile:
            outfile.write(f"File Name : {display_name} [ERROR: {e}]\n\n")
            outfile.write("\n\n=====================\n\n")
        raise


def merge_specific_paths_from_file(paths_file, output_file):
    processed_files = 0
    failed_files = 0

    if not os.path.exists(paths_file):
        print(f"{RED}❌ Error: Paths file '{paths_file}' does not exist!{NC}")
        return 0, 1

    try:
        with open(paths_file, "r", encoding="utf-8") as file:
            paths = [line.strip() for line in file.readlines() if line.strip()]

        if not paths:
            print(f"{YELLOW}⚠️  Warning: No paths found in '{paths_file}'{NC}")
            return 0, 0

        print(f"{BLUE}📁 Processing {len(paths)} paths from {paths_file}{NC}")

        # Find common base path for better relative path display
        common_base = os.path.commonpath([os.path.abspath(p) for p in paths if os.path.exists(p)])

        # If common_base is a file (not directory), use its parent directory
        if os.path.isfile(common_base):
            common_base = os.path.dirname(common_base)

        for path in paths:
            if os.path.isdir(path):
                p_files, f_files = merge_files_recursively(path, output_file, base_path=common_base)
                processed_files += p_files
                failed_files += f_files
            elif os.path.isfile(path):
                # Get relative path from common base
                display_name = os.path.relpath(path, common_base)
                try:
                    append_file_content(path, output_file, display_name)
                    processed_files += 1
                    print(f"{GREEN}✅ Processed: {path}{NC}")
                except Exception as e:
                    failed_files += 1
                    print(f"{RED}❌ Failed to process {path}: {e}{NC}")
            else:
                print(f"{YELLOW}⚠️  Warning: Path does not exist: {path}{NC}")
                failed_files += 1

        return processed_files, failed_files

    except Exception as e:
        print(f"{RED}❌ Error reading paths file: {e}{NC}")
        return 0, 1


@timer_decorator
def merge_files():
    """Main entry point for file merge tool"""
    print(f"{BLUE}🚀 File Merge Tool Started{NC}")
    print("="*60)

    # Clear or create the output file to start fresh
    path_output_file = "path_merge_files.txt"

    print(f"{BLUE}🗑️  Clearing/creating output file...{NC}")
    try:
        open(path_output_file, "w").close()
        print(f"{GREEN}✅ Output file created successfully{NC}")
    except Exception as e:
        print(f"{RED}❌ Error creating output file: {e}{NC}")
        exit(1)

    total_processed = 0
    total_failed = 0

    # Merging specific paths listed in a file
    print(f"\n{BLUE}📁 Merging files from paths list...{NC}")
    paths_file = "paths.txt"  # This file should contain the paths as you wish to input them
    processed, failed = merge_specific_paths_from_file(paths_file, path_output_file)
    total_processed += processed
    total_failed += failed

    if processed > 0 or failed == 0:
        print(f"{GREEN}✅ Paths file merge completed: {processed} files processed, {failed} failed{NC}")
    else:
        print(f"{RED}❌ Paths file merge failed or no files found{NC}")

    # Final summary
    print("\n" + "="*60)
    print(f"{BLUE}📊 FINAL SUMMARY:{NC}")
    print(f"{GREEN}✅ Total files processed successfully: {total_processed}{NC}")
    if total_failed > 0:
        print(f"{RED}❌ Total files failed: {total_failed}{NC}")

    if total_failed == 0:
        print(f"\n{GREEN}🎉 ALL OPERATIONS COMPLETED SUCCESSFULLY!{NC}")
        print(f"{BLUE}📁 Check your merged file: {path_output_file}{NC}")
        # Auto-open the merged file
        open_file_with_default_app(path_output_file)
    else:
        print(f"\n{YELLOW}⚠️  COMPLETED WITH SOME ERRORS!{NC}")
        print(f"{YELLOW}ℹ️  Check the error messages above for details{NC}")

    print("="*60)
