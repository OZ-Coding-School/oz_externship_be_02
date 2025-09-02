from rest_framework import serializers


class VerificationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    verification_code = serializers.CharField(required=True)


