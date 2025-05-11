from typing import List, Optional
import logging
import fitz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_pdf(pdf_path: str) -> str:
    try:
        text = []
        with fitz.open(pdf_path) as doc:
            logger.info(f"Processing PDF with {len(doc)} pages")
            for page in doc:
                text.append(page.get_text())
        return "\n".join(filter(None, text))
    except Exception as e:
        logger.error(f"Error reading PDF: {str(e)}")
        raise

def split_into_chunks(text: str, chunk_size: int, model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct") -> List[str]:
    paragraphs = text.split('\n\n')
    current_chunk = []
    chunks = []

    for paragraph in paragraphs:
        if not paragraph.strip():
            continue

        paragraph_words = paragraph.split()

        if len(current_chunk) + len(paragraph_words) > chunk_size:
            if current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []

            while len(paragraph_words) > chunk_size:
                chunks.append(' '.join(paragraph_words[:chunk_size]))
                paragraph_words = paragraph_words[chunk_size:]

            current_chunk = paragraph_words
        else:
            current_chunk.extend(paragraph_words)

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    logger.info(f"Split text into {len(chunks)} chunks")
    return chunks

def count_tokens(text: str, model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct") -> int:
    return len(text.split())

def get_default_prompts() -> tuple[str, str]:
    worker_prompt = """You are a worker agent responsible for analyzing a portion of a document.
Your task is to identify key information related to the user's query and provide clear, concise analysis."""

    manager_prompt = """You are a manager agent responsible for synthesizing information from multiple workers.
Your task is to combine their analyses into a coherent, comprehensive response that directly answers the user's query."""

    return worker_prompt, manager_prompt

def batch_process_chunks(
    chunks: List[str],
    query: str,
    batch_size: int,
    worker_agent,
    manager_agent,
    threshold_keywords: List[str]
) -> List[str]:
    def chunk_batches(chunks: List[str], size: int) -> List[List[str]]:
        return [chunks[i:i + size] for i in range(0, len(chunks), size)]

    all_outputs = []
    batches = chunk_batches(chunks, batch_size)

    for i, batch in enumerate(batches):
        logger.info(f"Processing batch {i+1}/{len(batches)}")
        batch_outputs = [worker_agent.process_chunk(chunk, query) for chunk in batch]
        all_outputs.extend(batch_outputs)

        synthesized_response = manager_agent.synthesize(all_outputs, query)
        if any(keyword.lower() in synthesized_response.lower() for keyword in threshold_keywords):
            logger.info(f"Stopping early at batch {i+1}, manager is satisfied.")
            break

    return all_outputs



























# from typing import List
# import logging
# import fitz  

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# def read_pdf(pdf_path: str) -> str:
#     """
#     Read text content from a PDF file.
    
#     Args:
#         pdf_path: Path to the PDF file
        
#     Returns:
#         str: Extracted text from the PDF
#     """
#     try:
#         text = []
#         with fitz.open(pdf_path) as doc:
#             logger.info(f"Processing PDF with {len(doc)} pages")
#             for page in doc:
#                 text.append(page.get_text())
        
#         return "\n".join(filter(None, text))  # Filter out empty strings
#     except Exception as e:
#         logger.error(f"Error reading PDF: {str(e)}")
#         raise

# def split_into_chunks(text: str, chunk_size: int, model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct") -> List[str]:
#     """
#     Split text into chunks based on word count.
    
#     Args:
#         text: The input text to split
#         chunk_size: Maximum number of words per chunk
#         model: Not used, kept for compatibility
        
#     Returns:
#         List[str]: List of text chunks
#     """
#     # Split by paragraphs first to maintain context
#     paragraphs = text.split('\n\n')
#     words = []
#     current_chunk = []
#     chunks = []
    
#     for paragraph in paragraphs:
#         # Skip empty paragraphs
#         if not paragraph.strip():
#             continue
            
#         paragraph_words = paragraph.split()
        
#         # If adding this paragraph exceeds chunk size, save current chunk and start new one
#         if len(current_chunk) + len(paragraph_words) > chunk_size:
#             if current_chunk:  # Save current chunk if it exists
#                 chunks.append(' '.join(current_chunk))
#                 current_chunk = []
            
#             # Handle paragraphs larger than chunk_size
#             while len(paragraph_words) > chunk_size:
#                 chunks.append(' '.join(paragraph_words[:chunk_size]))
#                 paragraph_words = paragraph_words[chunk_size:]
            
#             current_chunk = paragraph_words
#         else:
#             current_chunk.extend(paragraph_words)
    
#     # Add any remaining text
#     if current_chunk:
#         chunks.append(' '.join(current_chunk))
    
#     logger.info(f"Split text into {len(chunks)} chunks")
#     return chunks

# def count_tokens(text: str, model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct") -> int:
#     """
#     Count the number of words in a text string.
    
#     Args:
#         text: The input text
#         model: Not used, kept for compatibility
        
#     Returns:
#         int: Number of words
#     """
#     return len(text.split())

# def get_default_prompts() -> tuple[str, str]:
#     """
#     Get default system prompts for worker and manager agents.
    
#     Returns:
#         tuple[str, str]: (worker_prompt, manager_prompt)
#     """
#     worker_prompt = """You are a worker agent responsible for analyzing a portion of a document.
# Your task is to identify key information related to the user's query and provide clear, concise analysis."""

#     manager_prompt = """You are a manager agent responsible for synthesizing information from multiple workers.
# Your task is to combine their analyses into a coherent, comprehensive response that directly answers the user's query."""

#     return worker_prompt, manager_prompt 