import csv
from io import StringIO


def read_csv_in_chunks(file, chunk_size=1000):
    """
    Generator that yields rows in chunks
    """
    decoded = file.file.read().decode("utf-8")
    reader = csv.DictReader(StringIO(decoded))

    chunk = []

    for row_number, row in enumerate(reader, start=1):
        chunk.append((row_number, row))

        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []

    if chunk:
        yield chunk