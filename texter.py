from twilio.rest import Client as TwilioClient
from coinbase.wallet.client import Client as CoinbaseClient
import twilio

import sqlite3
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

    def check_alerts(self, db_conn, db_cursor):
        for i in range(len(self.coins)):
            self.check_alerts_for_coin(self.coins[i], db_conn, db_cursor)

    def check_alerts_for_coin(self, coin, db_conn, db_cursor):
        base_code = coin
        currency_code = 'USD'  # can also use EUR, CAD, etc.
        # Make the request
        # price = coinbase_client.get_spot_price(currency=currency_code)
        price = self.cb_client.get_spot_price(
            currency_pair=base_code +
            '-' +
            currency_code)
        # Get all of the prices that are less than the current amount
        cmd = ('SELECT phone_number, price, symbol '
               'FROM alerts where symbol = ? and price < ? and above = 1')
        stuff = db_cursor.execute(cmd, (base_code, price.amount))
        self.text_greater_than(stuff, price)
        cmd = ('SELECT phone_number, price, symbol '
               'FROM alerts where symbol = ? and price > ? and above = 0')
        stuff = db_cursor.execute(cmd, (base_code, price.amount))
        self.text_less_than(stuff, price)
        # Delete values we sent texts to.
        # TODO(Chase): This will cause race condition.
        cmd = 'DELETE FROM alerts where symbol = ? and price > ? and above = 0'
        db_cursor.execute(cmd, (base_code, price.amount))
        cmd = 'DELETE FROM alerts where symbol = ? and price < ? and above = 1'
        db_cursor.execute(cmd, (base_code, price.amount))
        db_conn.commit()


    def text_greater_than(self, clients, price):
        for s in clients:
            # Some logging
            print("Sending text to %s" % s[0])
            try:
                # Send the text
                self.send_message(
                    to=s[0],
                    from_="+15072003597",
                    body=(
                        "%s price is above your trigger of %s. Current price is %s"
                        % (s[2], s[1], price.amount)))
            except twilio.base.exceptions.TwilioRestException:
                # Catch errors.
                print("Invalid number:", s[0])


    def text_less_than(self, clients, price):
        for s in clients:
            # Some logging
            print("Sending text to %s" % s[0])
            try:
                # Send the text
                self.send_message(
                    to=s[0],
                    from_="+15072003597",
                    body=(
                        "%s price is below your trigger of %s. Current price is %s"
                        % (s[2], s[1], price.amount)))
            except twilio.base.exceptions.TwilioRestException:
                # Catch errors.
                print("Invalid number:", s[0])