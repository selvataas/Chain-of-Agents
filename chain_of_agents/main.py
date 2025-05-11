import asyncio
import logging
import time
import json
from typing import Optional, List, Dict, Iterator
from concurrent.futures import ThreadPoolExecutor

from .agents import WorkerAgent, ManagerAgent
from .utils import split_into_chunks, get_default_prompts, batch_process_chunks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChainOfAgents:
    """Chain of Agents implementation with async parallel decoding + streaming."""

    def __init__(
        self,
        worker_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct",
        manager_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct",
        chunk_size: int = 500,
        worker_prompt: Optional[str] = None,
        manager_prompt: Optional[str] = None
    ):
        default_worker_prompt, default_manager_prompt = get_default_prompts()
        self.worker_prompt = worker_prompt or default_worker_prompt
        self.manager_prompt = manager_prompt or default_manager_prompt
        self.chunk_size = chunk_size
        self.worker_model = worker_model
        self.manager_model = manager_model
        logger.info(f"Initialized Chain of Agents with {worker_model} workers and {manager_model} manager")

    async def run_worker_async(self, index, chunk, cu_future, query):
        print(f" Worker {index+1} is reading chunk...")
        previous_cu = await cu_future
        print(f" Worker {index+1} received CU and starts processing.")
        worker = WorkerAgent(self.worker_model, self.worker_prompt)
        result = worker.process_chunk(chunk, query, previous_cu)
        return index, result

    async def process_parallel_coa(self, chunks: List[str], query: str) -> List[str]:
        loop = asyncio.get_event_loop()
        num_chunks = len(chunks)
        cu_futures = [loop.create_future() for _ in range(num_chunks)]
        cu_futures[0].set_result(None)
        tasks = []
        results = [None] * num_chunks

        for i in range(num_chunks):
            task = asyncio.create_task(
                self.run_worker_async(i, chunks[i], cu_futures[i], query)
            )
            tasks.append(task)

        for i in range(num_chunks):
            index, output = await tasks[i]
            results[index] = output
            if i + 1 < num_chunks:
                cu_futures[i + 1].set_result(output)

        return results

    def process(self, input_text: str, query: str, use_batching: bool = False, batch_size: int = 5, threshold_keywords: Optional[List[str]] = None) -> str:
        print("Starting Chain of Agents (CoA-style)...")
        start_time = time.time()
        chunks = split_into_chunks(input_text, self.chunk_size, self.worker_model)
        print(f"Input split into {len(chunks)} chunks")
        logger.info(f"Split into {len(chunks)} chunks")

        if use_batching:
            worker = WorkerAgent(self.worker_model, self.worker_prompt)
            manager = ManagerAgent(self.manager_model, self.manager_prompt)
            threshold_keywords = threshold_keywords or ["cevap", "bulundu", "sonuç", "doğrudur"]
            worker_outputs = batch_process_chunks(
                chunks,
                query,
                batch_size,
                worker,
                manager,
                threshold_keywords
            )
        else:
            worker_outputs = asyncio.run(self.process_parallel_coa(chunks, query))

        print("All workers completed. Running manager synthesis...")
        manager = ManagerAgent(self.manager_model, self.manager_prompt)
        final_output = manager.synthesize(worker_outputs, query)

        total_time = time.time() - start_time
        print(f"Toplam işlem süresi: {total_time:.2f} saniye")
        logger.info(f"Total latency: {total_time:.2f} seconds")

        return final_output

    def process_stream(self, input_text: str, query: str) -> Iterator[Dict[str, str]]:
        print("Starting Chain of Agents (streaming mode)...")
        start_time = time.time()
        chunks = split_into_chunks(input_text, self.chunk_size, self.worker_model)
        total_chunks = len(chunks)
        print(f"Input split into {total_chunks} chunks")
        logger.info(f"Split into {total_chunks} chunks")

        yield {
            "type": "metadata",
            "content": json.dumps({
                "total_chunks": total_chunks
            })
        }

        async def stream_async():
            loop = asyncio.get_event_loop()
            cu_futures = [loop.create_future() for _ in range(total_chunks)]
            cu_futures[0].set_result(None)
            tasks = []
            results = [None] * total_chunks

            for i in range(total_chunks):
                task = asyncio.create_task(
                    self.run_worker_async(i, chunks[i], cu_futures[i], query)
                )
                tasks.append(task)

            for i in range(total_chunks):
                index, output = await tasks[i]
                results[index] = output

                yield {
                    "type": "worker",
                    "content": output,
                    "progress": {
                        "current": index + 1,
                        "total": total_chunks
                    }
                }

                if i + 1 < total_chunks:
                    cu_futures[i + 1].set_result(output)

            manager = ManagerAgent(self.manager_model, self.manager_prompt)
            final_output = manager.synthesize(results, query)

            yield {
                "type": "manager",
                "content": final_output
            }

            total_time = time.time() - start_time
            print(f" Toplam stream işlem süresi: {total_time:.2f} saniye")
            logger.info(f"Total stream latency: {total_time:.2f} seconds")

        for future_result in asyncio.run(stream_async()):
            yield future_result


























