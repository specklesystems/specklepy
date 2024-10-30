from deprecated import deprecated

from specklepy.core.api.models import FE1_DEPRECATION_VERSION
from specklepy.core.api.resources.subscription_resource import SubscriptionResource


@deprecated(
    reason="Class renamed to SubscriptionResource", version=FE1_DEPRECATION_VERSION
)
class Resource(SubscriptionResource):
    pass
