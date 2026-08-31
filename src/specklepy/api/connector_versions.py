from datetime import datetime
from typing import List

import httpx
from pydantic import AliasGenerator, BaseModel, ConfigDict, HttpUrl
from pydantic.alias_generators import to_pascal


class ConnectorFeedBaseModel(BaseModel):
    """
    Parent class for all Connector Feed Object Model classes
    Sets-up a pydantic config to serialize properties using a pascal case alias
    """

    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=to_pascal,
        ),
        populate_by_name=True,
    )


class ConnectorVersion(ConnectorFeedBaseModel):
    number: str
    url: HttpUrl
    os: int  # this is an enum, it's properly defined in the old v2 SDK (used by Speckle.Manager.Feed)  # noqa: E501
    architecture: int  # These are enums, they are properly defined in the old v2 SDK (used by Speckle.Manager.Feed) # noqa: E501
    date: datetime
    prerelease: bool


class ConnectorVersions(ConnectorFeedBaseModel):
    versions: List[ConnectorVersion]


def get_latest_version(host_app_slug: str, allow_pre_release: bool) -> ConnectorVersion:
    """
    Fetches the JSON feed for the given connector slug and
    Returns the latest version by date - Note, it does not consider semvers!

    Arguments:
        host_app_slug {str} -- the host app slug to query for
        allow_pre_release {bool} -- if false, only stable releases will be considered
    Raises:
        HTTPStatusError: if http request failed
        ValidationError: response was not valid json
        ValueError: The feed contained no connector versions
    """
    connector_versions = get_connector_versions(host_app_slug).versions
    filtered_versions = [
        v for v in connector_versions if allow_pre_release or not v.prerelease
    ]

    return max(filtered_versions, key=lambda x: x.date)


def get_connector_versions(host_app_slug: str) -> ConnectorVersions:
    """
    Fetches the JSON feed for the given slug (v3 feeds only)
    Raises:
        HTTPStatusError: if http request failed
        ValidationError: response was not valid json
    """
    url = f"https://releases.speckle.dev/manager2/feeds/{host_app_slug.lower()}-v3.json"

    res = httpx.get(url).raise_for_status()

    feed_data = ConnectorVersions.model_validate_json(res.text)

    return feed_data
