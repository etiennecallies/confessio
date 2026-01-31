import traceback
from contextvars import ContextVar
from datetime import datetime


buffer: ContextVar[str | None] = ContextVar('buffer', default=None)


def info(message: any = ''):
    log_to_print = f'{datetime.now()} {str(message)}'
    print(log_to_print)
    add_line_to_buffer(log_to_print)


def start_log_buffer():
    global buffer
    buffer.set('')


def get_log_buffer() -> str:
    global buffer
    return buffer.get()


def add_line_to_buffer(line: str):
    global buffer

    buffer_value = buffer.get()
    if buffer_value is not None:
        buffer.set(buffer_value + f'{line}\n')


def append_to_buffer(content: str):
    global buffer
    buffer_value = buffer.get()
    if buffer_value is not None:
        buffer.set(buffer_value + content)


def log_stack_trace():
    stack_trace = traceback.format_exc()
    if len(stack_trace) > 8000:
        info(stack_trace[:4000] + '...')
        info('...' + stack_trace[-4000:])
    else:
        info(stack_trace)
