#!/bin/bash

# Exit on error
set -e

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    echo "NEBIUS_API_KEY=" > .env
    echo "Please add your Nebius API key to the .env file"
    exit 1
fi

# Run example
echo "Running Chain of Agents example..."
python3 - << EOF
from chain_of_agents import ChainOfAgents
from chain_of_agents.utils import read_pdf
import os
from dotenv import load_dotenv
import pathlib
import sys
import time

# Load environment variables
env_path = pathlib.Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Verify API key is loaded
if not os.getenv("NEBIUS_API_KEY"):
    raise ValueError("NEBIUS_API_KEY not found in environment variables")

# Initialize Chain of Agents
coa = ChainOfAgents(
    worker_model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    manager_model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    chunk_size=500
)

# Read PDF file
pdf_path = "MRKP0023.pdf"
if not os.path.exists(pdf_path):
    print(f"Error: PDF file not found at {pdf_path}")
    sys.exit(1)

input_text = read_pdf(pdf_path)
query = "Bu sözleşmede taraflar arasındaki yükümlülükleri çıkar."



# Run full processing with latency tracking
print("\n Processing document with Chain of Agents...\n")
start_time = time.time()

final_output = coa.process(input_text, query, use_batching=True, batch_size=5)


elapsed = time.time() - start_time
print("\n" + "=" * 80)
print("FINAL OUTPUT")
print("=" * 80 + "\n")
print(final_output)

print(f"\n Script toplam süresi: {elapsed:.2f} saniye\n")
EOF

# Deactivate virtual environment
deactivate

echo "Done!"









# #!/bin/bash

# # Exit on error
# set -e

# # Check if virtual environment exists
# if [ ! -d "venv" ]; then
#     echo "Creating virtual environment..."
#     python3 -m venv venv
# fi

# # Activate virtual environment
# source venv/bin/activate

# # Install requirements
# echo "Installing requirements..."
# pip install -r requirements.txt

# # Check if .env file exists
# if [ ! -f ".env" ]; then
#     echo "Creating .env file..."
#     echo "NEBIUS_API_KEY=" > .env
#     echo "Please add your Nebius API key to the .env file"
#     exit 1
# fi



# # Run example
# echo "Running Chain of Agents example..."
# python3 - << EOF
# from chain_of_agents import ChainOfAgents
# from chain_of_agents.utils import read_pdf, split_into_chunks
# from chain_of_agents.agents import WorkerAgent, ManagerAgent
# import os
# from dotenv import load_dotenv
# import pathlib
# import sys

# # Load environment variables
# env_path = pathlib.Path('.') / '.env'
# load_dotenv(dotenv_path=env_path)

# # Verify API key is loaded
# if not os.getenv("NEBIUS_API_KEY"):
#     raise ValueError("NEBIUS_API_KEY not found in environment variables")

# # Initialize Chain of Agents
# coa = ChainOfAgents(
#     worker_model="meta-llama/Meta-Llama-3.1-8B-Instruct",
#     manager_model="meta-llama/Meta-Llama-3.1-8B-Instruct",
#     chunk_size=500  # Reduced chunk size for better handling
# )

# # Read PDF file
# pdf_path = "MRKP0023.pdf"  # Updated to your PDF file
# if not os.path.exists(pdf_path):
#     print(f"Error: PDF file not found at {pdf_path}")
#     sys.exit(1)

# input_text = read_pdf(pdf_path)
# query = "Bu sözleşmede taraflar arasındaki yükümlülükleri çıkar."

# # Process the text
# print("\nProcessing document with Chain of Agents...\n")

# chunks = split_into_chunks(input_text, coa.chunk_size, coa.worker_model)
# worker_outputs = []
# previous_cu = None

# print("=" * 80)
# print("WORKER RESPONSES")
# print("=" * 80 + "\n")

# for i, chunk in enumerate(chunks):
#     print(f"\n{'='*30} Worker {i+1}/{len(chunks)} {'='*30}")
#     worker = WorkerAgent(coa.worker_model, coa.worker_prompt)
#     output = worker.process_chunk(chunk, query, previous_cu)
#     worker_outputs.append(output)
#     previous_cu = output
#     print(f"\n{output}\n")

# print("\n" + "=" * 80)
# print("MANAGER SYNTHESIS")
# print("=" * 80 + "\n")

# manager = ManagerAgent(coa.manager_model, coa.manager_prompt)
# final_output = manager.synthesize(worker_outputs, query)
# print(final_output)

# print("\n" + "=" * 80)
# EOF

# # Deactivate virtual environment
# deactivate

# echo "Done!" 