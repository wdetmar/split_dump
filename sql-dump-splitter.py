#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = "Davyd Maker + AI"
__version__ = "1.5"

import os
import argparse
import time
import re

DEFAULT_SQL_CONDITIONS = ["DROP TABLE", "CREATE TABLE IF NOT EXISTS", "create or replace TABLE", "CREATE OR REPLACE FUNCTION", "create or replace view", "CREATE OR REPLACE PROCEDURE" ]

def save_file(content, directory, file_name):
    try:
        file_path = os.path.join(directory, f'{file_name}.sql')
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(''.join(content))
    except IOError as e:
        print(f"Error writing file {file_path}: {e}")

def prepare_directory(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

def should_split(line, sql_conditions, condition_hit_count, trigger_count):
    if any(condition in line for condition in sql_conditions):
        condition_hit_count += 1
        if condition_hit_count >= trigger_count:
            return True, condition_hit_count
    return False, condition_hit_count

def extract_function_name(line, sql_conditions):
    """
    Searches for specific SQL conditions in a line and extracts the name following each condition.
    Supports conditions from the sql_conditions list (like CREATE FUNCTION, CREATE VIEW, etc.).
    """
    for condition in sql_conditions:
        # Create a regex pattern for each condition to capture the name following the condition keyword
        if condition.upper() in line.upper():
            if "FUNCTION" in condition.upper():
                # Capture the function name after "CREATE OR REPLACE FUNCTION" up to the first "("
                match = re.search(r'CREATE OR REPLACE FUNCTION\s+([^\s(]+)', line, re.IGNORECASE)
            elif "VIEW" in condition.upper():
                # Capture the view name after "CREATE OR REPLACE VIEW" up to the first space or semicolon
                match = re.search(r'CREATE OR REPLACE VIEW\s+([^\s;]+)', line, re.IGNORECASE)
            elif "TABLE" in condition.upper():
                # Capture the table name after "CREATE TABLE" or "DROP TABLE" up to the first space or semicolon
                match = re.search(r'(CREATE TABLE|DROP TABLE)\s+([^\s;]+)', line, re.IGNORECASE)
                if match:
                    return match.group(2)  # Table name is in the second group
            elif "PROCEDURE" in condition.upper():
                # Capture the procedure name after "CREATE OR REPLACE PROCEDURE" up to the first "(" or space
                match = re.search(r'CREATE OR REPLACE PROCEDURE\s+([^\s(]+)', line, re.IGNORECASE)
            else:
                match = None

            if match:
                return match.group(1)  # Return the name captured after the SQL keyword

    return None  # Return None if no condition matches

def handle_line(line, ignore_blank_lines):
    if ignore_blank_lines and not line.strip():
        return None
    return line

def process_file(input_file_path, output_dir, trigger_count, ignore_blank_lines, sql_conditions):
    prepare_directory(output_dir)

    start_time = time.time()
    file_count = 0
    try:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            current_content = []
            condition_hit_count = 0
            file_name = f'file_{file_count}'  # Default file name

            for line in file:
                processed_line = handle_line(line, ignore_blank_lines)
                if processed_line is None:
                    continue

               if any(keyword in processed_line.upper() for keyword in sql_conditions):
                # Extract name based on the matching SQL condition
                extracted_name = extract_function_name(processed_line, sql_conditions)
                if extracted_name:
                    file_name = extracted_name  # Update file name with the extracted name

                split, condition_hit_count = should_split(processed_line, sql_conditions, condition_hit_count, trigger_count)
                if split:
                    save_file(current_content, output_dir, file_name)
                    file_count += 1
                    current_content = []
                    condition_hit_count = 0
                    file_name = f'file_{file_count}'  # Reset to default if no function name is found

                current_content.append(processed_line)

            if current_content:
                save_file(current_content, output_dir, file_name)
                file_count += 1
    except Exception as e:
        print(f"Error reading file {input_file_path}: {e}")

    return time.time() - start_time, file_count

def main():
    parser = argparse.ArgumentParser(description="Splits an SQL file into parts based on specific conditions, a count of occurrences of those conditions, and the option to ignore blank lines.")
    parser.add_argument("-i", "--input-file", required=True, help="Path to the SQL file to be processed.")
    parser.add_argument("-o", "--output-dir", default=None, help="Directory where the split files will be saved. If not provided, a directory with the name of the input file is created.")
    parser.add_argument("-t", "--trigger-count", type=int, default=1, help="Number of occurrences of the SQL conditions before saving a file (default: 1).")
    parser.add_argument("-b", "--ignore-blank-lines", action='store_true', help="Ignore blank lines in the file (default: False).")
    parser.add_argument("-c", "--sql-conditions", nargs='+', default=DEFAULT_SQL_CONDITIONS, help="List of SQL conditions that trigger the file division. Example: --sql-conditions 'DROP TABLE' 'ALTER TABLE'")
    parser.add_argument("-r", "--report", action='store_true', help="Display a summary report at the end of the execution.")

    args = parser.parse_args()

    if not args.output_dir:
        base_name = os.path.splitext(os.path.basename(args.input_file))[0]
        args.output_dir = os.path.join(os.getcwd(), base_name)

    elapsed_time, total_files = process_file(args.input_file, args.output_dir, args.trigger_count, args.ignore_blank_lines, args.sql_conditions)

    if args.report:
        print("\nExecution Summary:")
        print(f"Time elapsed: {elapsed_time:.2f} seconds")
        print(f"Input file: {args.input_file}")
        print(f"Output directory: {args.output_dir}")
        print(f"Total files generated: {total_files}")
        print(f"Ignore blank lines: {args.ignore_blank_lines}")
        print(f"SQL conditions used: {', '.join(args.sql_conditions)}")

if __name__ == "__main__":
    main()