# import asyncio
# import logging
# import time
# import json
# from typing import Optional, List, Dict, Iterator
# from concurrent.futures import ThreadPoolExecutor

# from .agents import WorkerAgent, ManagerAgent
# from .utils import split_into_chunks, get_default_prompts

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# class ChainOfAgents:
#     """Chain of Agents implementation with async parallel decoding + streaming."""

#     def __init__(
#         self,
#         worker_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct",
#         manager_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct",
#         chunk_size: int = 500,
#         worker_prompt: Optional[str] = None,
#         manager_prompt: Optional[str] = None
#     ):
#         default_worker_prompt, default_manager_prompt = get_default_prompts()
#         self.worker_prompt = worker_prompt or default_worker_prompt
#         self.manager_prompt = manager_prompt or default_manager_prompt
#         self.chunk_size = chunk_size
#         self.worker_model = worker_model
#         self.manager_model = manager_model
#         logger.info(f"Initialized Chain of Agents with {worker_model} workers and {manager_model} manager")

#     async def run_worker_async(self, index, chunk, cu_future, query):
#         print(f" Worker {index+1} is reading chunk...")
#         previous_cu = await cu_future
#         print(f" Worker {index+1} received CU and starts processing.")
#         worker = WorkerAgent(self.worker_model, self.worker_prompt)
#         result = worker.process_chunk(chunk, query, previous_cu)
#         return index, result

#     async def process_parallel_coa(self, chunks: List[str], query: str) -> List[str]:
#         loop = asyncio.get_event_loop()
#         num_chunks = len(chunks)
#         cu_futures = [loop.create_future() for _ in range(num_chunks)]
#         cu_futures[0].set_result(None)
#         tasks = []
#         results = [None] * num_chunks

#         for i in range(num_chunks):
#             task = asyncio.create_task(
#                 self.run_worker_async(i, chunks[i], cu_futures[i], query)
#             )
#             tasks.append(task)

#         for i in range(num_chunks):
#             index, output = await tasks[i]
#             results[index] = output
#             if i + 1 < num_chunks:
#                 cu_futures[i + 1].set_result(output)

#         return results

#     def process(self, input_text: str, query: str) -> str:
#         print("Starting Chain of Agents (CoA-style parallel mode)...")
#         start_time = time.time()
#         chunks = split_into_chunks(input_text, self.chunk_size, self.worker_model)
#         print(f"Input split into {len(chunks)} chunks")
#         logger.info(f"Split into {len(chunks)} chunks")

#         worker_outputs = asyncio.run(self.process_parallel_coa(chunks, query))

#         print("All workers completed. Running manager synthesis...")
#         manager = ManagerAgent(self.manager_model, self.manager_prompt)
#         final_output = manager.synthesize(worker_outputs, query)

#         total_time = time.time() - start_time
#         print(f"Toplam işlem süresi: {total_time:.2f} saniye")
#         logger.info(f"Total latency: {total_time:.2f} seconds")

#         return final_output

#     def process_stream(self, input_text: str, query: str) -> Iterator[Dict[str, str]]:
#         print("Starting Chain of Agents (streaming mode)...")
#         start_time = time.time()
#         chunks = split_into_chunks(input_text, self.chunk_size, self.worker_model)
#         total_chunks = len(chunks)
#         print(f"Input split into {total_chunks} chunks")
#         logger.info(f"Split into {total_chunks} chunks")

