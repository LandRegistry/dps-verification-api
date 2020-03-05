import unittest

from verification_api.main import app


class TestNotFound(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_not_found(self):
        self.assertEqual((self.app.get('/doest_exist')).status_code, 404)
