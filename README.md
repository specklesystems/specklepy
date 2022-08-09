<h1 align="center">
  <img src="https://user-images.githubusercontent.com/2679513/131189167-18ea5fe1-c578-47f6-9785-3748178e4312.png" width="150px"/><br/>
  Speckle | specklepy 🐍
</h1>
<h3 align="center">
    The Python SDK
</h3>
<p align="center"><b>Speckle</b> is the data infrastructure for the AEC industry.</p><br/>

<p align="center"><a href="https://twitter.com/SpeckleSystems"><img src="https://img.shields.io/twitter/follow/SpeckleSystems?style=social" alt="Twitter Follow"></a> <a href="https://speckle.community"><img src="https://img.shields.io/discourse/users?server=https%3A%2F%2Fspeckle.community&amp;style=flat-square&amp;logo=discourse&amp;logoColor=white" alt="Community forum users"></a> <a href="https://speckle.systems"><img src="https://img.shields.io/badge/https://-speckle.systems-royalblue?style=flat-square" alt="website"></a> <a href="https://speckle.guide/dev/"><img src="https://img.shields.io/badge/docs-speckle.guide-orange?style=flat-square&amp;logo=read-the-docs&amp;logoColor=white" alt="docs"></a></p>
<p align="center"><a href="https://github.com/specklesystems/specklepy/"><img src="https://circleci.com/gh/specklesystems/specklepy.svg?style=svg&amp;circle-token=76eabd350ea243575cbb258b746ed3f471f7ac29" alt="Speckle-Next"></a><a href="https://codecov.io/gh/specklesystems/specklepy">
  <img src="https://codecov.io/gh/specklesystems/specklepy/branch/main/graph/badge.svg?token=8KQFL5N0YF"/>
</a> </p>

# About Speckle

What is Speckle? Check our ![YouTube Video Views](https://img.shields.io/youtube/views/B9humiSpHzM?label=Speckle%20in%201%20minute%20video&style=social)

### Features

- **Object-based:** say goodbye to files! Speckle is the first object based platform for the AEC industry
- **Version control:** Speckle is the Git & Hub for geometry and BIM data
- **Collaboration:** share your designs collaborate with others
- **3D Viewer:** see your CAD and BIM models online, share and embed them anywhere
- **Interoperability:** get your CAD and BIM models into other software without exporting or importing
- **Real time:** get real time updates and notifications and changes
- **GraphQL API:** get what you need anywhere you want it
- **Webhooks:** the base for a automation and next-gen pipelines
- **Built for developers:** we are building Speckle with developers in mind and got tools for every stack
- **Built for the AEC industry:** Speckle connectors are plugins for the most common software used in the industry such as Revit, Rhino, Grasshopper, AutoCAD, Civil 3D, Excel, Unreal Engine, Unity, QGIS, Blender and more!

### Try Speckle now!

Give Speckle a try in no time by:

- [![speckle XYZ](https://img.shields.io/badge/https://-speckle.xyz-0069ff?style=flat-square&logo=hackthebox&logoColor=white)](https://speckle.xyz) ⇒ creating an account at our public server
- [![create a droplet](https://img.shields.io/badge/Create%20a%20Droplet-0069ff?style=flat-square&logo=digitalocean&logoColor=white)](https://marketplace.digitalocean.com/apps/speckle-server?refcode=947a2b5d7dc1) ⇒ deploying an instance in 1 click 

### Resources

- [![Community forum users](https://img.shields.io/badge/community-forum-green?style=for-the-badge&logo=discourse&logoColor=white)](https://speckle.community) for help, feature requests or just to hang with other speckle enthusiasts, check out our community forum!
- [![website](https://img.shields.io/badge/tutorials-speckle.systems-royalblue?style=for-the-badge&logo=youtube)](https://speckle.systems) our tutorials portal is full of resources to get you started using Speckle
- [![docs](https://img.shields.io/badge/docs-speckle.guide-orange?style=for-the-badge&logo=read-the-docs&logoColor=white)](https://speckle.guide/dev/) reference on almost any end-user and developer functionality


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