#         yield {
#             "type": "metadata",
#             "content": json.dumps({
#                 "total_chunks": total_chunks
#             })
#         }

#         async def stream_async():
#             loop = asyncio.get_event_loop()
#             cu_futures = [loop.create_future() for _ in range(total_chunks)]
#             cu_futures[0].set_result(None)
#             tasks = []
#             results = [None] * total_chunks

#             for i in range(total_chunks):
#                 task = asyncio.create_task(
#                     self.run_worker_async(i, chunks[i], cu_futures[i], query)
#                 )
#                 tasks.append(task)

#             for i in range(total_chunks):
#                 index, output = await tasks[i]
#                 results[index] = output

#                 yield {
#                     "type": "worker",
#                     "content": output,
#                     "progress": {
#                         "current": index + 1,
#                         "total": total_chunks
#                     }
#                 }

#                 if i + 1 < total_chunks:
#                     cu_futures[i + 1].set_result(output)

#             # Manager işlemi
#             manager = ManagerAgent(self.manager_model, self.manager_prompt)
#             final_output = manager.synthesize(results, query)

#             yield {
#                 "type": "manager",
#                 "content": final_output
#             }

#             total_time = time.time() - start_time
#             print(f" Toplam stream işlem süresi: {total_time:.2f} saniye")
#             logger.info(f"Total stream latency: {total_time:.2f} seconds")

#         # Stream'i senkron iterator gibi çalıştır
#         for future_result in asyncio.run(stream_async()):
#             yield future_result

#----------------

# import asyncio
# import logging
# import time
# import json
# from typing import Optional, List, Dict, Iterator
# from concurrent.futures import ThreadPoolExecutor

# from .agents import WorkerAgent, ManagerAgent
# from .utils import split_into_chunks, get_default_prompts

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# class ChainOfAgents:
#     """Chain of Agents implementation with async parallel decoding."""

#     def __init__(
#         self,
#         worker_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct",
#         manager_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct",
#         chunk_size: int = 500,
#         worker_prompt: Optional[str] = None,
#         manager_prompt: Optional[str] = None
#     ):
#         default_worker_prompt, default_manager_prompt = get_default_prompts()
#         self.worker_prompt = worker_prompt or default_worker_prompt
#         self.manager_prompt = manager_prompt or default_manager_prompt
#         self.chunk_size = chunk_size
#         self.worker_model = worker_model
#         self.manager_model = manager_model
#         logger.info(f"Initialized Chain of Agents with {worker_model} workers and {manager_model} manager")

#     async def run_worker_async(self, index, chunk, cu_future, query):
#         print(f" Worker {index+1} is reading chunk...")
#         previous_cu = await cu_future  # Bekle, CU hazır olunca devam ediyoruz

#         print(f"🚦 Worker {index+1} received CU and starts processing.")
#         worker = WorkerAgent(self.worker_model, self.worker_prompt)
#         result = worker.process_chunk(chunk, query, previous_cu)
#         return index, result

#     async def process_parallel_coa(self, chunks: List[str], query: str) -> List[str]:
#         loop = asyncio.get_event_loop()
#         num_chunks = len(chunks)

#         # Gelecekteki CU zincirini tanımlıyoruz
#         cu_futures = [loop.create_future() for _ in range(num_chunks)]
#         cu_futures[0].set_result(None)  # İlk CU boş başlar

#         tasks = []
#         results = [None] * num_chunks

#         for i in range(num_chunks):
#             task = asyncio.create_task(
#                 self.run_worker_async(i, chunks[i], cu_futures[i], query)
#             )
#             tasks.append(task)

#         for i in range(num_chunks):
#             index, output = await tasks[i]
#             results[index] = output

#             if i + 1 < num_chunks:
#                 cu_futures[i + 1].set_result(output)

#         return results

#     def process(self, input_text: str, query: str) -> str:
#         print("Starting Chain of Agents (CoA-style parallel mode)...")
#         start_time = time.time()

#         chunks = split_into_chunks(input_text, self.chunk_size, self.worker_model)
#         print(f"Input split into {len(chunks)} chunks")
#         logger.info(f"Split into {len(chunks)} chunks")

#         worker_outputs = asyncio.run(self.process_parallel_coa(chunks, query))

