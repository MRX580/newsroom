from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255)

class BusinessAgreement(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

class VideoProject(models.Model):
    published_at = models.DateField()
    limit_type = models.CharField(max_length=64)

class VideoProjectTranslation(models.Model):
    video_project = models.ForeignKey(VideoProject, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)

class Tag(models.Model):
    name = models.CharField(max_length=128)

class TagConnection(models.Model):
    video_project = models.ForeignKey(VideoProject, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

class BusinessAgreementOperation(models.Model):
    created_at = models.DateField()
    agreement = models.ForeignKey(BusinessAgreement, on_delete=models.CASCADE)
    video_project = models.ForeignKey(VideoProject, on_delete=models.CASCADE)
