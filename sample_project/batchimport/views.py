"""
Views which allow users batch import/update any data for which
a model is present.

"""
import sys
import os
from os.path import join, isfile

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.forms.forms import BoundField
from django.db.models import get_model
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

import xlrd

from util import process_import_file
from forms import UploadImportFileForm
from forms import ImportOptionsForm
from batchimport_settings import *


# TODO:
# - Add overrides for forms everywhere.
# - Add overrides for templates too.

def import_start(request, extra_context=None):
	"""
    Start the import process by presenting/accepting a form into
	which the user specifies the model for whom an XLS file is
	being uploaded and the file/path of the file to upload.
    
    See documentation to learn about customizing the templates
    used for batch import.
    
	"""
	if request.method == 'POST':
		form = UploadImportFileForm(request.POST, request.FILES)
		if form.is_valid():
			save_file_name = process_import_file(form.cleaned_data['import_file'], request.session)
			request.session['save_file_name'] = save_file_name
			request.session['model_for_import'] = form.cleaned_data['model_for_import']
			return HttpResponseRedirect(reverse('batchimport_import_options'))
	else:
		form = UploadImportFileForm()
	if extra_context is None:
		extra_context = {}

	context = RequestContext(request)
	for key, value in extra_context.items():
		context[key] = callable(value) and value() or value
		
	return render_to_response(BATCH_IMPORT_START_TEMPLATE, 
							  {'form': form},
                              context_instance=context)
	
def import_options(request, extra_context=None):
	"""
	This view allows the user to specify options for how the system should
	attempt to import the data in the uploaded Excel spreadsheet.
	
	If this view is not processed, the system will use the default settings
	for the mechanics-specific options (whether to show successful imports
	in the results, for example) and will try to guess the appropriate
	model.field to spreadsheet.column mappings to use. See ``import_execute``
	for more on that part.
	
	"""
	try:
		save_file_name = request.session['save_file_name']
		model_for_import = request.session['model_for_import']
	except KeyError:
		# Either we don't have a file or we don't know what we're importing.
		# So restart the process with a blank form (which will show the
		# model list).
		form = UploadImportFileForm()
		if extra_context is None:
			extra_context = {}
	
		context = RequestContext(request)
		for key, value in extra_context.items():
			context[key] = callable(value) and value() or value
			
		return render_to_response(BATCH_IMPORT_START_TEMPLATE, 
								  {'form': form},
		                          context_instance=context)
		
	if request.method == 'POST':
		# Add the various options to the session for use during execution.
		form = ImportOptionsForm(model_for_import, save_file_name, request.POST, request.FILES)
		if form.is_valid():
			# Put the various user-specified options in the session for use during execution.
			request.session['field_name_list'] = form.field_dict.keys()
			request.session['show_successful_imports'] = form.cleaned_data['show_successful_imports']
			request.session['show_successful_updates'] = form.cleaned_data['show_successful_updates']
			request.session['show_errors'] = form.cleaned_data['show_errors']
			request.session['stop_on_first_error'] = form.cleaned_data['stop_on_first_error']
			request.session['update_dupes'] = form.cleaned_data['update_dupes']
			request.session['start_row'] = form.cleaned_data['start_row']
			request.session['end_row'] = form.cleaned_data['end_row']
				
			# Put each dynamically created form field's value in the session here.
			for field_name in form.field_dict.keys():
				request.session[field_name + '_related_model_app_name'] = form.related_model_dict[field_name][0]
				request.session[field_name + '_related_model_name'] = form.related_model_dict[field_name][1]
				request.session[field_name + '_xls_column'] = form.cleaned_data[field_name + '_xls_column']
				request.session[field_name + '_default_value'] = form.cleaned_data[field_name + '_default_value']
				if request.session[field_name + '_default_value'] == '':
					request.session[field_name + '_default_value'] = None
				request.session[field_name + '_mapping_choice'] = form.cleaned_data[field_name + '_mapping_choice']
				request.session[field_name + '_is_id_field'] = form.cleaned_data[field_name + '_is_id_field']
		else:
			form.field_dict = _get_bound_field_dict(form)
			if extra_context is None:
				extra_context = {}
		
			context = RequestContext(request)
			for key, value in extra_context.items():
				context[key] = callable(value) and value() or value

			return render_to_response(BATCH_IMPORT_OPTIONS_TEMPLATE, {'form': form, 'model_for_import':model_for_import},
		                          context_instance=context)
			

		# Redirect to the Processing template which displays a "processing,
		# please wait" notice and immediately fires off execution of the import.
		if extra_context is None:
			extra_context = {}
	
		context = RequestContext(request)
		for key, value in extra_context.items():
			context[key] = callable(value) and value() or value
		return render_to_response(BATCH_IMPORT_EXECUTE_TEMPLATE, {}, context_instance=context)
	else:
		form = ImportOptionsForm(model_for_import, save_file_name)
		form.field_dict = _get_bound_field_dict(form)
		if extra_context is None:
			extra_context = {}
	
		context = RequestContext(request)
		for key, value in extra_context.items():
			context[key] = callable(value) and value() or value

		return render_to_response(BATCH_IMPORT_OPTIONS_TEMPLATE, {'form': form, 'model_for_import':model_for_import},
	                          context_instance=context)
	
