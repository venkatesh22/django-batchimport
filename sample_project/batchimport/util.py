from django.db import models
from django.db.models import get_model, related
from django.db.models.fields import AutoField

from batchimport_settings import *

import xlrd
from os.path import join, isfile

def process_import_file(import_file, session):
	"""
	Open the uploaded file and save it to the temp file location specified
	in BATCH_IMPORT_TEMPFILE_LOCATION, adding the current session key to
	the file name. Then return the file name so it can be stored in the
	session for the current user.

    **Required arguments**
    
    ``import_file``
    	The uploaded file object.
       
    ``session``
    	The session object for the current user.
    	
    ** Returns**
    
    ``save_file_name``
    	The name of the file saved to the temp location.
    	
    """
	import_file_name = import_file.name
	session_key = session.session_key
	save_file_name = session_key + import_file_name
	destination = open(join(BATCH_IMPORT_TEMPFILE_LOCATION, save_file_name), 'wb+')
	for chunk in import_file.chunks():
		destination.write(chunk)
	destination.close()
	return save_file_name

def get_model_list():
	"""
	Get a list of models for which the user can	batch import information. 
	Start by assuming that the user has specified the list in the
	settings.py file. If not (or it's empty) go through all installed
	apps and get a list of models.
	
	"""
	model_list = []
	settings_model_list = BATCH_IMPORT_IMPORTABLE_MODELS
	if settings_model_list:
		for model in settings_model_list:
			model_list.append((model, model.split('.')[len(model.split('.'))-1]))
	else:
		for app in settings.INSTALLED_APPS:
			if not app == 'batchimport':
				try:
					mod = __import__(app+'.models')
					if 'models' in dir(mod):
						for item in dir(mod.models):
							if (not item is None) and (type(getattr(mod.models, item)) == type(models.Model)):
								if not (app+'.models.'+item, item) in model_list:
									# You have to try to instantiate it to rule out any models
									# you might find in the app that were simply imported (i.e. not
									# REALLY part of that app).
									model = get_model(app, item)
									if model:
										model_list.append((app+'.models.'+item, item))		
				except ImportError:
					pass
	return model_list

def get_column_choice_list(save_file_name):
	"""
	Use xlrd to open the file whose name/path is sent in via ``save_file_name``.
	Once open, retrieve a list of values representing the first value in
	each column of the spreadsheet. Hopefully, this will be a header row
	but if it's not, it will be a list of sample values, one for each column.
    
    **Required arguments**
    
    ``save_file_name``
       The activation key to validate and use for activating the
       ``User``.
    	
    ** Returns**
    
    ``column_choice_list``
    	A list of choice tuples to be used to get the mapping between a model
    	field and a spreadsheet column.

	"""
	column_choice_list = []
	column_choice_list.append((-1, 'SELECT COLUMN'))
	filepath = join(BATCH_IMPORT_TEMPFILE_LOCATION, save_file_name)
	if not isfile(filepath):
		raise NameError, "%s is not a valid filename" % save_file_name
	book = xlrd.open_workbook(filepath)
	sheet = book.sheet_by_index(0)
	column_index = 0
	for column in range(0,sheet.ncols):
		column_item = sheet.cell_value(rowx=0, colx=column)
		column_choice_list.append((column_index, column_item))
		column_index = column_index + 1
	return column_choice_list

def get_model_fields(model_name):
	"""
	Use reflection to get the list of fields in the supplied model. If any
	of the fields represented a related field (ForeignKey, OneToOne, etc)
	then the function will get a list of fields for the related model. 
	These fields will be used to prompt the user to map a spreadsheet
	column value to a specific field on the RELATED model for related
	fields.
	
	For example, suppose you had a model for Student that had a field
	for name, a field for date of birth and a foreign key field to teacher.
	The spreadsheet the user uploads may have name, dob, teacher.
	The related model is Teacher which has a bunch of fields too. By
	getting a list of these fields, we can prompt the user later to
	specify WHICH field on the related model we should use to search
	for the specific Teacher we want to relate to a given student (from
	a row in the spreadsheet). This gives the user the flexibility
	of creating a spreadsheet with student_name, student_dob, and
	teacher_id OR teacher_email OR teacher_name, etc. 
    
    **Required arguments**
    
    ``model_name``
       The (full) name of the model for which a batch import is being
       attempted.
    	
    ** Returns**
    
    ``field_tuple_list``
    	Each entry is a tuple in the form:
    		(field_name, [list_of_field_names_for_related_model]) 

	"""
	field_tuple_list = []
	app_name = model_name.split(".")[0]
	specific_model_name = model_name.split('.')[-1]
	model = get_model(app_name, specific_model_name)
	opts = model._meta
	
	# Process non many-to-many fields (includes ForeignKey relationships).
	field_tuple_list.extend(_get_field_tuple_list(opts.fields))
	field_tuple_list.extend(_get_field_tuple_list(opts.many_to_many))
	return field_tuple_list


def _get_field_tuple_list(field_list):
	"""
	Used by ``get_model_fields`` to retrieve a list of tuples. Each tuple consists of a
	field name and, in the case of a field representing a relationship to another
	model (via ManyToMany, OneToOne, etc), a list of fields on the related model.
    **Required arguments**
    
    ``field_list``
    	List of fields to process.
       
    ** Returns**
    
    ``field_tuple_list``
    	List of tuples.
    	
	"""
	field_tuple_list = []
	for field in field_list:
		related_model_field_name_list = []
		# We will skip all '_ptr' and AutoField fields so we don't disrupt
		# django's inner workings.
		related_model_name = None
		related_model_app_name = None
		if (not field.name[-4:] == '_ptr') and (not field.__class__ == AutoField):
			if issubclass(field.__class__, related.RelatedField):
				related_model_app_name = field.rel.to.__module__.split('.')[0]
				# We'll ignore all django-specific models (such as User, etc).
				if not related_model_app_name == 'django':
					related_model_name = field.rel.to.__name__
					related_model = get_model(related_model_app_name, related_model_name)
					for sub_field in related_model._meta.fields:
						# For fields representing a relationship to another model
						# we'll ignore all _ptr fields, AutoFields AND
						# all related fields.
						if (not sub_field.name[-4:] == '_ptr') and \
						  (not sub_field.__class__ == AutoField) and \
						  (not issubclass(sub_field.__class__, related.RelatedField)):
							related_model_field_name_list.append(sub_field.name)
				else:
					continue
			field_tuple_list.append((field.name, related_model_app_name, related_model_name, related_model_field_name_list))
	return field_tuple_list


