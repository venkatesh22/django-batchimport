# NEW STUFF #

I've updated this code with others help to be dramatically simpler. Check out the latest code **excel\_test.zip**. This is a total overhaul (and DRAMATIC simplification of the previous version of this code). Please use it instead. The docs below are for the old version which is still available and I've not yet documented the new library/sample project satifactorily but it is VERY straightforward.

Best,
Keyton




---


# DOCS FOR 0.2 (OLD) VERSION: #

# Introduction #

Django -- either through the admin interface or through custom forms -- makes insertion of new single items one-at-a-time into your database easy. However, this becomes tedious when you have multiple entries to make.

And while fixtures makes this process easy for web application administrators and testers, end users are usually left to struggle unless the system's developer builds a custom batch import process that requires data to be uploaded in a specific domain-specific format.

Also, while Python and Django make building bulk import processes relatively straightforward, it is often left to do for later, forcing your first to users bear the brunt of the single-item-at-a-time entry pain.

The django-batchimport reusable application aims to help with this process. It allows you to provide your users with a way to select a model for import, upload an Excel file containing multiple instances of your data (multiple Poll objects, for example) and then either have the system "guess" which column in your spreadsheet goes to which field in your model or have the user select the mapping of column to field, including support for foreign keys.

Internally it uses John Machin's xlrd library to read Microsoft Excel files. Read about it http://www.lexicon.net/sjmachin/xlrd.htm

Finally, it optionally allows for batch update using the same process.

# How Does It Work? #
The django-batchadmin app can be added to any existing django project. See installation below for more details but simply stated, once you have the prerequisites in place, all you need to do is drop the app into your project, drop the templates (yours or my examples) into a template folder suitable for your app, and wire up the urls.py for batchimport (assuming you like how I have it).

Once added, the main work is performed by its three main views:
## import\_start ##
The first view retrieves a list of all the models in your application (or you can specify exactly which models you want supported in a simple settings option -- more on that in a moment). It does this using django's introspection mechanics and reflection.

