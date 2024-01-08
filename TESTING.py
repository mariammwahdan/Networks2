import multiprocessing
import subprocess
import psutil
import time
import threading
import socket

index = -1
hostIp = socket.gethostbyname(socket.gethostname())


def run_peer(i):
    try:
        start_time = time.time()
        process = subprocess.Popen(
            [
                "python",
                "peer.py",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        inputs = [str(hostIp) + "\n", "9\n"]
        for input in inputs:
            process.stdin.write(input.encode())
            process.stdin.flush()

        # Wait for process to finish
        process.communicate()

        end_time = time.time()
        runtime = end_time - start_time
        print(f"Peer {i} finished")
        global index
        index += 1
        return (index, runtime)
    except Exception as e:
        print(f"Error in run_peer: {e}")
        return None


def run_chunk(start, end):
    with multiprocessing.Pool(end - start) as pool:
        runtimes = pool.map(run_peer, range(start, end))
        return runtimes


def stress_test():
    max_processes = 60
    num_of_peers = 100
    num_chunks = num_of_peers // max_processes
    processes = []
    runtimes = []

    for i in range(num_chunks):
        runtimes.extend(
            multiprocessing.Pool(max_processes).map(
                run_peer,
                range(i * max_processes, (i + 1) * max_processes),
            )
        )

    for i in range(num_chunks):
        start = i * max_processes
        end = (i + 1) * max_processes
        runtimes.extend(run_chunk(start, end))

    remainder = num_of_peers % max_processes
    if remainder > 0:
        runtimes.extend(
            run_chunk(
                num_chunks * max_processes, num_chunks * max_processes + remainder
            )
        )

    for process in processes:
        process.join()

    return runtimes


def server_thread():
    with open("server_output.txt", "w") as output_file:
        server = subprocess.Popen(
            ["python", "registery.py"],
            stdin=subprocess.PIPE,
            stdout=output_file,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        output_file.flush()
        print("Server thread started")
        time.sleep(30)
        server.kill()
        server.wait()


def main():
    # Create and start the server thread
    server_thread_instance = threading.Thread(target=server_thread)
    server_thread_instance.start()
    time.sleep(1)
    runtimes = stress_test()
    runtimes.sort()
    runtimes = [x[1] for x in runtimes]
    # Print individual runtimes

    for i, runtime in enumerate(runtimes):
        print(f"{runtime:.5f}s", end=" ")
        if i % 10 == 9:
            print()

    # Calculate and print aggregate metrics
    avg_runtime = sum(runtimes) / len(runtimes)
    max_runtime = max(runtimes)
    min_runtime = min(runtimes)
    print()
    print(f"Average runtime: {avg_runtime} seconds")
    print(f"Maximum runtime: {max_runtime} seconds")
    print(f"Minimum runtime: {min_runtime} seconds")

    # Additional Metrics
    time.sleep(15)
    cpu_percent = psutil.cpu_percent()
    virtual_memory = psutil.virtual_memory()
    print(f"CPU usage: {cpu_percent}%")
    print(f"Memory usage: {virtual_memory.percent}%")

    # Wait for the server thread to finish
    server_thread_instance.join()

#comment
if __name__ == "__main__":
    main()
