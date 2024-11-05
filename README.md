<h1 align="center">
  <img src="https://user-images.githubusercontent.com/2679513/131189167-18ea5fe1-c578-47f6-9785-3748178e4312.png" width="150px"/><br/>
  Speckle | specklepy 🐍
</h1>

<p align="center"><a href="https://twitter.com/SpeckleSystems"><img src="https://img.shields.io/twitter/follow/SpeckleSystems?style=social" alt="Twitter Follow"></a> <a href="https://speckle.community"><img src="https://img.shields.io/discourse/users?server=https%3A%2F%2Fspeckle.community&amp;style=flat-square&amp;logo=discourse&amp;logoColor=white" alt="Community forum users"></a> <a href="https://speckle.systems"><img src="https://img.shields.io/badge/https://-speckle.systems-royalblue?style=flat-square" alt="website"></a> <a href="https://speckle.guide/dev/"><img src="https://img.shields.io/badge/docs-speckle.guide-orange?style=flat-square&amp;logo=read-the-docs&amp;logoColor=white" alt="docs"></a></p>

> Speckle is the first AEC data hub that connects with your favorite AEC tools. Speckle exists to overcome the challenges of working in a fragmented industry where communication, creative workflows, and the exchange of data are often hindered by siloed software and processes. It is here to make the industry better.

<h3 align="center">
    The Python SDK
</h3>

<p align="center"><a href="https://codecov.io/gh/specklesystems/specklepy"><img src="https://codecov.io/gh/specklesystems/specklepy/branch/main/graph/badge.svg?token=8KQFL5N0YF" alt="Codecov"></a></p>

# Repo structure

## Usage

Send and receive data from a Speckle Server with `operations`, interact with the Speckle API with the `SpeckleClient`, create and extend your own custom Speckle Objects with `Base`, and more!

Head to the [**📚 specklepy docs**](https://speckle.guide/dev/python.html) for more information and usage examples.

## Developing & Debugging

### Installation

This project uses python-poetry for dependency management, make sure you follow the official [docs](https://python-poetry.org/docs/#installation) to get poetry.

To bootstrap the project environment run `$ poetry install`. This will create a new virtual-env for the project and install both the package and dev dependencies.

If this is your first time using poetry and you're used to creating your venvs within the project directory, run `poetry config virtualenvs.in-project true` to configure poetry to do the same.

To execute any python script run `$ poetry run python my_script.py`

> Alternatively you may roll your own virtual-env with either venv, virtualenv, pyenv-virtualenv etc. Poetry will play along an recognize if it is invoked from inside a virtual environment.

### Style guide

All our repo  wide styling linting and other rules are checked and enforced by `pre-commit`, which is included in the dev dependencies.
It is recommended to set up `pre-commit` after installing the dependencies by running `$ pre-commit install`.
Commiting code that doesn't adhere to the given rules, will fail the checks in our CI system.

### Local Data Paths

It may be helpful to know where the local accounts and object cache dbs are stored. Depending on on your OS, you can find the dbs at:
- Windows: `APPDATA` or `<USER>\AppData\Roaming\Speckle`
- Linux: `$XDG_DATA_HOME` or by default `~/.local/share/Speckle`
- Mac: `~/.config/Speckle`

## Contributing

Please make sure you read the [contribution guidelines](.github/CONTRIBUTING.md) and [code of conduct](.github/CODE_OF_CONDUCT.md) for an overview of the practices we try to follow.

## Community

The Speckle Community hangs out on [the forum](https://discourse.speckle.works), do join and introduce yourself & feel free to ask us questions!

## Security

For any security vulnerabilities or concerns, please contact us directly at security[at]speckle.systems.

## License

Unless otherwise described, the code in this repository is licensed under the Apache-2.0 License. Please note that some modules, extensions or code herein might be otherwise licensed. This is indicated either in the root of the containing folder under a different license file, or in the respective file's header. If you have any questions, don't hesitate to get in touch with us via [email](mailto:hello@speckle.systems).
