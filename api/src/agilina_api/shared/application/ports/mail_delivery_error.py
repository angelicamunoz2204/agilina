class MailDeliveryError(Exception):
    """The mail server did not accept the message. It never carries credentials."""
