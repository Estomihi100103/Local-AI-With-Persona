from django.contrib import admin
from .models import Persona
from django.utils.html import format_html
# Register your models here.

class PersonaAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'formatted_image')

    def formatted_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px;" />', obj.image.url)
        return "No Image"
    formatted_image.short_description = 'Image'

admin.site.register(Persona, PersonaAdmin)
