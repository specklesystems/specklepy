import os
import random
import string
import time
from pathlib import Path
from typing import List

from specklepy.api import operations
from specklepy.objects import Base
from specklepy.transports.sqlite import SQLiteTransport


class Sub(Base):
    bar: List[str]


def random_string():
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(10))


BASE_PATH = SQLiteTransport.get_base_path("Speckle")


def clean_db():
    os.remove(Path(BASE_PATH, "Objects.db"))


def one_pass(clean: bool, randomize: bool, child_count: int):
    foo = Base()
    for i in range(child_count):
        stuff = random_string() if randomize else "stuff"
        foo[f"@child_{i}"] = Sub(bar=["asdf", "bar", i, stuff])

    if clean:
        clean_db()
    transport = SQLiteTransport()
    start = time.time()
    hash = operations.send(base=foo, transports=[transport])
    send_time = time.time() - start

    receive_start = time.time()
    operations.receive(hash, transport)
    receive_time = time.time() - receive_start
    return send_time, receive_time


if __name__ == "__main__":
    sample_size = 4

    test_permutations = [
        (True, True),
        (False, False),
        (False, True),
        (True, False),
    ]
    for clean, randomize in test_permutations:
        print(f"CLEAN: {clean}, RANDOMIZE: {randomize}")
        for child_count in [10, 100, 1000, 10000]:
            print(f"\tCHILD COUNT: {child_count}")
            for _ in range(sample_size):
                send_time, receive_time = one_pass(clean, randomize, child_count)
                print(f"\t\tSend: {send_time} Receive: {receive_time}")
