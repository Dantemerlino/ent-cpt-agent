import os
import json

def get_directory_info(target_folder):
    text_output_file = os.path.join(target_folder, "directory_contents.txt")
    json_output_file = os.path.join(target_folder, "directory_contents.json")

    directory_structure = {"name": os.path.basename(target_folder), "folders": []}

    with open(text_output_file, "w", encoding="utf-8") as f:
        f.write(f"Directory listing for: {target_folder}\n")
        f.write("=" * 60 + "\n\n")

        for root, dirs, files in os.walk(target_folder):
            # Exclude ignored directories
            dirs[:] = [d for d in dirs if d not in {'venv', '__pycache__', 'data',".git"}]

            # Relative path for readability
            relative_root = os.path.relpath(root, target_folder)

            # Write directory name to text file
            f.write(f"[DIR] {relative_root}\n")

            # Create folder structure in JSON
            folder_data = {"name": relative_root, "files": []}

            for file in files:
                if file.endswith(('.pyc', '.pyo', '.pyd')):  # Ignore pycache files
                    continue

                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)

                # Write file info to text file
                f.write(f"  - {file} ({file_size} bytes)\n")

                # Read file contents for JSON
                try:
                    with open(file_path, "r", encoding="utf-8") as file_content:
                        content = file_content.read()
                except Exception as e:
                    content = f"Error reading file: {str(e)}"

                # Add file info to JSON
                folder_data["files"].append({"name": file, "content": content})

            directory_structure["folders"].append(folder_data)
            f.write("\n")  # Add spacing for readability

    # Save JSON file
    with open(json_output_file, "w", encoding="utf-8") as json_file:
        json.dump(directory_structure, json_file, indent=4)

    print(f"Directory information saved to {text_output_file} and {json_output_file}")

if __name__ == "__main__":
    #folder_path = input("Enter the folder path: ").strip()
    folder_path = "/Users/dantemacstudio/Desktop/Claude_playground/ent-cpt-agent"
    if os.path.isdir(folder_path):
        get_directory_info(folder_path)
    else:
        print("Error: Invalid folder path.")