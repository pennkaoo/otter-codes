from twilio.rest import Client as TwilioClient
from coinbase.wallet.client import Client as CoinbaseClient
import twilio
import time
from api_keys import (coinbase_auth, coinbase_secret,
                          twilio_sid, twilio_auth, app_secret)


class Texter(object):
    def __init__(self):
        self.cb_client = CoinbaseClient(
            coinbase_auth,
            coinbase_secret,
            api_version='2017-05-19')
        self.twilio_client = TwilioClient(twilio_sid, twilio_auth)
        self.send_message = self.twilio_client.api.account.messages.create
        
        self.coins = ['BTC', 'ETH', 'LTC']

    def check_alerts(self, db):
        for i in range(len(self.coins)):
            self.check_alerts_for_coin(self.coins[i], db)

    def check_alerts_for_coin(self, coin, db):
        from app import Alert

        currency_code = 'USD'  # can also use EUR, CAD, etc.
        # Make the request
        # price = coinbase_client.get_spot_price(currency=currency_code)
        price = self.cb_client.get_spot_price(
            currency_pair=coin +
            '-' +
            currency_code).amount

        # Get all of the prices that are less than the current amount
        greater_than_query = Alert.query.filter(Alert.symbol == coin, Alert.price < price, Alert.above)
        self.text_greater_than(greater_than_query.all(), price)
        greater_than_query.delete(False)

        less_than_query = Alert.query.filter(Alert.symbol == coin, Alert.price > price, not Alert.above)
        self.text_less_than(less_than_query.all(), price)
        less_than_query.delete(False)

        # TODO(Chase): This will cause race condition.
        db.session.commit()


    def text_greater_than(self, alerts, price):
        for alert in alerts:
            # Some logging
            print("Sending text to %s" % alert.phone_number)
            try:
                # Send the text
                self.send_message(
                    to=alert.phone_number,
                    from_="+15072003597",
                    body=(
                        "%s price is above your trigger of %s. Current price is %s"
                        % (alert.symbol, alert.price, price)))
            except twilio.base.exceptions.TwilioRestException:
                # Catch errors.
                print("Invalid number:", s[0])


    def text_less_than(self, alerts, price):
        for alert in alerts:
            # Some logging
            print("Sending text to %s" % alert.phone_number)
            try:
                # Send the text
                self.send_message(
                    to=alert.phone_number,
                    from_="+15072003597",
                    body=(
                        "%s price is below your trigger of %s. Current price is %s"
                        % (alert.symbol, alert.price, price)))
            except twilio.base.exceptions.TwilioRestException:
                # Catch errors.
                print("Invalid number:", s[0])