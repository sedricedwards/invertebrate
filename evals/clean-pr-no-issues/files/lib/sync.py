from lib.batching import chunk

BATCH_SIZE = 50

def upload_all(records, send):
    for batch in chunk(records, BATCH_SIZE):
        send(batch)
