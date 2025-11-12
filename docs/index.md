# specklepy API Reference

> The Python SDK for Speckle - Build powerful AEC data workflows

**specklepy** is the Python SDK for Speckle, enabling you to interact with Speckle Server, send and receive geometry, and build custom integrations for the AEC industry.

## What is specklepy?

specklepy is a comprehensive Python library that provides:

* **Object-based data exchange** - Send and receive geometry and BIM data without files
* **GraphQL API client** - Full access to Speckle Server's API
* **Extensible object model** - Create custom objects that inherit from `Base`
* **Multiple transport options** - Store data locally (SQLite), in-memory, or on Speckle Server
* **Geometry support** - Rich geometric primitives (Point, Line, Mesh, etc.)

## Speckle Automate

Speckle Automate is a fully fledged CI/CD platform designed to run custom code on Speckle models whenever a new version is available.

As a software developer, you can develop Functions that others in your team consume in Automations. From creating reports to running code compliance checks to wind simulations, there is no limit to what you can do with Automate.

## Installation

Install specklepy using pip:

```bash
pip install specklepy
```

## Quick Example

```python
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account
from specklepy.objects.geometry import Point

# Authenticate
client = SpeckleClient(host="https://app.speckle.systems")
account = get_default_account()
client.authenticate_with_account(account)

# Create geometry
point = Point(x=10, y=20, z=5)
```

## Getting Help

- **Community Forum**: [speckle.community](https://speckle.community/c/help/developers)
- **GitHub Issues**: [github.com/specklesystems/specklepy](https://github.com/specklesystems/specklepy/issues)
