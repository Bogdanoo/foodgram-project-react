import base64

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            decoded_file = base64.b64decode(data.split(',')[1])
            file_name = 'image.jpg'
            data = ContentFile(decoded_file, name=file_name)
        return super().to_internal_value(data)
