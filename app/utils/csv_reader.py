import csv
import io


def read_csv_in_chunks(file, chunk_size=1000):
    """
    Stream CSV file and yield chunks of rows
    """

    # Reset pointer just in case
    file.file.seek(0)

    # csv can read text, so decode line-by-line
    def line_generator():
        for line in file.file:
            yield line.decode("utf-8") # This way, we can ensure that only one row is in the memory (plus the chunk buffer).

    reader = csv.DictReader(line_generator()) # DictReader is streaming friendly

    chunk = []

    for row_number, row in enumerate(reader, start=1):
        chunk.append((row_number, row))

        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []

    if chunk:
        yield chunk