#         print("All workers completed. Running manager synthesis...")
#         manager = ManagerAgent(self.manager_model, self.manager_prompt)
#         final_output = manager.synthesize(worker_outputs, query)

#         total_time = time.time() - start_time
#         print(f"✅ Toplam işlem süresi: {total_time:.2f} saniye")
#         logger.info(f"Total latency: {total_time:.2f} seconds")

#         return final_output














# from typing import Optional, Iterator, Dict, List
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from .agents import WorkerAgent, ManagerAgent
# from .utils import split_into_chunks, get_default_prompts
# import logging
# import json
# import time

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class ChainOfAgents:
#     """Main class for the Chain of Agents implementation."""

#     def __init__(
#         self,
#         worker_model: str = "Qwen/Qwen3-14B",
#         manager_model: str = "Qwen/Qwen3-14B",
#         chunk_size: int = 500,
#         worker_prompt: Optional[str] = None,
#         manager_prompt: Optional[str] = None
#     ):
#         default_worker_prompt, default_manager_prompt = get_default_prompts()
#         self.worker_prompt = worker_prompt or default_worker_prompt
#         self.manager_prompt = manager_prompt or default_manager_prompt
#         self.chunk_size = chunk_size
#         self.worker_model = worker_model
#         self.manager_model = manager_model
#         logger.info(f"Initialized Chain of Agents with {worker_model} workers and {manager_model} manager")

#     def process(self, input_text: str, query: str) -> str:
#         print("🚀 Starting Chain of Agents (process mode)...")
#         start_time = time.time()

#         chunks = split_into_chunks(input_text, self.chunk_size, self.worker_model)
#         print(f"🔍 Input split into {len(chunks)} chunks")
#         logger.info(f"Split into {len(chunks)} chunks")

#         # Step 1: Compute previous_cu sequentially
#         previous_cus = []
#         previous_cu = None
#         for i, chunk in enumerate(chunks):
#             print(f"🔄 Computing previous_cu for chunk {i+1}/{len(chunks)}")
#             previous_cus.append(previous_cu)
#             worker = WorkerAgent(self.worker_model, self.worker_prompt)
#             previous_cu = worker.process_chunk(chunk, query, previous_cu)

#         # Step 2: Run workers in parallel using ThreadPoolExecutor
#         def run_worker(chunk, prev):
#             worker = WorkerAgent(self.worker_model, self.worker_prompt)
#             return worker.process_chunk(chunk, query, prev)

#         with ThreadPoolExecutor() as executor:
#             worker_outputs = list(executor.map(run_worker, chunks, previous_cus))

#         print("🧠 All workers completed. Running manager synthesis...")
#         logger.info("All workers done. Synthesizing final output.")
#         manager = ManagerAgent(self.manager_model, self.manager_prompt)
#         final_output = manager.synthesize(worker_outputs, query)

#         total_time = time.time() - start_time
#         print(f"✅ Toplam işlem süresi: {total_time:.2f} saniye")
#         logger.info(f"Total latency: {total_time:.2f} seconds")

#         return final_output

#     def process_stream(self, input_text: str, query: str) -> Iterator[Dict[str, str]]:
#         print("🚀 Starting Chain of Agents (stream mode)...")
#         start_time = time.time()

#         chunks = split_into_chunks(input_text, self.chunk_size, self.worker_model)
#         total_chunks = len(chunks)
#         print(f"🔍 Input split into {total_chunks} chunks")
#         logger.info(f"Split into {total_chunks} chunks")

#         previous_cus = []
#         previous_cu = None
#         for i, chunk in enumerate(chunks):
#             print(f"🔄 Computing previous_cu for chunk {i+1}/{total_chunks}")
#             previous_cus.append(previous_cu)
#             worker = WorkerAgent(self.worker_model, self.worker_prompt)
#             previous_cu = worker.process_chunk(chunk, query, previous_cu)

#         def run_worker(index, chunk, prev):
#             t0 = time.time()
#             worker = WorkerAgent(self.worker_model, self.worker_prompt)
#             result = worker.process_chunk(chunk, query, prev)
#             elapsed = time.time() - t0
#             print(f"🧩 Worker {index+1} finished in {elapsed:.2f}s")
#             logger.info(f"Worker {index+1} processed in {elapsed:.2f}s")
#             return index, result

