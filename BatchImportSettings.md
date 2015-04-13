# Customizable Settings for django-batchimport #
You can set one or more of the following settings in your django project's settings.py file to override the default behavior of django-batchimport.

**BATCH\_IMPORT\_START\_TEMPLATE**<br />
**BATCH\_IMPORT\_OPTIONS\_TEMPLATE**<br />
**BATCH\_IMPORT\_EXECUTE\_TEMPLATE**<br />
**BATCH\_IMPORT\_RESULTS\_TEMPLATE**<br />
Template settings. The following settings can be set to point to a template to override the default template used (if you don't want to just edit the defaults):

**BATCH\_IMPORT\_IMPORTABLE\_MODELS**<br />
Specify the list of models in your application which are importable in batch. If you do not provide a list, the system will use introspection to get a list of ALL models in your application (via INSTALLED\_APPS).

**BATCH\_IMPORT\_TEMPFILE\_LOCATION**<br />
Specify where the uploaded Microsoft Excel file will be saved to the system.
NOTE: This must be a absolute path.
NOTE: Django must have read/write access to this location.

**BATCH\_IMPORT\_UNEDITABLE\_FIELDS**<br />
By default, the system does not allow you to import data for fields that are not EDITABLE (i.e. in their model field declarations, you've set editable=False). You can override this behavior here.

**BATCH\_IMPORT\_VALUE\_OVERRIDES**<br />
Sometimes you will want to override the value coming in from the XLS file with a constant or a dynamically generated value. The following setting is a dictionary of values (or callables) per each fully specified model field.
NOTE: You must import the item into your settings file if it is a callable.

**BATCH\_IMPORT\_SHOW\_SUCCESSFUL\_IMPORTS**<br />
**BATCH\_IMPORT\_SHOW\_SUCCESSFUL\_UPDATES**<br />
**BATCH\_IMPORT\_SHOW\_ERRORS**<br />
The system can show you individual imports, updates, or errors individually using the following boolean options.
Note that True is assumed for all three if no setting is present.

**BATCH\_IMPORT\_STOP\_ON\_FIRST\_ERROR**<br />
Whether the system should stop on the first error or process the entire uploaded spreadsheet and show errors afterwards.

**BATCH\_IMPORT\_UPDATE\_DUPS**<br />
Whether or not to update duplicates or simply ignore them. Note that duplicates are determined based on the user's specification of model fields as identification fields. If these are not set, a duplicate must match at all column/fields.

**BATCH\_IMPORT\_START\_ROW**<br />
**BATCH\_IMPORT\_END\_ROW**<br />
If no options are set for start/end row, defaults are used that assume (1) the spreadsheet has a header row (indicating that data starts on row #2 and (2) the entire spreadsheet is to be processed.