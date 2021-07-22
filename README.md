# speckle-py 🥧

[![Twitter Follow](https://img.shields.io/twitter/follow/SpeckleSystems?style=social)](https://twitter.com/SpeckleSystems) [![Community forum users](https://img.shields.io/discourse/users?server=https%3A%2F%2Fdiscourse.speckle.works&style=flat-square&logo=discourse&logoColor=white)](https://discourse.speckle.works) [![website](https://img.shields.io/badge/https://-speckle.systems-royalblue?style=flat-square)](https://speckle.systems) [![docs](https://img.shields.io/badge/docs-speckle.guide-orange?style=flat-square&logo=read-the-docs&logoColor=white)](https://speckle.guide/dev/)

## Introduction

> ⚠ This is the start of the Python client for Speckle 2.0. It is currently quite nebulous and may be trashed and rebuilt at any moment! It is compatible with Python 3.6+ ⚠
> 

## Documentation

Comprehensive developer and user documentation can be found in our:

#### 📚 [Speckle Docs website](https://speckle.guide/dev/)

## Developing & Debugging

### Installation

This project uses python-poetry for dependency management, make sure you follow the official [docs](https://python-poetry.org/docs/#installation) to get poetry.

To bootstrap the project environment run `$ poetry install`. This will create a new virtual-env for the project and install both the package and dev dependencies.

If this is your first time using poetry and you're used to creating your venvs within the project directory, run `poetry config virtualenvs.in-project true` to configure poetry to do the same.

To execute any python script run `$ poetry run python my_script.py`

> Alternatively you may roll your own virtual-env with either venv, virtualenv, pyenv-virtualenv etc. Poetry will play along an recognize if it is invoked from inside a virtual environment.

### Local Data Paths

It may be helpful to know where the local accounts and object cache dbs are stored. Depending on on your OS, you can find the dbs at:
- Windows: `APPDATA` or `<USER>\AppData\Roaming\Speckle`
- Linux: `$XDG_DATA_HOME` or by default `~/.local/share/Speckle`
- Mac: `~/.config/Speckle`

## Overview of functionality 

The `SpeckleClient` is the entry point for interacting with the GraphQL API. You'll need to have a running server to use this.

```py
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account, get_local_accounts

all_accounts = get_local_accounts() # get back a list
account = get_default_account()

client = SpeckleClient(host="speckle.xyz")
# client = SpeckleClient(host="yourserver.com") or whatever your host is

client.authenticate(account.token)
```

Interacting with streams is meant to be intuitive and evocative of PySpeckle 1.0

```py
# get your streams
stream_list = client.stream.list()

# search your streams
results = client.user.search("mech")

# create a stream
new_stream_id = client.stream.create(name="a shiny new stream")

# get a stream
new_stream = client.stream.get(id=new_stream_id)
```

New in 2.0: commits! Here are some basic commit interactions.

```py
# get list of commits
commits = client.commit.list("stream id")

# get a specific commit
commit = client.commit.get("stream id", "commit id")

# create a commit
commit_id = client.commit.create("stream id", "object id", "this is a commit message to describe the commit")

# delete a commit
deleted = client.commit.delete("stream id", "commit id")
```

The `BaseObjectSerializer` is used for decomposing and serializing `Base` objects so they can be sent / received to the server. You can use it directly to get the id (hash) and a serializable object representation of the decomposed `Base`. You can learn more about the Speckle `Base` object [here](https://discourse.speckle.works/t/core-2-0-the-base-object/782) and the decomposition API [here](https://discourse.speckle.works/t/core-2-0-decomposition-api/911).

```py
from specklepy.objects.base import Base
from specklepy.serialization.base_object_serializer import BaseObjectSerializer

detached_base = Base()
detached_base.name = "this will get detached"

base_obj = Base()
base_obj.name = "my base"
base_obj["@nested"] = detached_base

serializer = BaseObjectSerializer()
hash, obj_dict = serializer.traverse_base(base_obj)
```

If you use the `operations`, you will not need to interact with the serializer directly as this will be taken care of for you. You will just need to provide a transport to indicate where the objects should be sent / received from. At the moment, just the `MemoryTransport` and the `ServerTransport` are fully functional at the moment. If you'd like to learn more about Transports in Speckle 2.0, have a look [here](https://discourse.speckle.works/t/core-2-0-transports/919).

```py
from specklepy.transports.memory import MemoryTransport
from specklepy.api import operations

transport = MemoryTransport()

# this serialises the object and sends it to the transport
hash = operations.send(base=base_obj, transports=[transport])

# if the object had detached objects, you can see these as well
saved_objects = transport.objects # a dict with the obj hash as the key

# this receives and object from the given transport, deserialises it, and recomposes it into a base object
received_base = operations.receive(obj_id=hash, remote_transport=transport)
```

You can also use the GraphQL API to send and receive objects.

```py
# create a test base object
test_base = Base()
test_base.testing = "a test base obj"

# run it through the serialiser
s = BaseObjectSerializer()
hash, obj = s.traverse_base(test_base)

# send it to the server
objCreate = client.object.create(stream_id="stream id", objects=[obj])

received_base = client.object.get("stream id", hash)
```

This doc is not complete - there's more to see so have a dive into the code and play around! Please feel free to provide feedback, submit issues, or discuss new features ✨

## Contributing

Please make sure you read the [contribution guidelines](.github/CONTRIBUTING.md) for an overview of the best practices we try to follow.

## Community

The Speckle Community hangs out on [the forum](https://discourse.speckle.works), do join and introduce yourself & feel free to ask us questions!

## Security

For any security vulnerabilities or concerns, please contact us directly at security[at]speckle.systems. 

## License

Unless otherwise described, the code in this repository is licensed under the Apache-2.0 License. Please note that some modules, extensions or code herein might be otherwise licensed. This is indicated either in the root of the containing folder under a different license file, or in the respective file's header. If you have any questions, don't hesitate to get in touch with us via [email](mailto:hello@speckle.systems).
