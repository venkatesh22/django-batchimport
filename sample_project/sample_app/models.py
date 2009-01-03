from django.db import models
from django.contrib.localflavor.us.us_states import STATE_CHOICES
from django.contrib.localflavor.us.models import PhoneNumberField

TITLE_CHOICES = (
    ('Dr.', 'Dr.'),
    ('Mr.', 'Mr.'),
    ('Ms.', 'Ms.'),
    ('Mrs.', 'Mrs.'),
    ('Miss.', 'Miss.'),
)

# Create your models here.
class School(models.Model):
    name = models.CharField("Name of school", max_length=100)
    address_1 = models.CharField("Street address of school", max_length=200)
    address_2 = models.CharField("Suite, Box #, etc", max_length=200, blank=True, null=True)
    city = models.CharField("City", max_length=100)
    state = models.CharField("State", choices=STATE_CHOICES, max_length=100)
    zip = models.CharField("Zipcode", max_length=10)
    phone = PhoneNumberField("Main phone number for school")
    fax = PhoneNumberField("Fax number for school", null=True)
    def __unicode__(self):
        return self.name + ' (' + self.city + ', ' + self.state + ')'

class Teacher(models.Model):
    title = models.CharField("Title", max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField("First name", max_length=100)
    last_name = models.CharField("Last name", max_length=100)
    email = models.EmailField(blank=True)
    phone_1 = PhoneNumberField("Primary phone number")
    school = models.ForeignKey(School)
    def __unicode__(self):
        return self.last_name + ', ' + self.first_name
