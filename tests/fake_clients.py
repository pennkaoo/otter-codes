"""Fake clients to use for testing."""


class twilio_fake():
    """Fake twilio client."""

    def __init__(self):
        """Create the fake twilio client."""
        self.to = []
        self.messages = []

    def send_message(self, to, from_, body):
        """Send a fake message.

        Args:
            to: The number that will recieve the message.
            from_: The number that will send the message.
            body: Text message body.
        """
        self.to.append(to)
        self.messages.append(body)


class price_tracker_fake():
    """Fake Price Tracker client."""

    def __init__(self, amount):
        """Build fake price tracker client."""
        self.amount = float(amount)

    def get_spot_price(self, asset):
        """Get the current price of the asset.

        Args:
            asset: The asset in question.
        """
        return self.amount