#         yield {
#             "type": "metadata",
#             "content": json.dumps({
#                 "total_chunks": total_chunks,
#                 "total_pages": getattr(input_text, 'total_pages', 0)
#             })
#         }

#         results_map = [None] * total_chunks

#         with ThreadPoolExecutor() as executor:
#             futures = [
#                 executor.submit(run_worker, i, chunk, previous_cus[i])
#                 for i, chunk in enumerate(chunks)
#             ]
#             for f in as_completed(futures):
#                 idx, output = f.result()
#                 results_map[idx] = output
#                 yield {
#                     "type": "worker",
#                     "content": output,
#                     "progress": {
#                         "current": idx + 1,
#                         "total": total_chunks
#                     }
#                 }

#         print("🧠 Synthesizing manager output...")
#         logger.info("Manager processing after stream.")

#         manager = ManagerAgent(self.manager_model, self.manager_prompt)
#         final_output = manager.synthesize(results_map, query)

#         total_time = time.time() - start_time
#         print(f"✅ Toplam stream işlem süresi: {total_time:.2f} saniye")
#         logger.info(f"Total stream latency: {total_time:.2f}s")

#         yield {
#             "type": "manager",
#             "content": final_output
#         }















# from typing import Optional, Iterator, Dict, List
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from .agents import WorkerAgent, ManagerAgent
# from .utils import split_into_chunks, get_default_prompts
# import logging
# import json
# import time  # ⏱️ Latency ölçümü için

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class ChainOfAgents:
#     """Main class for the Chain of Agents implementation."""

#     def __init__(
#         self,
#         worker_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct",
#         manager_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct",
#         chunk_size: int = 500,
#         worker_prompt: Optional[str] = None,
#         manager_prompt: Optional[str] = None
#     ):
#         default_worker_prompt, default_manager_prompt = get_default_prompts()

#         self.worker_prompt = worker_prompt or default_worker_prompt
#         self.manager_prompt = manager_prompt or default_manager_prompt
#         self.chunk_size = chunk_size
#         self.worker_model = worker_model
#         self.manager_model = manager_model

#         logger.info(f"Initialized Chain of Agents with {worker_model} workers and {manager_model} manager")

#     def process(self, input_text: str, query: str) -> str:
#         """Process a long text input using the Chain of Agents with parallel workers and previous_cu support."""
#         print("🚀 Starting Chain of Agents (process mode)...")
#         start_time = time.time()

#         chunks = split_into_chunks(input_text, self.chunk_size, self.worker_model)
#         logger.info(f"Split into {len(chunks)} chunks")
#         print(f"🔍 Input split into {len(chunks)} chunks")

#         previous_cus = []
#         previous_cu = None

#         for i, chunk in enumerate(chunks):
#             logger.info(f"[Prepass] Computing CU for chunk {i+1}/{len(chunks)}")
#             previous_cus.append(previous_cu)
#             worker = WorkerAgent(self.worker_model, self.worker_prompt)
#             previous_cu = worker.process_chunk(chunk, query, previous_cu)

#         def run_worker(chunk, prev):
#             worker = WorkerAgent(self.worker_model, self.worker_prompt)
#             return worker.process_chunk(chunk, query, prev)

#         with ThreadPoolExecutor() as executor:
#             worker_outputs = list(executor.map(run_worker, chunks, previous_cus))

#         logger.info("All workers done. Synthesizing final output.")
#         print("🧠 All workers completed. Running manager synthesis...")

#         manager = ManagerAgent(self.manager_model, self.manager_prompt)
#         final_output = manager.synthesize(worker_outputs, query)

#         total_time = time.time() - start_time
#         logger.info(f"Total latency: {total_time:.2f} seconds")
#         print(f"✅ Total latency: {total_time:.2f} seconds")

#         return final_output

#     def process_stream(self, input_text: str, query: str) -> Iterator[Dict[str, str]]:
#         """Stream worker and manager outputs with parallel workers and preserved previous_cu."""
#         print("🚀 Starting Chain of Agents (stream mode)...")
#         start_time = time.time()

#         chunks = split_into_chunks(input_text, self.chunk_size, self.worker_model)
#         total_chunks = len(chunks)
#         previous_cus = []

