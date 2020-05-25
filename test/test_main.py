import main
import unittest
from unittest.mock import patch

import flask
from telegram import Bot

class TestBot(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = flask.Flask(__name__)
        pass

    @classmethod
    def tearDown(cls):
        pass

    def test_webhook(self):
        with open('test_message.json') as f:
            with patch.object(Bot, 'send_message', return_value='test message') as p_obj:
                with self.app.test_request_context(method='POST', data=f):
                    r = flask.request
                    main.webhook(r)


if __name__ == "__main__":
    unittest.main()
