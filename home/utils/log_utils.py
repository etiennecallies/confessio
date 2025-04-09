from datetime import datetime


def info(message: any):
    print(f'{datetime.now()} {str(message)}')
