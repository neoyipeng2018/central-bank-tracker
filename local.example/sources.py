"""Example custom data source.

Copy this file to ``local/sources.py`` to add your own news/data fetcher.
The ``@data_source`` decorator automatically registers the function so it
runs alongside the built-in sources during ``fetch_data.py``.
"""

# from fomc_tracker.news_fetcher import data_source
# from fomc_tracker.participants import Participant
#
#
# @data_source("my_internal_api")
# def fetch_internal(participant: Participant, **kwargs) -> list[dict]:
#     """Fetch articles from an internal company API."""
#     # import requests
#     # resp = requests.get(
#     #     "https://internal.example.com/api/articles",
#     #     params={"speaker": participant.name},
#     # )
#     # resp.raise_for_status()
#     # return [
#     #     {
#     #         "source": "my_internal_api",
#     #         "title": a["headline"],
#     #         "body": a["text"],
#     #         "url": a["link"],
#     #         "date": a["published"],
#     #     }
#     #     for a in resp.json()["articles"]
#     # ]
#     return []
