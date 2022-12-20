import random
import string
from typing import List

from specklepy.api import operations
from specklepy.api.wrapper import StreamWrapper
from specklepy.objects import Base


class Sub(Base):
    bar: List[str]


def random_string():
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(10))


def create_object(child_count: int) -> Base:
    foo = Base()
    for i in range(child_count):
        stuff = random_string()
        foo[f"@child_{i}"] = Sub(bar=["asdf", "bar", i, stuff])
    return foo


if __name__ == "__main__":
    stream_url = "http://hyperion:3000/streams/2372b54c35"

    child_count = 10
    foo = create_object(child_count)

    wrapper = StreamWrapper(stream_url)
    transport = wrapper.get_transport()

    hash = operations.send(base=foo, transports=[transport], use_default_cache=False)

    rec = operations.receive(hash, transport)
    print(rec)
