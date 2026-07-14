import requests
from beacon.watcher import conf


def fetch_remote_classifications(variant_id: str) -> dict:
    """Ask the central Beacon Network for the pathogenicity classification
    that every member node reports for a given variant.

    Queries the standard GA4GH g_variants endpoint exposed by the network
    aggregator (beacon-network-docker / WildFly), filtering by the variant's
    internal identifier, and reads back the clinicalRelevance value found
    under each result's caseLevelData.clinicalInterpretations.

    Returns a dict mapping "<beaconId>/<datasetId>" -> classification string,
    for every node that returned a match. Nodes that don't have the variant
    are simply absent from the result.
    """
    url = "{}/g_variants".format(conf.beacon_network_url)
    params = {"variantInternalId": variant_id}

    response = requests.get(url, params=params, timeout=conf.beacon_network_timeout_seconds)
    response.raise_for_status()
    payload = response.json()

    classifications = {}
    for result_set in payload.get("response", {}).get("resultSets", []):
        beacon_id = result_set.get("beaconId") or result_set.get("id") or "unknown-beacon"
        for result in result_set.get("results", []):
            classification = _extract_classification(result)
            if classification is None:
                continue
            dataset_id = result.get("datasetId", "unknown-dataset")
            classifications["{}/{}".format(beacon_id, dataset_id)] = classification

    return classifications


def _extract_classification(variant_result: dict):
    for case_level in variant_result.get("caseLevelData", []) or []:
        for interpretation in case_level.get("clinicalInterpretations", []) or []:
            classification = interpretation.get("clinicalRelevance")
            if classification:
                return classification
    return None
