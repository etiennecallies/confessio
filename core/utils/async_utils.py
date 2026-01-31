import asyncio

from core.utils.log_utils import get_log_buffer, append_to_buffer, start_log_buffer


async def run_in_sync(func, *args):
    def run_and_get_log(*arguments):
        start_log_buffer()
        r = func(*arguments)
        buffer_value = get_log_buffer()

        return r, buffer_value

    loop = asyncio.get_running_loop()
    result, buffer_val = await loop.run_in_executor(None, run_and_get_log, *args)
    append_to_buffer(buffer_val)

    return result
