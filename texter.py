"""Texting Service."""
from twilio.rest import Client as TwilioClient
import twilio
from price_tracker import PriceTracker
from assets import assets


class Texter(object):
    """Texting Object."""

    def __init__(self):
        """Object initializer."""
        self.price_tracker = None
        self.send_message = None

        self.coins = [i[0] for i in assets]

    def set_clients(self, price_tracker=None, send_message=None):
        """Set Clients. Used for unit testing.

        Args:
            price_tracker: The price tracking client.
            send_message: The function to send the text message.
        """
        self.price_tracker = price_tracker
        self.send_message = send_message

    def check_alerts(self, db):
        """Check alerts for all types of assets.

        Args:
            db: The db cursor object.
        """
        if self.price_tracker is None:
            self.price_tracker = PriceTracker()
        if self.send_message is None:
            from api_keys import twilio_sid, twilio_auth
            twilio_client = TwilioClient(twilio_sid, twilio_auth)
            self.send_message = twilio_client.api.account.messages.create

        for i in range(len(self.coins)):
            self.check_alerts_for_coin(self.coins[i], db)

    def check_alerts_for_coin(self, coin, db):
        """Check for alerts.

        Args:
            coin: The asset to check against.
                TODO(Chase): Change name.
            db: The database curson object.
        """
        # TODO(Chase): Move Alerts to it's own file.
        from app import Alert
        currency_code = 'USD'  # can also use EUR, CAD, etc.
        # Make the request
        # price = coinbase_client.get_spot_price(currency=currency_code)
        price = self.price_tracker.get_spot_price(
            asset=coin)

        # Get all of the prices that are less than the current amount
        greater_than_query = Alert.query.filter(Alert.symbol == coin,
                                                Alert.price < price,
                                                Alert.above != 0)
        self.text_greater_than(greater_than_query.all(), price)
        greater_than_query.delete(False)

        less_than_query = Alert.query.filter(Alert.symbol == coin,
                                             Alert.price > price,
                                             Alert.above == 0)
        self.text_less_than(less_than_query.all(), price)
        less_than_query.delete(False)

        # TODO(Chase): This will cause race condition.
        db.session.commit()

    def text_greater_than(self, alerts, price):
        """Send text message for above triggers.

        Args:
            alerts: The alerts to send. Should be type Alert.
            price: The current asset price.
        """
        for alert in alerts:
            # Some logging
            print("Sending text to %s" % alert.phone_number)
            try:
                # Send the text
                self.send_message(
                    to=alert.phone_number,
                    from_="+15072003597",
                    body=(
                        "%s price is above your trigger of %s. "
                        "Current price is %s"
                        % (alert.symbol, alert.price, price)))
            except twilio.base.exceptions.TwilioRestException:
                # Catch errors.
                print("Invalid number:", alert.phone_number)

    def text_less_than(self, alerts, price):
        """Send text message for above triggers.

        Args:
            alerts: The alerts to send. Should be type Alert.
            price: The current asset price.
        """
        for alert in alerts:
            # Some logging
            print("Sending text to %s" % alert.phone_number)
            try:
                # Send the text
                self.send_message(
                    to=alert.phone_number,
                    from_="+15072003597",
                    body=(
                        "%s price is below your trigger of %s. "
                        "Current price is %s"
                        % (alert.symbol, alert.price, price)))
            except twilio.base.exceptions.TwilioRestException:
                print("Invalid number:", alert.phone_number)
