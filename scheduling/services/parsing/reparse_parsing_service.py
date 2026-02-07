from scheduling.models import Parsing
from scheduling.tasks import worker_reparse_parsing


def reparse_parsing(parsing: Parsing):
    worker_reparse_parsing(str(parsing.uuid))