#         previous_cu = None
#         for i, chunk in enumerate(chunks):
#             logger.info(f"[Prepass-stream] Computing CU for chunk {i+1}/{total_chunks}")
#             previous_cus.append(previous_cu)
#             worker = WorkerAgent(self.worker_model, self.worker_prompt)
#             previous_cu = worker.process_chunk(chunk, query, previous_cu)

#         def run_worker(index, chunk, prev):
#             t0 = time.time()
#             worker = WorkerAgent(self.worker_model, self.worker_prompt)
#             result = worker.process_chunk(chunk, query, prev)
#             elapsed = time.time() - t0
#             logger.info(f"Worker {index+1} processed in {elapsed:.2f}s")
#             print(f"🧩 Worker {index+1} done in {elapsed:.2f}s")
#             return index, result

#         yield {
#             "type": "metadata",
#             "content": json.dumps({
#                 "total_chunks": total_chunks,
#                 "total_pages": getattr(input_text, 'total_pages', 0)
#             })
#         }

#         results_map = [None] * total_chunks

#         with ThreadPoolExecutor() as executor:
#             futures = [
#                 executor.submit(run_worker, i, chunk, previous_cus[i])
#                 for i, chunk in enumerate(chunks)
#             ]
#             for f in as_completed(futures):
#                 idx, output = f.result()
#                 results_map[idx] = output
#                 yield {
#                     "type": "worker",
#                     "content": output,
#                     "progress": {
#                         "current": idx + 1,
#                         "total": total_chunks
#                     }
#                 }

#         logger.info("Manager processing after stream.")
#         print("🧠 Synthesizing manager output...")

#         manager = ManagerAgent(self.manager_model, self.manager_prompt)
#         final_output = manager.synthesize(results_map, query)

#         total_time = time.time() - start_time
#         logger.info(f"Total stream latency: {total_time:.2f}s")
#         print(f"✅ Total stream latency: {total_time:.2f} seconds")

#         yield {
#             "type": "manager",
#             "content": final_output
#         }

# from typing import Optional, Iterator, Dict, List
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from .agents import WorkerAgent, ManagerAgent
# from .utils import split_into_chunks, get_default_prompts
# import logging
# import json
# import time  

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class ChainOfAgents:
#     """Main class for the Chain of Agents implementation."""

#     def __init__(
#         self,
#         worker_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct",
#         manager_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct",
#         chunk_size: int = 500,
#         worker_prompt: Optional[str] = None,
#         manager_prompt: Optional[str] = None
#     ):
#         default_worker_prompt, default_manager_prompt = get_default_prompts()

#         self.worker_prompt = worker_prompt or default_worker_prompt
#         self.manager_prompt = manager_prompt or default_manager_prompt
#         self.chunk_size = chunk_size
#         self.worker_model = worker_model
#         self.manager_model = manager_model

#         logger.info(f"Initialized Chain of Agents with {worker_model} workers and {manager_model} manager")

#     def process(self, input_text: str, query: str) -> str:
#         """Process a long text input using the Chain of Agents with parallel workers and previous_cu support."""
#         start_time = time.time()

#         chunks = split_into_chunks(input_text, self.chunk_size, self.worker_model)
#         logger.info(f"Split into {len(chunks)} chunks")

#         # Step 1: Prepare previous_cu values sequentially
#         previous_cus = []
#         previous_cu = None

#         for i, chunk in enumerate(chunks):
#             logger.info(f"[Prepass] Computing CU for chunk {i+1}/{len(chunks)}")
#             previous_cus.append(previous_cu)
#             worker = WorkerAgent(self.worker_model, self.worker_prompt)
#             previous_cu = worker.process_chunk(chunk, query, previous_cu)

#         # Step 2: Re-run all workers in parallel with the prepared previous_cus
#         def run_worker(chunk, prev):
#             worker = WorkerAgent(self.worker_model, self.worker_prompt)
#             return worker.process_chunk(chunk, query, prev)

#         with ThreadPoolExecutor() as executor:
#             worker_outputs = list(executor.map(run_worker, chunks, previous_cus))

#         # Step 3: Final synthesis with manager
#         logger.info("All workers done. Synthesizing final output.")
#         manager = ManagerAgent(self.manager_model, self.manager_prompt)
#         final_output = manager.synthesize(worker_outputs, query)

