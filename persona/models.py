from django.db import models

            
class Persona(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    guide_prompt = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='persona_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name