from app.connectors.base import BaseConnector
from app.connectors.tradefair import TradefairConnector
from app.connectors.website_discovery import WebsiteDiscoveryConnector
from app.connectors.wikidata import WikidataConnector
from app.connectors.yellowpages import YellowPagesConnector


def get_default_connectors() -> list[BaseConnector]:
    return [
        WikidataConnector(),
        YellowPagesConnector(),
        TradefairConnector(),
        WebsiteDiscoveryConnector(),
    ]
