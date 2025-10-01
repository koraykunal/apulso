import fal_client
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import logging
import time
from typing import Optional, Dict, Any

from .models import TryOnRequest, TryOnRequestStatus, TryOnUsageStats

logger = logging.getLogger(__name__)


class FalAITryOnService:
    FAL_ENDPOINT = "fal-ai/kling/v1-5/kolors-virtual-try-on"
    DEFAULT_COST = Decimal('0.07')

    def __init__(self):
        if not hasattr(settings, 'FAL_KEY') or not settings.FAL_KEY:
            raise ValueError("FAL_KEY not configured in settings")

    def create_try_on_request(self, user=None, demo_invitation=None, human_image=None, garment_image=None) -> TryOnRequest:
        request = TryOnRequest.objects.create(
            user=user,
            demo_invitation=demo_invitation,
            human_image=human_image,
            garment_image=garment_image,
            status=TryOnRequestStatus.PENDING
        )

        if user:
            self._update_user_stats(user, 'total_requests')
        return request

    def process_try_on_request(self, request: TryOnRequest, demo_context=None) -> bool:
        try:
            request.status = TryOnRequestStatus.PROCESSING
            request.save()

            start_time = time.time()

            result = self._call_fal_api(request.human_image, request.garment_image)

            processing_time = time.time() - start_time

            if result and 'image' in result:
                request.result_image_url = result['image']['url']
                request.status = TryOnRequestStatus.COMPLETED
                request.completed_at = timezone.now()
                request.processing_time = processing_time
                request.save()

                if request.user:
                    self._update_user_stats(request.user, 'successful_requests')
                    self._update_user_stats(request.user, 'total_cost', self.DEFAULT_COST)

                logger.info(f"TryOn request {request.id} completed successfully")
                return True
            else:
                raise Exception("Invalid response from FAL API")

        except Exception as e:
            request.status = TryOnRequestStatus.FAILED
            request.error_message = str(e)
            request.save()

            if request.user:
                self._update_user_stats(request.user, 'failed_requests')

            logger.error(f"TryOn request {request.id} failed: {str(e)}")
            return False

    def _call_fal_api(self, human_image_file, garment_image_file) -> Optional[Dict[Any, Any]]:
        try:
            human_image_url = self._upload_file_to_fal(human_image_file.path)
            garment_image_url = self._upload_file_to_fal(garment_image_file.path)

            logger.info(f"Uploaded images - Human: {human_image_url}, Garment: {garment_image_url}")

            result = fal_client.subscribe(
                self.FAL_ENDPOINT,
                arguments={
                    "human_image_url": human_image_url,
                    "garment_image_url": garment_image_url
                }
            )
            return result
        except Exception as e:
            logger.error(f"FAL API call failed: {str(e)}")
            raise

    def _call_fal_api_with_urls(self, human_image_url: str, garment_image_url: str) -> Optional[Dict[Any, Any]]:
        try:
            logger.info(f"Using external URLs - Human: {human_image_url}, Garment: {garment_image_url}")

            result = fal_client.subscribe(
                self.FAL_ENDPOINT,
                arguments={
                    "human_image_url": human_image_url,
                    "garment_image_url": garment_image_url
                }
            )
            return result
        except Exception as e:
            logger.error(f"FAL API call failed: {str(e)}")
            raise

    def create_try_on_request_from_urls(self, user=None, demo_invitation=None, human_image_url: str = None, garment_image_url: str = None) -> TryOnRequest:
        request = TryOnRequest.objects.create(
            user=user,
            demo_invitation=demo_invitation,
            human_image_url=human_image_url,
            garment_image_url=garment_image_url,
            status=TryOnRequestStatus.PENDING
        )

        if user:
            self._update_user_stats(user, 'total_requests')
        return request

    def process_try_on_request_from_urls(self, request: TryOnRequest, human_image_url: str, garment_image_url: str, demo_context=None) -> bool:
        try:
            request.status = TryOnRequestStatus.PROCESSING
            request.save()

            start_time = time.time()

            result = self._call_fal_api_with_urls(human_image_url, garment_image_url)

            processing_time = time.time() - start_time

            if result and 'image' in result:
                request.result_image_url = result['image']['url']
                request.status = TryOnRequestStatus.COMPLETED
                request.completed_at = timezone.now()
                request.processing_time = processing_time
                request.save()

                if request.user:
                    self._update_user_stats(request.user, 'successful_requests')
                    self._update_user_stats(request.user, 'total_cost', self.DEFAULT_COST)

                logger.info(f"TryOn request {request.id} completed successfully")
                return True
            else:
                raise Exception("Invalid response from FAL API")

        except Exception as e:
            request.status = TryOnRequestStatus.FAILED
            request.error_message = str(e)
            request.save()

            if request.user:
                self._update_user_stats(request.user, 'failed_requests')

            logger.error(f"TryOn request {request.id} failed: {str(e)}")
            return False

    def _upload_file_to_fal(self, file_path: str) -> str:
        try:
            with open(file_path, 'rb') as f:
                file_upload = fal_client.upload_file(f)
                return file_upload.url
        except Exception as e:
            logger.error(f"Failed to upload file to FAL: {str(e)}")
            raise

    def _update_user_stats(self, user, field: str, value=1):
        stats, created = TryOnUsageStats.objects.get_or_create(user=user)

        if field == 'total_cost':
            stats.total_cost += value
        else:
            current_value = getattr(stats, field, 0)
            setattr(stats, field, current_value + 1)

        stats.save()

    def get_user_stats(self, user) -> TryOnUsageStats:
        stats, created = TryOnUsageStats.objects.get_or_create(user=user)
        return stats

    def get_user_requests(self, user, limit: int = 10):
        return TryOnRequest.objects.filter(user=user)[:limit]