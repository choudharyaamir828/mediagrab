from django.urls import path
from .views import VideoInfoView, DownloadVideoView

urlpatterns = [
    path('info/', VideoInfoView.as_view(), name='video-info'),
    path('download/', DownloadVideoView.as_view(), name='video-download'),
]