#         total_time = time.time() - start_time
#         logger.info(f"Total latency: {total_time:.2f} seconds")
#         return final_output

#     def process_stream(self, input_text: str, query: str) -> Iterator[Dict[str, str]]:
#         """Stream worker and manager outputs with parallel workers and preserved previous_cu."""
#         start_time = time.time()

#         chunks = split_into_chunks(input_text, self.chunk_size, self.worker_model)
#         total_chunks = len(chunks)
#         previous_cus = []

#         # Step 1: Prepare previous_cu values sequentially
#         previous_cu = None
#         for i, chunk in enumerate(chunks):
#             logger.info(f"[Prepass-stream] Computing CU for chunk {i+1}/{total_chunks}")
#             previous_cus.append(previous_cu)
#             worker = WorkerAgent(self.worker_model, self.worker_prompt)
#             previous_cu = worker.process_chunk(chunk, query, previous_cu)

#         # Step 2: Launch parallel worker processing
#         def run_worker(index, chunk, prev):
#             t0 = time.time()
#             worker = WorkerAgent(self.worker_model, self.worker_prompt)
#             result = worker.process_chunk(chunk, query, prev)
#             elapsed = time.time() - t0
#             logger.info(f"Worker {index+1} processed in {elapsed:.2f}s")
#             return index, result

#         yield {
#             "type": "metadata",
#             "content": json.dumps({
#                 "total_chunks": total_chunks,
#                 "total_pages": getattr(input_text, 'total_pages', 0)
#             })
#         }

#         results_map = [None] * total_chunks

#         with ThreadPoolExecutor() as executor:
#             futures = [
#                 executor.submit(run_worker, i, chunk, previous_cus[i])
#                 for i, chunk in enumerate(chunks)
#             ]
#             for f in as_completed(futures):
#                 idx, output = f.result()
#                 results_map[idx] = output
#                 yield {
#                     "type": "worker",
#                     "content": output,
#                     "progress": {
#                         "current": idx + 1,
#                         "total": total_chunks
#                     }
#                 }

#         # Step 3: Final synthesis
#         logger.info("Manager processing after stream.")
#         manager = ManagerAgent(self.manager_model, self.manager_prompt)
#         final_output = manager.synthesize(results_map, query)

#         logger.info(f"Total stream latency: {time.time() - start_time:.2f}s")
#         yield {
#             "type": "manager",
#             "content": final_output
#         }


    # def process_stream(self, input_text: str, query: str) -> Iterator[Dict[str, str]]:
    #     """Stream worker and manager outputs with parallel workers and preserved previous_cu."""
    #     chunks = split_into_chunks(input_text, self.chunk_size, self.worker_model)
    #     total_chunks = len(chunks)
    #     previous_cus = []

    #     # Step 1: Prepare previous_cu values sequentially
    #     previous_cu = None
    #     for i, chunk in enumerate(chunks):
    #         logger.info(f"[Prepass-stream] Computing CU for chunk {i+1}/{total_chunks}")
    #         previous_cus.append(previous_cu)
    #         worker = WorkerAgent(self.worker_model, self.worker_prompt)
    #         previous_cu = worker.process_chunk(chunk, query, previous_cu)

    #     # Step 2: Launch parallel worker processing
    #     def run_worker(index, chunk, prev):
    #         worker = WorkerAgent(self.worker_model, self.worker_prompt)
    #         result = worker.process_chunk(chunk, query, prev)
    #         return index, result

    #     yield {
    #         "type": "metadata",
    #         "content": json.dumps({
    #             "total_chunks": total_chunks,
    #             "total_pages": getattr(input_text, 'total_pages', 0)
    #         })
    #     }

    #     results_map = [None] * total_chunks

    #     with ThreadPoolExecutor() as executor:
    #         futures = [
    #             executor.submit(run_worker, i, chunk, previous_cus[i])
    #             for i, chunk in enumerate(chunks)
    #         ]
    #         for f in as_completed(futures):
    #             idx, output = f.result()
    #             results_map[idx] = output
    #             yield {
    #                 "type": "worker",
    #                 "content": output,
    #                 "progress": {
    #                     "current": idx + 1,
    #                     "total": total_chunks
    #                 }
    #             }

    #     # Step 3: Final synthesis
    #     logger.info("Manager processing after stream.")
    #     manager = ManagerAgent(self.manager_model, self.manager_prompt)
    #     final_output = manager.synthesize(results_map, query)

    #     yield {
    #         "type": "manager",
    #         "content": final_output
    #     }

