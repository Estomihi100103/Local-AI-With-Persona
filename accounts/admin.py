from django.contrib import admin
from .models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'persona', 'nim', 'gpa', 'angkatan', 'get_course_programming', 'study_program')
    search_fields = ('user__username', 'nim')
    list_filter = ('get_course_programming',)
    ordering = ('user',)
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('user', 'persona', 'nim', 'gpa', 'angkatan', 'get_course_programming', 'study_program')
        }),
    )

admin.site.register(UserProfile, UserProfileAdmin)