import logging
import time
import uuid

logger = logging.getLogger('app')


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # gắn vào request để dùng chỗ khác nếu cần
        request.request_id = request_id

        user_id = request.user.id if request.user.is_authenticated else None
        ip = request.META.get("REMOTE_ADDR")

        logger.info(
            f"[{request_id}] START {request.method} {request.path} "
            f"user={user_id} ip={ip}"
        )

        try:
            response = self.get_response(request)
        except Exception:
            logger.exception(
                f"[{request_id}] ERROR {request.method} {request.path}"
            )
            raise

        duration = round((time.time() - start_time) * 1000, 2)

        logger.info(
            f"[{request_id}] END {request.method} {request.path} "
            f"{response.status_code} {duration}ms"
        )

        if duration > 300:
            logger.warning(f"[{request_id}] SLOW {request.method} {request.path} {duration}ms")

        if duration > 1000:
            logger.error(f"[{request_id}] VERY SLOW {request.method} {request.path} {duration}ms")

        return response