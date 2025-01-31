# mapigator

# Google API

## Nearby search
Nearby search (Find the doc [here](https://developers.google.com/maps/documentation/places/web-service/search-nearby?hl=fr))
currently returns a maximum if `60`results. If there are more results to fetch
the api provides a `next_page_token` to use to complete the request.
This token can be used to return up to `20` additional results.

## Possible types
All available types to pass are available in the documentation [here](https://developers.google.com/maps/documentation/places/web-service/supported_types?hl=fr). 
**Please note, mapigator currently performs no validation on the type provided.**