This list is used as part of a form which is then presented to the end user as shown below:
![http://django-batchimport.googlecode.com/files/object_data_import_start.png](http://django-batchimport.googlecode.com/files/object_data_import_start.png)
Look for the red numbers in the image above:

1. This is a list of models django-batchimport retrieved from your project (or your setting).

2. This is a simple file field to allow you to upload an XLS file.


The user selects the model he/she wishes to use for this upload, browses to the file and submits the form.


## import\_options: object data ##
Once the model and file are accepted, the import\_options view does a fair amount more stuff which can be shown easier than it can be described. See the screenshot of the template below:

![http://django-batchimport.googlecode.com/files/object_data_import_options.png](http://django-batchimport.googlecode.com/files/object_data_import_options.png)

Again, look at the red numbers above to follow along:

3. **Field Name** For the model selected, the django\_options view will reflect and get a list of fields for that model. This list is dynamically created. Fields that are required have an asterisk appended to the end of the name. (NOTE: By default any field for which you've set _editable=False_ in your models file is NOT shown here. However, you can override this behavior using the **BATCH\_IMPORT\_UNEDITABLE\_FIELDS** setting. See [BatchImportSettings](BatchImportSettings.md) for more information.)

4. **Spreadsheet Column** For each model field, the user can select one column from the excel spreadsheet. If any model field's name matches the name in the spreadsheet column (case-insensitive) the match is made for you. The view goes ahead and gets the first row (assumed to be a header row but could be just a row of sample data) and dynamically creates a choice list for each field. This is how the user can specify which column in each spreadsheet row goes to which model field. (NOTE: If any column header in your spreadsheet matches the name of your model's field name (case insensitive), that column is auto-selected.)

5. **Is Identity** What if your spreadsheet contains rows that represent data you've previously imported (a School you've already got in your database from a previous import, for example)?

Based on the setting **BATCH\_IMPORT\_UPDATE\_DUPS** (See [BatchImportSettings](BatchImportSettings.md) for more information.), you can have django-batchimport update the item in the database or simply ignore it -- **IF** it's a duplicate. But how does the system determine if it's a duplicate -- especially if you have no unique identifier in your excel spreadsheet?

The **Is Identity** checkbox allows you to specify WHICH fields to use to look in the database for duplicates. It starts out as ALL checked. In this case, every value in the spreadsheet row must match every field in the model in the database to be considered a duplicate (in which case, an update won't do anything). But the user can UNCHECK some of these items. The system will use the values from the checked spreadsheet columns to check this row against the database. If there is a match, then the system either ignores the row or tries to update the underlying object as specified by **BATCH\_IMPORT\_UPDATE\_DUPS**.

6. **Default Value** For each field, the user can also specify a default value just in case there is no value in the spreadsheet column for a given row.

7. **Mapping Field** But what if the field represents a related object (_ManyToMany_, _OneToOne_, etc)? The view goes ahead and gets a list of fields for that related model as well and provides a list of fields. The user specifies which field to use to FIND the related object.

For example, suppose I have schools and students in my project. Each student has a reference to his/her school. I upload my school data. Now I want to upload my student data. Each student is associated via its model to a school. My spreadsheet just has the school name. So I specify the **name** field on the Relationship option drop-down. When it starts to process my spreadsheet, django-batchimport will get the value from this spreadsheet column and use it to find a School object using the School's **name** field.

8. These are the available django-batchimport options. Here I have them exposed to the user but you could just as easily set them yourself in your settings (more on settings below). The app allows for defaults on these as well, obviously.


## import\_options: relationship data ##

When uploading a spreadsheet representing relationship data, the options are a little different:

![http://django-batchimport.googlecode.com/files/relationship_import_options.png](http://django-batchimport.googlecode.com/files/relationship_import_options.png)

1. The instructions are specific to import of relationship data. Note that you may want to customize this to your business case should you expose this functionality to end users.

2. For each model in the relationship, there is a section of options. Each is labeled at the top. In the above example, the first model is the Parent model.

3. As with import of object data, each field for each model is listed down the left.

4. Again as with import of object data, there is a drop-down of available spreadsheet columns to map to each field. You do NOT have to select a column for every field -- just those designated as identity fields.

5. Each row represents data for TWO models. The Is Identity column on the options screen for import of relationship data tells the system which fields to use to determine which pre-existing objects (one for each model) this row represents. You have to specify at least one identity column/field for each model. You can choose them all if your spreadsheet data supports it.

## import\_execute ##
Once the user has submitted the options form, the app goes to a "processing, please wait..." page:
![http://django-batchimport.googlecode.com/files/object_data_import_processing.png](http://django-batchimport.googlecode.com/files/object_data_import_processing.png)

This page is quickly redirected to the **import\_execute**. (This should be asynchronous and reload the page on a given interval etc, but I've not gotten to it yet. For right now this whole thing is a synchronous process -- see Caveats/Excuses below).

The **import\_execute** view iterates over each row in the uploaded spreadsheet, figures out the appropriate field values from the mapped row values (including getting related objects as needed), and then uses these values to either update an existing or insert a new item in the database for the given model.

As the app is doing this, it gathers various results variables and uses it in the final template for results:
![http://django-batchimport.googlecode.com/files/object_data_import_results.png](http://django-batchimport.googlecode.com/files/object_data_import_results.png)

9. The name of the model is supplied so you can see what type of model these results are for.

10. Various summary variables are included for your template.

11-12. There are four lists which you can show (I show them all in the sample template). The first is a row-by-row accounting of all that's happened (so long as you specified to show all the possible outcomes in your settings). The others are exclusive to imports, updates, or errors, respectively.

Thanks for downloading django-batchimport.

## INSTALLATION ##
1. Ensure that you have Python 2.5+ installed.
See http://www.python.org for more information.

2. Ensure that you have Django 1.0+ installed.
See http://docs.djangoproject.com/en/dev/topics/install/ for more
information.

3. Install xlrd.
See http://www.lexicon.net/sjmachin/xlrd.htm for more
information.

4. In the same folder where you found this file is a sample\_project folder.
Navigate to it.

5. Run syncdb (adding admin user):
> python manage.py syncdb

6. Start your django app:
> python manage.py runserver



## TESTING ##
1. Navigate to http://localhost:8000/batchimport/import_start/

2. Pick School from the model drop-down.

3. Browse to the sample\_data folder (in the same folder you found this
document). Select the sample\_school\_data.xls file. Click Submit.

4. Leave the options alone for now. Select appropriate mappings from the
spreadsheet drop downs for each of the model fields. You shouldn't have to
select anything for the school data. Click submit.

5. Wait some time (longer on Windows machines for some reason).

6. See the results of your batch import.

7. Go back to http://localhost:8000/batchimport/import_start/

8. Repeat steps 11-16 for Parents (sample\_parents.xls) and
Students (sample\_students.xls).

9. Navigate to http://localhost:8000/batchimport/import_start/

10. Pick Mapping: Student-Parent from the model drop-down.

11. Browse to the sample\_data folder (in the same folder you found this
document). Select the sample\_student\_to\_parent.xls file. Click Submit.

12. Select the following options:
Parent:
-first\_name: Pick ParentGivenName from the spreadsheet column dropdown.
-last\_name: Pick ParentSurname from the spreadsheet column dropdown.
-email: Pick ParentEmailAddress from the spreadsheet column dropdown.
Student:
-first\_name: Pick StudentGivenName from the spreadsheet column dropdown.
-last\_name: Pick StudentSurname from the spreadsheet column dropdown.
-dob: Pick StudentBirthday from the spreadsheet column dropdown.

13. Click submit.

14. Wait some time (longer on Windows machines for some reason).

15. See the results of your batch import.

16. Go to http://localhost:8000/admin/ and log in.

17. Check out the Schools, Parents, and Students you just imported.
NOTE: The last names of the parents do NOT match the last names
of the students (sorry. was too lazy).


# Templates #
I've included two versions of four sample templates:
  * _start.html:_ This is the first screen prompting for model and Excel file.

  * _options.html:_ This shows the layout of all recognized options, including those dynamically defined by the app itself upon inspection of your spreadsheet and selected model.

  * _processing.html:_ Something for your users to see while the work is happening.

  * _results.html:_ Shows all possible results variables.

There are two versions of each of the above templates. One is for use with Pinax-based apps and one is for standalone. The standalone versions are used in the sample\_project.

NOTE: Each of the above templates can be overridden using the following settings:
BATCH\_IMPORT\_START\_TEMPLATE
BATCH\_IMPORT\_OPTIONS\_TEMPLATE
BATCH\_IMPORT\_EXECUTE\_TEMPLATE
BATCH\_IMPORT\_RESULTS\_TEMPLATE

# Caveats/Excuses #
I'm new to django and don't know all that much python. I am 100% sure that I've done LOTS of things the "brute force" way. PLEASE PLEASE PLEASE (gently) let me know if you see stuff that I've missed or just completely botched due to limited experience. ;-)

Along those lines, if you yourself are new to Django, please look at James Bennett's django-registration project or Pinax for how it "should be done" -- i.e. **not here!** ;-)

My use case doesn't need this process to be fast or even particularly scalable. A few hundred rows are all my users will ever need to import. In testing it's "pretty fast" on my main Ubuntu-based linux box but on my Windows XP machine it's SLOW. I'm sure that this is fixable but I've not fixed it yet.

I've tried to follow James Bennett's suggestions in making this as reusable as possible, but I'm sure I've messed that up here and there.

Please tweak/customize and share this app and share it back to the community.

# Thanks #
Thanks very much to everyone in the django community that has made this platform a joy. Special thanks to James Bennett and James Tauber for their especially vigorous efforts in teaching the meaning of "reuse."