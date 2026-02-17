from rest_framework import serializers


class URLSerializer(serializers.Serializer):
    url = serializers.URLField(required=True, help_text="YouTube or Instagram URL")


class DownloadSerializer(serializers.Serializer):
    url = serializers.URLField(required=True)
    format_id = serializers.CharField(required=False, default="best")
    download_type = serializers.ChoiceField(
        choices=["video", "audio"],
        default="video",
        help_text="Choose 'video' or 'audio'"
    )
