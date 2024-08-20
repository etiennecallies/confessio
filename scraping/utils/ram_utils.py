import psutil

def print_memory_usage(prefix: str = ""):
    """
    Returns the current memory usage of the Python process in megabytes (MB).
    """
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_used_mb = memory_info.rss / (1024 * 1024)

    print(f"{prefix} Memory used: {memory_used_mb:.2f} MB")