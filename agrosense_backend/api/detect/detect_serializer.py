from rest_framework import serializers

class DetectSerializer(serializers.Serializer):
    image = serializers.ImageField()
    user_id = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )
