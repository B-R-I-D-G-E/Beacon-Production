import logging
from beacon.watcher import conf

LOG = logging.getLogger("beacon.watcher")


def send_discrepancy_alert(variant_id: str, local_classification: str, remote_classifications: dict) -> None:
    """Notify operators that a variant's pathogenicity classification now
    disagrees between this node and one or more other nodes in the network.

    remote_classifications maps beacon/node identifier -> classification
    string, as reported back by the central Beacon Network node.
    """
    subject = "[{}] Pathogenicity classification mismatch for variant {}".format(conf.node_name, variant_id)
    body_lines = [
        "Variant: {}".format(variant_id),
        "Classification on this node ({}): {}".format(conf.node_name, local_classification),
        "",
        "Classifications reported by the Beacon Network for the same variant:",
    ]
    for node, classification in remote_classifications.items():
        flag = "  <-- DIFFERS" if classification != local_classification else ""
        body_lines.append("  - {}: {}{}".format(node, classification, flag))
    body = "\n".join(body_lines)

    # TODO: real SMTP credentials are not configured yet. Once conf.smtp_host
    # / conf.email_from / conf.email_to_alerts are set (see watcher.env),
    # replace this stub with an actual smtplib.SMTP send, e.g.:
    #
    # import smtplib
    # from email.mime.text import MIMEText
    # msg = MIMEText(body)
    # msg["Subject"] = subject
    # msg["From"] = conf.email_from
    # msg["To"] = ", ".join(conf.email_to_alerts)
    # with smtplib.SMTP(conf.smtp_host, conf.smtp_port) as server:
    #     if conf.smtp_use_tls:
    #         server.starttls()
    #     if conf.smtp_user:
    #         server.login(conf.smtp_user, conf.smtp_password)
    #     server.sendmail(conf.email_from, conf.email_to_alerts, msg.as_string())
    if not conf.smtp_host or not conf.email_to_alerts:
        LOG.warning(
            "[watcher] Email alert NOT sent (SMTP not configured). Subject={!r} Body={!r}".format(subject, body)
        )
        return

    LOG.warning(
        "[watcher] SMTP is configured but sending is not implemented yet. Subject={!r} Body={!r}".format(
            subject, body
        )
    )
