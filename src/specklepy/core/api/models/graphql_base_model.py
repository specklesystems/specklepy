from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class GraphQLBaseModel(BaseModel):
    """
    Parent class for all GraphQL Object Model classes
    Sets-up a pydantic config to serialize properties using a camel case alias
    """

    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            serialization_alias=to_camel,
            validation_alias=to_camel,
        ),
        populate_by_name=True,
    )
