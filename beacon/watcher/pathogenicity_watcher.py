import logging
import time
from pymongo.errors import PyMongoError

from beacon.watcher import conf
from beacon.watcher.mongo_client import get_case_level_data_collection
from beacon.watcher.network_client import fetch_remote_classifications
from beacon.watcher.mailer import send_discrepancy_alert

logging.basicConfig(format='%(levelname)s - %(asctime)s - %(message)s', level=logging.INFO)
LOG = logging.getLogger("beacon.watcher")

# Watch only updates. fullDocument is fetched via "updateLookup" below since
# we need the current clinicalInterpretations to read the new value.
CHANGE_STREAM_PIPELINE = [
    {"$match": {"operationType": "update"}},
]


def _touched_clinical_relevance(updated_fields: dict) -> bool:
    """True if the update touched clinicalInterpretations (or a
    clinicalRelevance field inside it), as opposed to some unrelated field
    on the same document. Covers both a whole-array replace (field path is
    just "clinicalInterpretations") and a targeted element update (field
    path like "clinicalInterpretations.0.clinicalRelevance")."""
    return any(field.startswith("clinicalInterpretations") for field in updated_fields)


def _variant_id_from_document(document: dict) -> str:
    """caseLevelData documents reference the variant via variantInternalId
    (mirrors the identifier used on genomicVariations); fall back to the
    Mongo _id if that field isn't present."""
    return document.get("variantInternalId") or document.get("id") or str(document.get("_id"))


def _local_classifications(document: dict) -> list:
    classifications = []
    for interpretation in document.get("clinicalInterpretations", []) or []:
        relevance = interpretation.get("clinicalRelevance")
        if relevance:
            classifications.append(relevance)
    return classifications


def handle_change_event(change: dict) -> None:
    updated_fields = change.get("updateDescription", {}).get("updatedFields", {})
    if not _touched_clinical_relevance(updated_fields):
        return

    document = change.get("fullDocument")
    if not document:
        LOG.warning("[watcher] Update touched clinicalRelevance but no fullDocument was returned, skipping")
        return

    local_classifications = _local_classifications(document)
    if not local_classifications:
        return
    local_classification = local_classifications[0]
    variant_id = _variant_id_from_document(document)

    LOG.info(
        "[watcher] Detected pathogenicity change for variant {} on {}: now {!r}".format(
            variant_id, conf.node_name, local_classification
        )
    )

    try:
        remote_classifications = fetch_remote_classifications(variant_id)
    except Exception as exc:
        LOG.error("[watcher] Failed to query Beacon Network for variant {}: {}".format(variant_id, exc))
        return

    mismatching = {
        node: classification
        for node, classification in remote_classifications.items()
        if classification != local_classification
    }

    if mismatching:
        LOG.warning(
            "[watcher] Classification mismatch for variant {}: local={!r} remote={}".format(
                variant_id, local_classification, mismatching
            )
        )
        send_discrepancy_alert(variant_id, local_classification, remote_classifications)
    else:
        LOG.info("[watcher] Variant {} classification matches across the network".format(variant_id))


def watch_forever() -> None:
    """Keeps a Mongo change stream on caseLevelData open indefinitely,
    resuming automatically after transient errors. Requires the local
    MongoDB deployment to be a Replica Set (even a single-node one) since
    change streams are backed by the oplog."""
    collection = get_case_level_data_collection()

    while True:
        try:
            LOG.info("[watcher] Opening change stream on caseLevelData ({})".format(conf.node_name))
            with collection.watch(
                pipeline=CHANGE_STREAM_PIPELINE,
                full_document="updateLookup",
            ) as stream:
                for change in stream:
                    handle_change_event(change)
        except PyMongoError as exc:
            LOG.error("[watcher] Change stream error, resuming in {}s: {}".format(conf.resume_backoff_seconds, exc))
            time.sleep(conf.resume_backoff_seconds)
        except Exception as exc:
            LOG.error("[watcher] Unexpected error, resuming in {}s: {}".format(conf.resume_backoff_seconds, exc))
            time.sleep(conf.resume_backoff_seconds)
