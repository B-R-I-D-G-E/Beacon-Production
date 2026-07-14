from pymongo.mongo_client import MongoClient
from beacon.connections.mongo import conf as mongo_conf


def get_case_level_data_collection():
    """Standalone Mongo connection for the watcher process, independent from
    the main aiohttp app. Reuses the same connection settings (host, auth,
    db name) as beacon/connections/mongo/conf.py, but does not import
    beacon.connections.mongo itself since that module pulls in aiohttp.web
    and the main app's config/validation on import.
    """
    if mongo_conf.database_cluster:
        uri = "mongodb+srv://{}/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000".format(
            mongo_conf.database_host
        )
    else:
        uri = "mongodb://{}:{}/{}?authSource={}".format(
            mongo_conf.database_host,
            mongo_conf.database_port,
            mongo_conf.database_name,
            mongo_conf.database_auth_source,
        )

    if mongo_conf.database_certificate != '' and mongo_conf.database_cafile != '':
        uri += '&tls=true&tlsCertificateKeyFile={}&tlsCAFile={}'.format(
            mongo_conf.database_certificate, mongo_conf.database_cafile
        )

    client = MongoClient(uri, username=mongo_conf.database_user, password=mongo_conf.database_password)
    return client[mongo_conf.database_name].caseLevelData
