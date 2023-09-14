import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from conftest import get_oauth2_token

JWT = get_oauth2_token()


class PublicKeyListCreateTests(APITestCase):
    """
    Contains tests for creating new public keys with the class PublicKeyList in views.
    """

    def setUp(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + JWT
        self.api_url = reverse("public_keys")

    def test_empty_json_payload(self):
        """
        The endpoint expects certain fields to be provided. Errors will be thrown otherwise.
        """
        empty_payload = {}
        response = self.client.post(
            self.api_url, content_type="application/json", data=empty_payload
        )
        response_json = {
            "key_id": ["This field is required."],
            "url": ["This field is required."],
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

    def test_invalid_json_payload(self):
        """
        The endpoint expects certain fields to be provided. Errors will be thrown otherwise.
        """
        invalid_payload = {"key_id": "1", "url": 12}
        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(invalid_payload),
        )
        response_json = {"url": ["Enter a valid URL."]}
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

    def test_invalid_json_payload_1(self):
        """
        The endpoint expects certain fields to be provided. Errors will be thrown otherwise.
        """
        invalid_payload = {"key_id": "", "url": ""}
        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(invalid_payload),
        )
        response_json = {
            "key_id": ["This field may not be blank."],
            "url": ["This field may not be blank."],
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), response_json)

    def test_valid_payload(self):
        """
        Providing a valid payload
        """
        valid_payload = {"key_id": "001", "url": "https://publickeys.test.org"}
        response = self.client.post(
            self.api_url,
            content_type="application/json",
            data=json.dumps(valid_payload),
        )
        response_json = {
            "key_id": "001",
            "url": "https://publickeys.test.org",
            "is_active": True,
        }
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), response_json)


@pytest.mark.usefixtures("create_public_keys")
class PublicKeyListTests(APITestCase):
    """
    Contains tests for listing public keys with the class PublicKeyList in views.
    """

    def setUp(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + JWT
        self.api_url = reverse("public_keys")

    def test_get_public_keys(self):
        """
        The endpoint expects certain fields to be provided. Errors will be thrown otherwise.
        """
        response = self.client.get(
            self.api_url,
            content_type="application/json",
        )
        response_json = [
            {"key_id": "001", "url": "http://publickeyTrue.com", "is_active": True},
            {"key_id": "002", "url": "http://publickeyFalse.com", "is_active": False},
            {"key_id": "003", "url": "http://publickey.com", "is_active": True},
        ]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), response_json)
