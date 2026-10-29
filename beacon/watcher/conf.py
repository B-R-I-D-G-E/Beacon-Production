from dotenv import load_dotenv
import os

watcher_conf = "beacon/watcher/watcher.env"
load_dotenv(watcher_conf, override=True)

# Local node identity, used in the alert email and in the log lines so an
# operator monitoring several nodes can tell which one raised the alarm.
node_name = os.getenv('NODE_NAME', 'local-node')

# Beacon Network (the central/aggregator node) GA4GH endpoint, e.g.
# http://nginx/beacon-network/v2.0.0 as exposed by beacon-network-docker.
beacon_network_url = os.getenv('BEACON_NETWORK_URL', 'http://localhost:8080/beacon-network/v2.0.0').rstrip('/')
beacon_network_timeout_seconds = float(os.getenv('BEACON_NETWORK_TIMEOUT_SECONDS', '30'))

# SMTP / alert email configuration. send_email() only logs a warning until
# these are filled in with real credentials.
smtp_host = os.getenv('SMTP_HOST', '')
smtp_port = int(os.getenv('SMTP_PORT', '587'))
smtp_user = os.getenv('SMTP_USER', '')
smtp_password = os.getenv('SMTP_PASSWORD', '')
smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
email_from = os.getenv('EMAIL_FROM', '')
email_to_alerts = [addr.strip() for addr in os.getenv('EMAIL_TO_ALERTS', '').split(',') if addr.strip()]

# Poll interval (seconds) used only to resume a change stream after a
# transient error; the stream itself is push-based, not polling.
resume_backoff_seconds = float(os.getenv('RESUME_BACKOFF_SECONDS', '5'))
