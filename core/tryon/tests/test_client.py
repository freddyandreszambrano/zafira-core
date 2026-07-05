import hashlib
import hmac
import json
from unittest import mock

import requests
from django.test import TestCase

from core.security.models import ExternalProvider
from core.tryon.services.zafira_ia_client import (
    ZafiraIaClient,
    ZafiraIaRejected,
    ZafiraIaUnavailable,
)


class ZafiraIaClientTests(TestCase):
    def setUp(self):
        self.provider = ExternalProvider.objects.create(
            name="zafira-ia",
            client_id="core-client",
            client_secret="core-secret",
        )

    def test_signed_headers_match_zafira_ia_verifier(self):
        client = ZafiraIaClient(base_url="http://ia.test")
        body = json.dumps({"external_ref": "abc"}).encode("utf-8")

        headers = client.signed_headers(body)

        message = body.decode("utf-8") + headers["X-TIMESTAMP"]
        expected = hmac.new(
            b"core-secret", message.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        self.assertEqual(headers["X-CLIENT-ID"], "core-client")
        self.assertEqual(headers["X-SIGNATURE"], expected)
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_missing_provider_raises_rejected(self):
        self.provider.delete()
        with self.assertRaises(ZafiraIaRejected):
            ZafiraIaClient(base_url="http://ia.test")

    @mock.patch("core.tryon.services.zafira_ia_client.requests.post")
    def test_try_on_success(self, mock_post):
        mock_post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"external_ref": "abc", "result_image_b64": "aW1n"},
        )
        client = ZafiraIaClient(base_url="http://ia.test")

        data = client.try_on(
            external_ref="abc",
            person_image_url="http://core.test/media/p.jpg",
            garment_image_url="http://store.test/g.jpg",
            garment_type="upper_body",
        )

        self.assertEqual(data["result_image_b64"], "aW1n")
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://ia.test/api/v1/tryon")
        sent = json.loads(kwargs["data"])
        self.assertEqual(sent["garment_type"], "upper_body")
        self.assertIn("X-SIGNATURE", kwargs["headers"])

    @mock.patch("core.tryon.services.zafira_ia_client.requests.post")
    def test_try_on_5xx_raises_unavailable(self, mock_post):
        mock_post.return_value = mock.Mock(status_code=503, json=lambda: {})
        client = ZafiraIaClient(base_url="http://ia.test")
        with self.assertRaises(ZafiraIaUnavailable):
            client.try_on(
                external_ref="abc",
                person_image_url="http://core.test/media/p.jpg",
                garment_image_url="http://store.test/g.jpg",
                garment_type="upper_body",
            )

    @mock.patch("core.tryon.services.zafira_ia_client.requests.post")
    def test_try_on_network_error_raises_unavailable(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("boom")
        client = ZafiraIaClient(base_url="http://ia.test")
        with self.assertRaises(ZafiraIaUnavailable):
            client.try_on(
                external_ref="abc",
                person_image_url="http://core.test/media/p.jpg",
                garment_image_url="http://store.test/g.jpg",
                garment_type="upper_body",
            )

    @mock.patch("core.tryon.services.zafira_ia_client.requests.post")
    def test_try_on_4xx_raises_rejected(self, mock_post):
        mock_post.return_value = mock.Mock(
            status_code=422, json=lambda: {"detail": "bad payload"}
        )
        client = ZafiraIaClient(base_url="http://ia.test")
        with self.assertRaises(ZafiraIaRejected):
            client.try_on(
                external_ref="abc",
                person_image_url="http://core.test/media/p.jpg",
                garment_image_url="http://store.test/g.jpg",
                garment_type="upper_body",
            )
