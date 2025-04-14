from contextvars import ContextVar
from datetime import datetime


buffer: ContextVar[str | None] = ContextVar('buffer', default=None)


def info(message: any = ''):
    global buffer
    log_to_print = f'{datetime.now()} {str(message)}'
    print(log_to_print)

    buffer_value = buffer.get()
    if buffer_value is not None:
        buffer.set(buffer_value + f'{log_to_print}\n')


def start_log_buffer():
    global buffer
    buffer.set('')


def get_log_buffer() -> str:
    global buffer
    return buffer.get()


def append_to_buffer(content: str):
    global buffer
    buffer_value = buffer.get()
    if buffer_value is not None:
        buffer.set(buffer_value + content)
