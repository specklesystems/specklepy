from devtools import debug

from specklepy.api import operations
from specklepy.api.wrapper import StreamWrapper

if __name__ == "__main__":
    stream_url = "https://latest.speckle.dev/streams/7d051a6449"
    wrapper = StreamWrapper(stream_url)

    transport = wrapper.get_transport()

    rec = operations.receive("98396753f8bf7fe1cb60c5193e9f9d86", transport)

    # hash = operations.send(base=foo, transports=[transport], use_default_cache=False)
    debug(rec)
