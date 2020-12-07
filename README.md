# speckle-py 🥧

[![Twitter Follow](https://img.shields.io/twitter/follow/SpeckleSystems?style=social)](https://twitter.com/SpeckleSystems) [![Discourse users](https://img.shields.io/discourse/users?server=https%3A%2F%2Fdiscourse.speckle.works&style=flat-square)](https://discourse.speckle.works)
[![Slack Invite](https://img.shields.io/badge/-slack-grey?style=flat-square&logo=slack)](https://speckle-works.slack.com/join/shared_invite/enQtNjY5Mzk2NTYxNTA4LTU4MWI5ZjdhMjFmMTIxZDIzOTAzMzRmMTZhY2QxMmM1ZjVmNzJmZGMzMDVlZmJjYWQxYWU0MWJkYmY3N2JjNGI) [![website](https://img.shields.io/badge/www-speckle.systems-royalblue?style=flat-square)](https://speckle.systems)

## Introduction

> ⚠ This is the start of the Python client for Speckle 2.0. It is currently quite nebulous and may be trashed and rebuilt at any moment! It is compatible with Python 3.6+ ⚠

## Developing & Debugging

To get started, create a virtual environment and pip install the requirements. 

on windows:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Overview of functionality 

The `SpeckleClient` is the entry point for interacting with the GraphQL API. You'll need to have a running server to use this.

```py
from speckle.api.client import SpeckleClient
from speckle.api.credentials import get_default_account, get_local_accounts

all_accounts = get_local_accounts() # get back a list
account = get_default_account()

client = SpeckleClient(host="localhost:3000", use_ssl=False)
# client = SpeckleClinet(host="yourserver.com") or whatever your host is

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
commits = client.commit.get_list("stream id here")

# get a specific commit
commit = client.commit.get("stream id", "commit id")

# create a commit
commit_id = client.commit.create("stream id", "object id", "this is a commit message to describe the commit")

# delete a commit
deleted = client.commit.delete("stream id", "commit id")
```

The `BaseObjectSerializer` is used for decomposing and serializing `Base` objects so they can be sent / received to the server. You can use it directly to get the id (hash) and a serializable object representation of the decomposed `Base`.

```py
detached_base = Base()
detached_base.name = "this will get detached"

base_obj = Base()
base_obj.name = "my base"
base_obj["@nested"] = detached_base

serializer = BaseObjectSerializer()
hash, obj_dict = serializer.traverse_base(base_obj)
```

If you use the `operations`, you will not need to interact with the serializer directly as this will be taken care of for you. You will just need to provide a transport to indicate where the objects should be sent / received from. At the moment, just the `MemoryTransport` is fully functional.

```py
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

received_base = client.object.get(hash)
```

This doc is not complete - there's more to see so have a dive into the code and play around! Please feel free to provide feedback, submit issues, or discuss new features ✨

## Contributing

Please make sure you read the [contribution guidelines](.github/CONTRIBUTING.md) for an overview of the best practices we try to follow.

## Community

The Speckle Community hangs out in two main places, usually:

- on [the forum](https://discourse.speckle.works)
- on [the chat](https://speckle-works.slack.com/join/shared_invite/enQtNjY5Mzk2NTYxNTA4LTU4MWI5ZjdhMjFmMTIxZDIzOTAzMzRmMTZhY2QxMmM1ZjVmNzJmZGMzMDVlZmJjYWQxYWU0MWJkYmY3N2JjNGI)

Do join and introduce yourself!

## License

Unless otherwise described, the code in this repository is licensed under the Apache-2.0 License. Please note that some modules, extensions or code herein might be otherwise licensed. This is indicated either in the root of the containing folder under a different license file, or in the respective file's header. If you have any questions, don't hesitate to get in touch with us via [email](mailto:hello@speckle.systems).