def import_execute(request, extra_context=None):
	# Get the name of the uploaded Excel file for processing and the model
	# for which we're trying to import. If either are missing, send the user
	# back to the beginning of the process.
	try:
		save_file_name = request.session['save_file_name']
		model_for_import = request.session['model_for_import']
	except KeyError:
		# Either we don't have a file or we don't know what we're importing.
		# So restart the process with a blank form (which will show the
		# model list).
		form = UploadImportFileForm()
		return render_to_response(BATCH_IMPORT_START_TEMPLATE, {'form': form})

	# Retrieve the "import mechanics options". These will be set from the
	# user-specified options or from the settings-based defaults.
	show_successful_imports = _get_option_setting(request, 'show_successful_imports', BATCH_IMPORT_SHOW_SUCCESSFUL_IMPORTS)
	show_successful_updates = _get_option_setting(request, 'show_successful_updates', BATCH_IMPORT_SHOW_SUCCESSFUL_UPDATES)
	show_errors = _get_option_setting(request, 'show_errors', BATCH_IMPORT_SHOW_ERRORS)
	stop_on_first_error = _get_option_setting(request, 'stop_on_first_error', BATCH_IMPORT_STOP_ON_FIRST_ERROR)
	update_dupes = _get_option_setting(request, 'update_dupes', BATCH_IMPORT_UPDATE_DUPS)
	start_row = _get_option_setting(request, 'start_row', BATCH_IMPORT_START_ROW)
	end_row = _get_option_setting(request, 'end_row', BATCH_IMPORT_END_ROW)
	
	# Prepare the context to be sent to the template so we can load it
	# as we go along.
	status_dict = {}
	
	# Prepare for the results processing.
	status_dict['model_for_import'] = model_for_import.split('.')[-1]
	status_dict['start_row'] = start_row
	status_dict['end_row'] = end_row
	status_dict['num_rows_in_spreadsheet'] = 0

	status_dict['num_rows_processed'] = 0
	status_dict['num_items_imported'] = 0
	status_dict['num_items_updated'] = 0
	status_dict['num_errors'] = 0
	status_dict['combined_results_messages'] = []
	status_dict['import_results_messages'] = []
	status_dict['update_results_messages'] = []
	status_dict['error_results_messages'] = []

	# Open the uploaded Excel file and iterate over each of its rows starting
	# start_row and ending at end_row.
	filepath = join(BATCH_IMPORT_TEMPFILE_LOCATION, save_file_name)
	if not isfile(filepath):
		status_dict['error_results_messages'].append('Error opening file. Uploaded file was either not found or corrupt.')
		return _render_results_response(request, status_dict, extra_context)
	
	# Try to open the uploaded Excel file. If it fails, bomb out.
	try:
		book = xlrd.open_workbook(filepath)
		sheet = book.sheet_by_index(0)
		status_dict['num_rows_in_spreadsheet'] = sheet.nrows
	except:
		status_dict['error_results_messages'].append('Error opening Excel file: '+ sys.exc_info()[1])
		return _render_results_response(request, status_dict, extra_context)
	
	# Determine the last row of the spreadsheet to be processed.
	if end_row == -1:
		end_row = sheet.nrows
		status_dict['end_row'] = end_row

	# Iterate over each row in the spreadsheet. For each row, try to insert
	# a new item in the database for the appropriate model.
	for row in range(start_row-1,end_row):
		try:
			status_dict['num_rows_processed'] = status_dict['num_rows_processed'] + 1
			# Get the list of fields for our object.
			field_name_list = request.session['field_name_list']
			field_value_dict = {}
			field_identity_dict = {}
			for field_name in field_name_list:
				# First retrieve the correct value from the current row.
				column_number = int(request.session[field_name + '_xls_column'])
				if column_number > -1:
					value_from_spreadsheet_row = sheet.cell_value(rowx=row, colx=column_number)
				else:
					value_from_spreadsheet_row = None
				field_value_from_sheet = value_from_spreadsheet_row or request.session[field_name + '_default_value']
				field_value = field_value_from_sheet
	
				# If the current field represents a relationship, get the id 
				# from the related model using the mapping specified by the user.
				field_related_model_name = request.session[field_name + '_related_model_name']
				field_related_model_app_name = request.session[field_name + '_related_model_app_name']
				field_related_model_field_name = request.session[field_name + '_mapping_choice']
				if not field_related_model_name is None:
					related_object_keyword_dict = {}
					related_object_keyword_dict[str(field_related_model_field_name+'__iexact')] = str(field_value_from_sheet)
					related_model_class = get_model(field_related_model_app_name, field_related_model_name)
					try:
						related_object = related_model_class.objects.get(**related_object_keyword_dict)
						field_value = related_object
					except:
						field_value = None
				if field_value:
					field_value_dict[field_name] = field_value
					field_is_identifier = request.session[field_name + '_is_id_field']
					if field_is_identifier:
						field_identity_dict[field_name] = field_value
			
			# Now see if the data in this row represents an already
			# existing model in the database.
			app_name = model_for_import.split(".")[0]
			specific_model_name = model_for_import.split('.')[-1]
			model = get_model(app_name, specific_model_name)
			
			# If the user specified some fields as identity fields, try
			# to use them to find duplicates.
			try:
				if len(field_identity_dict.keys()) > 0:
					# User specified some identity columns. Use them to
					# look for dupes for update.
					dupe_in_db = model.objects.get(**field_identity_dict)
				else:
					# User did NOT specify some identiy columns. Use the
					# entire list of field values to check for dups.
					dupe_in_db = model.objects.get(**field_value_dict)
				if update_dupes: # Probably superfluous in the second case.
					for key in field_value_dict.keys():
						setattr(dupe_in_db, key, field_value_dict[key])
					dupe_in_db.save()
					status_msg = 'spreadsheet row#' + str(row)+' successfully updated.'
					status_dict['num_items_updated'] = status_dict['num_items_updated'] + 1
					if show_successful_updates:
						status_dict['combined_results_messages'].append(status_msg)
					status_dict['update_results_messages'].append(status_msg)
					
			except ObjectDoesNotExist:
				# The object doesn't exist. Go ahead and add it.
				new_object = model(**field_value_dict)
				new_object.save()
				status_msg = 'spreadsheet row#' + str(row)+' successfully imported.'
				status_dict['num_items_imported'] = status_dict['num_items_imported'] + 1
				if show_successful_imports:
					status_dict['combined_results_messages'].append(status_msg)
				status_dict['import_results_messages'].append(status_msg)
		except:
			status_dict['num_errors'] = status_dict['num_errors'] + 1
			status_msg = 'spreadsheet row#' + str(row)+' ERROR: ' + `sys.exc_info()[1]`
			if show_errors:
				status_dict['combined_results_messages'].append(status_msg)
			status_dict['error_results_messages'].append(status_msg)
			if stop_on_first_error:
				break
			
	# Clean up...
	del request.session['save_file_name']
	del request.session['model_for_import']
	filepath = join(BATCH_IMPORT_TEMPFILE_LOCATION, save_file_name)
	if isfile(filepath):
		os.remove(filepath)

	# Render the response.
	return _render_results_response(request, status_dict, extra_context)


def _get_bound_field_dict(form):
	bound_field_dict = {}
	for key in form.field_dict.keys():
		bound_field_list = []
		field_list = form.field_dict[key]
		for field_name in field_list:
			bound_field = form[field_name]
			bound_field_list.append(bound_field)
		bound_field_dict[key] = bound_field_list
	return bound_field_dict

def _get_option_setting(request, option, default):
	try:
		return request.session[option]
	except:
		return default
	
def _instantiate_and_save_model(model, field_value_dict):
	# Validate the values being sent in and remove keyword
	# arguments where the values do not work.
	new_object = model(**field_value_dict)
	new_object.save()

def _render_results_response(request, status_dict, extra_context):
	if extra_context is None:
		extra_context = {}

	context = RequestContext(request)
	for key, value in extra_context.items():
		context[key] = callable(value) and value() or value

	return render_to_response(BATCH_IMPORT_RESULTS_TEMPLATE, status_dict, context_instance=context)
	