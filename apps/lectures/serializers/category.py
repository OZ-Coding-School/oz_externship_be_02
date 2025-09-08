from rest_framework.serializers import ModelSerializer
from apps.lectures.models.categories import Category

class CategorySerializer(ModelSerializer[Category]):
    class Meta:
        model = Category
        fields = ["name"]