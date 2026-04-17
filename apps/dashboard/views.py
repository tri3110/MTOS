from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.users.authentication import CookieJWTAuthentication
from apps.orders.models import Order
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q

def build_series(queryset, from_date, days):
    data_map = {
        item["date"]: float(item["total"])
        for item in queryset
    }

    series = []
    labels = []

    for i in range(days):
        current_day = (from_date + timedelta(days=i)).date()

        series.append(data_map.get(current_day, 0))
        labels.append(current_day.strftime("%a"))

    return series, labels

def calc_stats(series):
    if not series:
        return {"avg": 0, "percent": 0}

    avg = sum(series) / len(series)
    last = series[-1]

    percent = ((last - avg) / avg * 100) if avg != 0 else 0

    return {
        "avg": round(avg, 1),
        "percent": round(percent, 1)
    }

def parse_date_range(request):
    range_param = request.GET.get("range")
    from_date = request.GET.get("from")
    to_date = request.GET.get("to")

    now = timezone.now()

    if range_param == "7d":
        return now - timedelta(days=6), now
    elif range_param == "30d":
        return now - timedelta(days=29), now
    elif range_param == "today":
        return now.replace(hour=0, minute=0, second=0), now

    if from_date and to_date:
        return (
            timezone.make_aware(timezone.datetime.fromisoformat(from_date)),
            timezone.make_aware(timezone.datetime.fromisoformat(to_date))
        )

    return now - timedelta(days=6), now

def build_multi_series(queryset, from_date, days):
    data_map = {item["date"]: item for item in queryset}

    result = {
        "revenue": [],
        "orders": [],
        "pending": [],
        "confirmed": [],
        "completed": [],
        "delivering": [],
        "cancelled": [],
        "labels": []
    }

    for i in range(days):
        day = (from_date + timedelta(days=i)).date()
        item = data_map.get(day, {})

        result["revenue"].append(float(item.get("revenue") or 0))
        result["orders"].append(item.get("orders", 0))
        result["pending"].append(item.get("pending", 0))
        result["confirmed"].append(item.get("confirmed", 0))
        result["completed"].append(item.get("completed", 0))
        result["delivering"].append(item.get("delivering", 0))
        result["cancelled"].append(item.get("cancelled", 0))
        result["labels"].append(day.strftime("%a"))

    return result

class DashboardView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from_date, to_date = parse_date_range(request)

        days = (to_date.date() - from_date.date()).days + 1

        orders = Order.objects.filter(
            created_at__date__range=(from_date, to_date),
            is_deleted=False
        )

        # 🔥 1 query duy nhất
        stats_by_day = (
            orders.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                revenue=Sum("total_price", filter=Q(status="completed")),
                orders=Count("id"),
                pending=Count("id", filter=Q(status="pending")),
                confirmed=Count("id", filter=Q(status="confirmed")),
                completed=Count("id", filter=Q(status="completed")),
                delivering=Count("id", filter=Q(status="delivering")),
                cancelled=Count("id", filter=Q(status="cancelled")),
            )
        )

        series = build_multi_series(stats_by_day, from_date, days)


        status_keys = ["pending", "confirmed", "completed", "delivering", "cancelled"]
        response_status = {}
        for key in status_keys:
            response_status[key] = {
                "total": sum(series[key]),
                "series": series[key],
                **calc_stats(series[key])
            }

        return Response({
            "categories": series["labels"],

            "revenue": {
                "total": sum(series["revenue"]),
                "series": series["revenue"],
                **calc_stats(series["revenue"])
            },

            "orders": {
                "total": sum(series["orders"]),
                "series": series["orders"],
                **calc_stats(series["orders"])
            },

            **response_status
        })