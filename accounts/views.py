from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions
from rest_framework.response import Response
from django.db.models import Sum
from .models import User, Activity
from .serializer import UserSerializer, ActivitySerializer
from rest_framework import generics, permissions
from rest_framework.response import Response
from datetime import datetime


# Register user
class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer


# List and create user activities

class ActivityListCreateView(generics.ListCreateAPIView):
    serializer_class = ActivitySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # Get all activities for the logged-in user
        queryset = Activity.objects.all().filter(user=self.request.user)
        # 
        # Optional: filter by date
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)

        return queryset
    # def get_queryset(self):
    #     return Activity.objects.filter(user=self.request.user)


# Carbon footprint total
class CarbonFootprintView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total_emission = Activity.objects.filter(user=request.user).aggregate(
            total=Sum('carbon_emission_kg')
        )['total'] or 0
        return Response({"total_carbon_kg": total_emission})


# Community leaderboard
class LeaderboardView(generics.GenericAPIView):
    queryset = User.objects.all()  # required by GenericAPIView

    def get(self, request, *args, **kwargs):
        leaderboard = []
        for user in self.get_queryset():  # uses the queryset
            total = Activity.objects.filter(user=user).aggregate(
                total=Sum('carbon_emission_kg')
            )['total'] or 0
            leaderboard.append({"username": user.username, "total_emission": total})

        # Sort ascending by total emission (less carbon = better)
        leaderboard.sort(key=lambda x: x['total_emission'])
        return Response(leaderboard)
    


class ActivityByDateView(generics.ListAPIView):
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        date_str = self.kwargs.get('date')

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Activity.objects.none()  # invalid date

        return Activity.objects.filter(user=user, date=date_obj)



from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import Activity
from .serializer import ActivitySerializer
from datetime import datetime, timedelta

class WeeklyActivityView(generics.ListAPIView):
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        date_str = self.kwargs.get('date')

        try:
            end_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Activity.objects.none()  # invalid date

        # Calculate previous Sunday
        # weekday() returns 0=Monday, 6=Sunday
        weekday = end_date.weekday()
        days_since_sunday = (weekday + 1) % 7  # Sunday = 6 → 0 days back
        start_date = end_date - timedelta(days=days_since_sunday)

        # Filter activities for user between start_date and end_date
        return Activity.objects.filter(user=user, date__range=[start_date, end_date])
    

from rest_framework import generics, permissions
from .models import Activity
from datetime import datetime
from django.db.models import Sum

class MonthlyActivityView(generics.ListAPIView):
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        date_str = self.kwargs.get('date')

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Activity.objects.none()  # invalid date

        # Get first and last day of the month
        first_day = date_obj.replace(day=1)
        if date_obj.month == 12:
            last_day = date_obj.replace(day=31)
        else:
            next_month = date_obj.replace(month=date_obj.month + 1, day=1)
            last_day = next_month - timedelta(days=1)

        return Activity.objects.filter(user=user, date__range=[first_day, last_day])
