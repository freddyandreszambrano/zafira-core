from unittest import mock

from django.test import TestCase, override_settings

from core.tryon.task.dispatch import dispatch_generate_try_on


class DispatchGenerateTryOnTests(TestCase):
    @override_settings(TRYON_USE_CELERY=True)
    @mock.patch("core.tryon.task.dispatch.generate_try_on_task")
    def test_celery_mode_enqueues(self, mock_task):
        dispatch_generate_try_on("job-1")

        mock_task.delay.assert_called_once_with("job-1")
        mock_task.apply.assert_not_called()

    @override_settings(TRYON_USE_CELERY=False)
    @mock.patch("core.tryon.task.dispatch.generate_try_on_task")
    def test_direct_mode_runs_inline(self, mock_task):
        dispatch_generate_try_on("job-1")

        mock_task.apply.assert_called_once_with(args=["job-1"])
        mock_task.delay.assert_not_called()
