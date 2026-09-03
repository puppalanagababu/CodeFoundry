"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from users.views import (
    DashboardView,
    LeaderboardView,
    PublicProfileView,
    RecruiterCandidateDetailView,
    RecruiterCandidateListView,
    SkillProfileView,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/users/skill-profile/', SkillProfileView.as_view(), name='user-skill-profile'),
    path('api/users/profile/<str:username>/', PublicProfileView.as_view(), name='public-profile'),
    path('api/leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('api/recruiter/candidates/', RecruiterCandidateListView.as_view(), name='recruiter-candidate-list'),
    path('api/recruiter/candidates/<str:username>/', RecruiterCandidateDetailView.as_view(), name='recruiter-candidate-detail'),
    path('api/submissions/', include('submissions.urls')),
    path('api/challenges/', include('challenges.urls')),
    path('api/execution/', include('execution.urls')),
]


