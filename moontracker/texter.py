"""Texting Service."""
from twilio.rest import Client as TwilioClient
import twilio
from moontracker.price_tracker import PriceTracker
from moontracker.assets import supported_assets
from moontracker.times import supported_times, supported_durations
from moontracker.extensions import db
from moontracker.models import Alert, LastPrice
from datetime import datetime


class Texter(object):
    """Texting Object."""

    def __init__(self):
        """Object initializer."""
        self.price_tracker = None
        self.send_message = None

    def set_clients(self, price_tracker=None, send_message=None):
        """Set Clients. Used for unit testing.

        Args:
            price_tracker: The price tracking client.
            send_message: The function to send the text message.
        """
        self.price_tracker = price_tracker
        self.send_message = send_message

    def check_alerts(self):
        """Check alerts for all types of assets."""
        self.check_date()

        if self.price_tracker is None:
            self.price_tracker = PriceTracker()
        if self.send_message is None:
            from moontracker.api_keys import twilio_sid, twilio_auth
            twilio_client = TwilioClient(twilio_sid, twilio_auth)
            self.send_message = twilio_client.api.account.messages.create

        for asset in supported_assets:
            for market in supported_assets[asset]["markets"]:
                self.check_alerts_for_coin(asset, market)

        # too many requests per second, keep getting 429 code
        for asset in supported_assets:
            for market in supported_assets[asset]["markets"]:
                # currently only supports 24 hours

                # for time in supported_durations[market]:
                #     self.check_alerts_for_coin_percent(
                #         asset, market, int(time))

                self.check_alerts_for_coin_percent(
                    asset, market, supported_times[1][1])

    def check_date(self):
        """Remove alert from database if at or past end date."""
        timestamp = datetime.now().date()
        dateQuery = Alert.query.filter(
            Alert.end_date < timestamp)

        dateQuery.delete(False)
        db.session.commit()

    def check_alerts_for_coin(self, coin, market):
        """Check for alerts.

        Args:
            coin: The asset to check against.
            market: String of which market to use
        """
        timestamp = datetime.utcnow()

        # Make the request
        price = self.price_tracker.get_spot_price(
            asset=coin, market=market)

        # Get all of the prices that are less than the current amount
        greater_than_query = Alert.query.filter(
            Alert.symbol == coin,
            Alert.price < price,
            Alert.condition == 1,
            ((Alert.market == market) | (Alert.market.is_(None))))
        self.text_greater_than(greater_than_query.all(), price)
        greater_than_query.delete(False)

        less_than_query = Alert.query.filter(
            Alert.symbol == coin,
            Alert.price > price,
            Alert.condition == 0,
            ((Alert.market == market) | (Alert.market.is_(None))))
        self.text_less_than(less_than_query.all(), price)
        less_than_query.delete(False)

        last_price = LastPrice(symbol=coin, price=price, timestamp=timestamp)
        db.session.merge(last_price)

        # TODO(Chase): This will cause race condition.
        db.session.commit()

    def check_alerts_for_coin_percent(self, coin, market, duration):
        """Check for alerts.

        Args:
            coin: The asset to check against.
            market: String of which market to use
        """
        # I need to check each supported time
        percent = self.price_tracker.get_percent_change(
            asset=coin, market=market, duration=duration)

        price = self.price_tracker.get_spot_price(
            asset=coin, market=market)

        if (percent > 0):  # what if 0? did we already check for that?
            # Get all alerts w/ increase less than the current increase
            percent_increase_query = Alert.query.filter(
                Alert.symbol == coin,
                Alert.percent_duration == duration,
                Alert.percent < percent,
                Alert.condition == 2,
                ((Alert.market == market) | (Alert.market.is_(None))))
            if percent_increase_query.count() > 0:
                self.text_percent_increase(
                    percent_increase_query.all(), price, percent)
            percent_increase_query.delete(False)
        else:
            # Get all alerts w/ decrease smaller in magnitude than
            # the current decrease
            percent_decrease_query = Alert.query.filter(
                Alert.symbol == coin,
                Alert.percent_duration == duration,
                - Alert.percent > percent,
                Alert.condition == 3,
                ((Alert.market == market) | (Alert.market.is_(None))))
            if percent_decrease_query.count() > 0:
                self.text_percent_decrease(
                    percent_decrease_query.all(), price, percent * -1)
            percent_decrease_query.delete(False)

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
                        "{} price is above your trigger of ${:.2f}. "
                        "Current price is ${:.2f}"
                        .format(alert.symbol, alert.price, price)))
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
                        "{} price is below your trigger of ${:.2f}. "
                        "Current price is ${:.2f}"
                        .format(alert.symbol, alert.price, price)))
            except twilio.base.exceptions.TwilioRestException:
                print("Invalid number:", alert.phone_number)

    def text_percent_increase(self, alerts, price, percent):
        """Send text message for percent increase triggers.

        Args:
            alerts: The alerts to send. Should be type Alert.
            price: The current asset price.
            percent:
            percent_duration:
        """
        percent_duration_str = ""
        for time in supported_times:
            if time[1] == alerts[0].percent_duration:
                percent_duration_str = time[0]
                break

        print("percent_duration_str: " + percent_duration_str)

        for alert in alerts:
            print("Sending text to %s" % alert.phone_number)
            try:
                # should switch percent w/ alert.percent
                self.send_message(
                    to=alert.phone_number,
                    from_="+15072003597",
                    body=(
                        "{} price has increased by {:.2f}% over {}. "
                        "Current price is ${:.2f}"
                        .format(
                            alert.symbol, percent,
                            percent_duration_str, price)))
            except twilio.base.exceptions.TwilioRestException:
                print("Invalid number:", alert.phone_number)

    def text_percent_decrease(self, alerts, price, percent):
        """Send text message for percent decrease triggers.

        Args:
            alerts: The alerts to send. Should be type Alert.
            price: The current asset price.
            percent:
            percent_duration:
        """
        percent_duration_str = ""
        for time in supported_times:
            if time[1] == alerts[0].percent_duration:
                percent_duration_str = time[0]
                break

        print("percent_duration_str: " + percent_duration_str)

        for alert in alerts:
            print("Sending text to %s" % alert.phone_number)
            try:
                self.send_message(
                    to=alert.phone_number,
                    from_="+15072003597",
                    body=(
                        "{} price has decreased by {:.2f}% over {}. "
                        "Current price is ${:.2f}"
                        .format(
                            alert.symbol, percent,
                            percent_duration_str, price)))
            except twilio.base.exceptions.TwilioRestException:
                print("Invalid number:", alert.phone_number)
