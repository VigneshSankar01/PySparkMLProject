import os

# The exact command needed for EMR
script_content = b"""#!/bin/bash
sudo pip3 install "numpy<2.0" "pandas<2.2" sentence-transformers --ignore-installed --no-cache-dir
"""

# Define the path to overwrite the existing file in the scripts folder
file_path = os.path.join("scripts", "bootstrap_emr.sh")

# Write the file specifically with Linux line endings ("\n")
with open(file_path, "w", newline="\n") as f:
    f.write(script_content)

print(f"SUCCESS: Created {file_path} with correct Linux formatting.")
