# Introduction

Welcome to the Specklepy Developer Docs - a single source of documentation on everything Specklepy! If you're looking for info on how to use Speckle, check our [user guide](https://speckle.guide/).

### Code Repository
The Python SDK can be found in our [repository](//github.com/specklesystems/specklepy), its readme contains instructions on how to build it.

### Installation
You can install it using pip
```
pip install specklepy
```

### Key Components

SpecklePy has three main parts:

1. a `SpeckleClient` which allows you to interact with the server API
2. `operations` and `transports` for sending and receiving large objects
3. a `Base` object and accompaniying serializer for creating and customizing your own Speckle objects


### Local Data Paths

It may be helpful to know where the local accounts and object cache dbs are stored. Depending on on your OS, you can find the dbs at:

- Windows: `APPDATA` or `<USER>\AppData\Roaming\Speckle`
- Linux: `$XDG_DATA_HOME` or by default `~/.local/share/Speckle`
- Mac: `~/.config/Speckle`
