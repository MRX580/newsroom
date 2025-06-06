from django.contrib import admin
from .models import *

admin.site.register(Company)
admin.site.register(BusinessAgreement)
admin.site.register(VideoProject)
admin.site.register(VideoProjectTranslation)
admin.site.register(Tag)
admin.site.register(TagConnection)
admin.site.register(BusinessAgreementOperation)