# from typing import Optional, Iterator, Dict
# from .agents import WorkerAgent, ManagerAgent
# from .utils import split_into_chunks, get_default_prompts
# import logging
# import json

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class ChainOfAgents:
#     """Main class for the Chain of Agents implementation."""
    
#     def __init__(
#         self,
#         worker_model: str = "Meta-Llama-3.1-8B-Instruct",  # Together AI model
#         manager_model: str = "Meta-Llama-3.1-8B-Instruct",  # Together AI model
#         chunk_size: int = 500,
#         worker_prompt: Optional[str] = None,
#         manager_prompt: Optional[str] = None
#     ):
#         """
#         Initialize the Chain of Agents.
        
#         Args:
#             worker_model: Model to use for worker agents
#             manager_model: Model to use for manager agent
#             chunk_size: Maximum tokens per chunk
#             worker_prompt: Custom system prompt for workers
#             manager_prompt: Custom system prompt for manager
#         """
#         default_worker_prompt, default_manager_prompt = get_default_prompts()
        
#         self.worker_prompt = worker_prompt or default_worker_prompt
#         self.manager_prompt = manager_prompt or default_manager_prompt
#         self.chunk_size = chunk_size
#         self.worker_model = worker_model
#         self.manager_model = manager_model
        
#         logger.info(f"Initialized Chain of Agents with {worker_model} workers and {manager_model} manager")
    
#     def process(self, input_text: str, query: str) -> str:
#         """
#         Process a long text input using the Chain of Agents.
        
#         Args:
#             input_text: The long input text to process
#             query: The user's query about the text
            
#         Returns:
#             str: The final response from the manager agent
#         """
#         # Split text into chunks
#         chunks = split_into_chunks(input_text, self.chunk_size, self.worker_model)
        
#         # Process chunks with worker agents
#         worker_outputs = []
#         previous_cu = None
        
#         for i, chunk in enumerate(chunks):
#             logger.info(f"Processing chunk {i+1}/{len(chunks)}")
#             worker = WorkerAgent(self.worker_model, self.worker_prompt)
#             output = worker.process_chunk(chunk, query, previous_cu)
#             worker_outputs.append(output)
#             previous_cu = output
        
#         # Synthesize results with manager agent
#         manager = ManagerAgent(self.manager_model, self.manager_prompt)
#         final_output = manager.synthesize(worker_outputs, query)
        
#         return final_output 
    
#     def process_stream(self, input_text: str, query: str) -> Iterator[Dict[str, str]]:
#         """Process text with streaming - yields worker and manager messages."""
#         worker_outputs = []
#         previous_cu = None
        
#         chunks = split_into_chunks(input_text, self.chunk_size, self.worker_model)
#         total_chunks = len(chunks)
        
#         # Debug logging for metadata
#         metadata_message = {
#             "type": "metadata",
#             "content": json.dumps({
#                 "total_chunks": total_chunks,
#                 "total_pages": getattr(input_text, 'total_pages', 0)
#             })
#         }
#         logger.info(f"Sending metadata: {metadata_message}")  # Debug log
#         yield metadata_message
        
#         for i, chunk in enumerate(chunks):
#             logger.info(f"Processing chunk {i+1}/{total_chunks}")
#             worker = WorkerAgent(self.worker_model, self.worker_prompt)
#             output = worker.process_chunk(chunk, query, previous_cu)
#             worker_outputs.append(output)
#             previous_cu = output
            
#             # Debug logging for worker message
#             worker_message = {
#                 "type": "worker",
#                 "content": output,
#                 "progress": {
#                     "current": i + 1,
#                     "total": total_chunks
#                 }
#             }
#             logger.info(f"Sending worker message: {worker_message}")  # Debug log
#             yield worker_message
        
#         logger.info("Processing manager synthesis")
#         manager = ManagerAgent(self.manager_model, self.manager_prompt)
#         final_output = manager.synthesize(worker_outputs, query)
        
#         yield {
#             "type": "manager",
#             "content": final_output
#         } 