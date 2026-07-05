from unittest import mock

import requests
from django.test import TestCase

from core.tryon.services.zafira_ia_client import (
    ZafiraIaClient,
    ZafiraIaRejected,
    ZafiraIaUnavailable,
)


class ZafiraIaClientTests(TestCase):
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
        self.assertEqual(kwargs["json"]["garment_type"], "upper_body")
        self.assertEqual(kwargs["json"]["external_ref"], "abc")

    def test_default_base_url_points_to_local_zafira_ia(self):
        client = ZafiraIaClient()
        self.assertEqual(client.base_url, "http://localhost:8001")

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

    @mock.patch("core.tryon.services.zafira_ia_client.requests.post")
    def test_try_on_503_rate_limited_propagates_code(self, mock_post):
        mock_post.return_value = mock.Mock(
            status_code=503, json=lambda: {"detail": "quota", "code": "RATE_LIMITED"}
        )
        client = ZafiraIaClient(base_url="http://ia.test")
        with self.assertRaises(ZafiraIaUnavailable) as ctx:
            client.try_on(
                external_ref="abc",
                person_image_url="http://core.test/media/p.jpg",
                garment_image_url="http://store.test/g.jpg",
                garment_type="upper_body",
            )
        self.assertEqual(ctx.exception.code, "RATE_LIMITED")

    @mock.patch("core.tryon.services.zafira_ia_client.requests.post")
    def test_try_on_rejected_propagates_code(self, mock_post):
        mock_post.return_value = mock.Mock(
            status_code=422,
            json=lambda: {"detail": "blocked", "code": "GENERATION_REJECTED"},
        )
        client = ZafiraIaClient(base_url="http://ia.test")
        with self.assertRaises(ZafiraIaRejected) as ctx:
            client.try_on(
                external_ref="abc",
                person_image_url="http://core.test/media/p.jpg",
                garment_image_url="http://store.test/g.jpg",
                garment_type="upper_body",
            )
        self.assertEqual(ctx.exception.code, "GENERATION_REJECTED")
