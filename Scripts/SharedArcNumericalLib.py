# --------------------------------
# Name: SharedArcNumericalLib.py
# Purpose: This file serves as a function library for the ArcTime/ArcNumerical Toolboxes. Import as san. 
# Current Owner: David Wasserman
# Last Modified: 10/15/2017
# Copyright:   David Wasserman
# ArcGIS Version:   ArcGIS Pro/10.4
# Python Version:   3.5/2.7
# --------------------------------
# Copyright 2017 David J. Wasserman
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# --------------------------------

# Import Modules
import arcpy
import numpy as np
import os, re
import datetime

try:
    import pandas as pd
except:
    arcpy.AddError("This library requires Pandas installed in the ArcGIS Python Install."
                   " Might require installing pre-requisite libraries and software.")


# Function Definitions
def func_report(function=None, reportBool=False):
    """This decorator function is designed to be used as a wrapper with other functions to enable basic try and except
     reporting (if function fails it will report the name of the function that failed and its arguments. If a report
      boolean is true the function will report inputs and outputs of a function.-David Wasserman"""

    def func_report_decorator(function):
        def func_wrapper(*args, **kwargs):
            try:
                func_result = function(*args, **kwargs)
                if reportBool:
                    print("Function:{0}".format(str(function.__name__)))
                    print("     Input(s):{0}".format(str(args)))
                    print("     Ouput(s):{0}".format(str(func_result)))
                return func_result
            except Exception as e:
                print(
                    "{0} - function failed -|- Function arguments were:{1}.".format(str(function.__name__), str(args)))
                print(e.args[0])

        return func_wrapper

    if not function:  # User passed in a bool argument
        def waiting_for_function(function):
            return func_report_decorator(function)

        return waiting_for_function
    else:
        return func_report_decorator(function)


def arc_tool_report(function=None, arcToolMessageBool=False, arcProgressorBool=False):
    """This decorator function is designed to be used as a wrapper with other GIS functions to enable basic try and except
     reporting (if function fails it will report the name of the function that failed and its arguments. If a report
      boolean is true the function will report inputs and outputs of a function.-David Wasserman"""

    def arc_tool_report_decorator(function):
        def func_wrapper(*args, **kwargs):
            try:
                func_result = function(*args, **kwargs)
                if arcToolMessageBool:
                    arcpy.AddMessage("Function:{0}".format(str(function.__name__)))
                    arcpy.AddMessage("     Input(s):{0}".format(str(args)))
                    arcpy.AddMessage("     Ouput(s):{0}".format(str(func_result)))
                if arcProgressorBool:
                    arcpy.SetProgressorLabel("Function:{0}".format(str(function.__name__)))
                    arcpy.SetProgressorLabel("     Input(s):{0}".format(str(args)))
                    arcpy.SetProgressorLabel("     Ouput(s):{0}".format(str(func_result)))
                return func_result
            except Exception as e:
                arcpy.AddMessage(
                    "{0} - function failed -|- Function arguments were:{1}.".format(str(function.__name__),
                                                                                    str(args)))
                print(
                    "{0} - function failed -|- Function arguments were:{1}.".format(str(function.__name__), str(args)))
                print(e.args[0])

        return func_wrapper

    if not function:  # User passed in a bool argument
        def waiting_for_function(function):
            return arc_tool_report_decorator(function)

        return waiting_for_function
    else:
        return arc_tool_report_decorator(function)


@arc_tool_report
def arc_print(string, progressor_Bool=False):
    """ This function is used to simplify using arcpy reporting for tool creation,if progressor bool is true it will
    create a tool label."""
    casted_string = str(string)
    if progressor_Bool:
        arcpy.SetProgressorLabel(casted_string)
        arcpy.AddMessage(casted_string)
        print(casted_string)
    else:
        arcpy.AddMessage(casted_string)
        print(casted_string)


@arc_tool_report
def field_exist(featureclass, fieldname):
    """ArcFunction
     Check if a field in a feature class field exists and return true it does, false if not.- David Wasserman"""
    fieldList = arcpy.ListFields(featureclass, fieldname)
    fieldCount = len(fieldList)
    if (fieldCount >= 1) and fieldname.strip():  # If there is one or more of this field return true
        return True
    else:
        return False


@arc_tool_report
def add_new_field(in_table, field_name, field_type, field_precision="#", field_scale="#", field_length="#",
                  field_alias="#", field_is_nullable="#", field_is_required="#", field_domain="#"):
    """ArcFunction
    Add a new field if it currently does not exist. Add field alone is slower than checking first.- David Wasserman"""
    if field_exist(in_table, field_name):
        print(field_name + " Exists")
        arcpy.AddMessage(field_name + " Exists")
    else:
        print("Adding " + field_name)
        arcpy.AddMessage("Adding " + field_name)
        arcpy.AddField_management(in_table, field_name, field_type, field_precision, field_scale,
                                  field_length,
                                  field_alias,
                                  field_is_nullable, field_is_required, field_domain)


@arc_tool_report
def validate_df_names(dataframe, output_feature_class_workspace):
    """Returns pandas dataframe with all col names renamed to be valid arcgis table names."""
    new_name_list = []
    old_names = dataframe.columns.names
    for name in old_names:
        new_name = arcpy.ValidateFieldName(name, output_feature_class_workspace)
        new_name_list.append(new_name)
    rename_dict = {i: j for i, j in zip(old_names, new_name_list)}
    dataframe.rename(index=str, columns=rename_dict)
    return dataframe


@arc_tool_report
def arcgis_table_to_dataframe(in_fc, input_fields, query="", skip_nulls=False, null_values=None):
    """Function will convert an arcgis table into a pandas dataframe with an object ID index, and the selected
    input fields."""
    OIDFieldName = arcpy.Describe(in_fc).OIDFieldName
    final_fields = [OIDFieldName] + input_fields
    np_array = arcpy.da.TableToNumPyArray(in_fc, final_fields, query, skip_nulls, null_values)
    object_id_index = np_array[OIDFieldName]
    fc_dataframe = pd.DataFrame(np_array, index=object_id_index, columns=input_fields)
    return fc_dataframe


@arc_tool_report
def arc_unique_values(table, field, filter_falsy=False):
    """This function will return a list of unique values from a passed field. If the optional bool is true,
    this function will scrub out null/falsy values. """
    with arcpy.da.SearchCursor(table, [field]) as cursor:
        if filter_falsy:
            return sorted({row[0] for row in cursor if row[0]})
        else:
            return sorted({row[0] for row in cursor})


@arc_tool_report
def arc_unique_value_lists(in_feature_class, field_list, filter_falsy=False):
    """Function will returned a nested list of unique values for each field in the same order as the field list."""
    ordered_list = []
    len_list = []
    for field in field_list:
        unique_vals = arc_unique_values(in_feature_class, field, filter_falsy)
        len_list.append((len(unique_vals)))
        ordered_list.append(unique_vals)
    return ordered_list, len_list


@arc_tool_report
def construct_sql_equality_query(fieldName, value, dataSource, equalityOperator="=", noneEqualityOperator="is"):
    """Creates a workspace sensitive equality query to be used in arcpy/SQL statements. If the value is a string,
    quotes will be used for the query, otherwise they will be removed. Python 2-3 try except catch.(BaseString not in 3)
    David Wasserman"""
    try:  # Python 2
        if isinstance(value, (basestring, str)):
            return "{0} {1} '{2}'".format(arcpy.AddFieldDelimiters(dataSource, fieldName), equalityOperator, str(value))
        if value is None:
            return "{0} {1} {2}".format(arcpy.AddFieldDelimiters(dataSource, fieldName), noneEqualityOperator, "NULL")
        else:
            return "{0} {1} {2}".format(arcpy.AddFieldDelimiters(dataSource, fieldName), equalityOperator, str(value))
    except:  # Python 3
        if isinstance(value, (str)):  # Unicode only
            return "{0} {1} '{2}'".format(arcpy.AddFieldDelimiters(dataSource, fieldName), equalityOperator, str(value))
        if value is None:
            return "{0} {1} {2}".format(arcpy.AddFieldDelimiters(dataSource, fieldName), noneEqualityOperator, "NULL")
        else:
            return "{0} {1} {2}".format(arcpy.AddFieldDelimiters(dataSource, fieldName), equalityOperator, str(value))


@arc_tool_report
def get_duplicates(items):
    """Return a list of duplicates items found in a provided list/sequence."""
    seen_items = set()
    seen_add = seen_items.add
    seen_twice = set(field for field in items if field in seen_items or seen_add(field))
    return list(seen_twice)


@arc_tool_report
def generate_statistical_fieldmap(target_features, join_features, prepended_name="", merge_rule_dict={}):
    """Generates field map object based on passed field objects based on passed tables (list),
    input_field_objects (list), and passed statistics fields to choose for numeric and categorical variables. Output
    fields take the form of *merge rule*+*prepended_name*+*fieldname*"""
    field_mappings = arcpy.FieldMappings()
    # We want every field in 'target_features' and all fields in join_features that are present
    # in the field statistics mappping.
    field_mappings.addTable(target_features)
    for merge_rule in merge_rule_dict:
        for field in merge_rule_dict[merge_rule]:
            new_field_map = arcpy.FieldMap()
            new_field_map.addInputField(join_features, field)
            new_field_map.mergeRule = merge_rule
            out_field = new_field_map.outputField
            out_field.name = str(merge_rule) + str(prepended_name) + str(field)
            out_field.aliasName = str(merge_rule) + str(prepended_name) + str(field)
            new_field_map.outputField = out_field
            field_mappings.addFieldMap(new_field_map)
    return field_mappings


###########################
# ArcTime
###########################

@arc_tool_report
def round_down_by_value_if_not_target(value, alternative, target=None):
    """If value is not target (depending on parameters), return alternative."""
    if value is not target or value != target:
        return (alternative // value) * value
    else:
        return alternative


@arc_tool_report
def round_new_datetime(datetime_obj, year, month, day, hour, minute, second, microsecond=-1, original_dt_target=-1):
    """Will round a new date time to the year increment within an apply function based on the type of object present.
    The rounded date time will take the smallest unit not to be the dt_target, and make all units smaller 0 by integer
    dividing by a large number. Starts with asking for forgiveness rather than permission to get original object
    properties, then uses isinstance to the appropriate datetime object to return."""
    time_list = [year, month, day, hour, minute, second, microsecond]
    counter = 0
    index = 0
    for time in time_list:
        counter += 1
        if time != original_dt_target:
            index = counter
    if index == 0:
        pass
    elif index == 1:
        month, day, hour, minute, second, microsecond = 1000000, 1000000, 1000000, 1000000, 1000000, 1000000
    elif index == 2:
        day, hour, minute, second, microsecond = 1000000, 1000000, 1000000, 1000000, 1000000
    elif index == 3:
        hour, minute, second, microsecond = 1000000, 1000000, 1000000, 1000000
    elif index == 4:
        minute, second, microsecond = 1000000, 1000000, 1000000
    elif index == 5:
        second, microsecond = 1000000, 1000000
    elif index == 6:
        microsecond = 1000000
    else:
        pass
    try:
        new_year = round_down_by_value_if_not_target(year, datetime_obj.year, original_dt_target)
        new_month = round_down_by_value_if_not_target(month, datetime_obj.month, original_dt_target)
        new_day = round_down_by_value_if_not_target(day, datetime_obj.day, original_dt_target)
    except:
        pass
    try:
        new_hour = round_down_by_value_if_not_target(hour, datetime_obj.hour, original_dt_target)
        new_minute = round_down_by_value_if_not_target(minute, datetime_obj.minute, original_dt_target)
        new_second = round_down_by_value_if_not_target(second, datetime_obj.second, original_dt_target)
        new_microsecond = round_down_by_value_if_not_target(microsecond, datetime_obj.microsecond, original_dt_target)
    except:
        pass
    try:
        if isinstance(datetime_obj, datetime.datetime):
            return datetime.datetime(year=new_year, month=new_month, day=new_day, hour=new_hour, minute=new_minute,
                                     second=new_second, microsecond=new_microsecond)
        elif isinstance(datetime_obj, datetime.date):
            return datetime.date(year=new_year, month=new_month, day=new_day)
        elif isinstance(datetime_obj, datetime.time):
            return datetime.time(hour=new_hour, minute=new_minute, second=new_second, microsecond=new_microsecond)
        else:  # If it is something else,send back max datetime.
            return datetime.date.min
    except:
        return datetime.date.min


def get_min_max_from_field(table, field):
    """Get min and max value from input feature class/table."""
    with arcpy.da.SearchCursor(table, [field]) as cursor:
        data = [row[0] for row in cursor if row[0]]
        return min(data), max(data)


@arc_tool_report
def construct_time_bin_ranges(first_time, last_time, time_delta):
    temporal_counter = first_time
    total_time_range = last_time - first_time
    bin_count = int(np.ceil(total_time_range.total_seconds() / time_delta.total_seconds()))
    nested_time_bin_pairs = []
    for bin in range(bin_count):
        start_time = temporal_counter
        end_time = temporal_counter + time_delta
        nested_time_bin_pairs.append([start_time, end_time])
        temporal_counter = end_time
    return nested_time_bin_pairs


@arc_tool_report
def construct_sql_queries_from_time_bin(nested_time_bin_pairs, dataSource, start_time_field, end_time_field=None):
    """Takes in nested time bin pairs and constructed ESRI file formatted SQL queries to extract data between the
    two date time pairs of each bin. Returns a list of SQL queries based on the time bins. """
    if end_time_field is None:
        end_time_field = start_time_field
    QueryList = []
    time_format = "%Y-%m-%d %H:%M:%S"
    prepended_sql_time = "date "
    start_field = arcpy.AddFieldDelimiters(dataSource, start_time_field)
    end_field = arcpy.AddFieldDelimiters(dataSource, end_time_field)
    for bin in nested_time_bin_pairs:
        start_time = bin[0]
        end_time = bin[1]
        start_string = start_time.strftime(time_format)
        end_string = end_time.strftime(time_format)
        SQLQuery = "{0} >= {1} '{2}' AND {3} < {4} '{5}'".format(start_field, prepended_sql_time, start_string,
                                                                 end_field, prepended_sql_time, end_string)
        QueryList.append(SQLQuery)
    return QueryList


@arc_tool_report
def alphanumeric_split(time_string):
    """Splits an incoming string based on the first encounter of a alphabetic character after encountering digits.
     It will lower case and remove all white space in the string first, and return a number as float and alpha text
     as a string. """
    preprocessed_string = str(time_string).replace(" ", "").lower()
    string_list = [string for string in re.split(r'(\d+)', preprocessed_string) if string]
    number = float(string_list[0])
    string = str(string_list[1])
    return number, string


@arc_tool_report
def parse_time_units_to_dt(float_magnitude, time_units):
    """This function will take a string with time units and a float associated with it. It will return
    a delta time based on the float and the passed time units. So float is 1 and time_units is 'hour' then
    it returns a time delta object equal to 1 hour"""
    micro_search = re.compile(r"microsecond")
    milli_search = re.compile(r"millisecond")
    second_search = re.compile(r"second")
    minute_search = re.compile(r"minute")
    hour_search = re.compile(r"hour")
    day_search = re.compile(r"day")
    week_search = re.compile(r"week")
    microseconds = 0
    milliseconds = 0
    seconds = 0
    minutes = 0
    hours = 0
    days = 0
    weeks = 0
    if re.search(micro_search, str(time_units)):
        microseconds = float_magnitude
    if re.search(milli_search, str(time_units)):
        milliseconds = float_magnitude
    if re.search(second_search, str(time_units)):
        seconds = float_magnitude
    if re.search(minute_search, str(time_units)):
        minutes = float_magnitude
    if re.search(hour_search, str(time_units)):
        hours = float_magnitude
    if re.search(day_search, str(time_units)):
        days = float_magnitude
    if re.search(week_search, str(time_units)):
        weeks = float_magnitude
    return datetime.timedelta(days=days, seconds=seconds, microseconds=microseconds, minutes=minutes,
                              milliseconds=milliseconds, hours=hours, weeks=weeks)


@arc_tool_report
def create_unique_field_name(field_name, in_table):
    """This function will be used to create a unique field name for an ArcGIS field by adding a number to the end.
    If the file has field character limitations, the new field name will not be validated.- DJW."""
    counter = 1
    new_field_name = field_name
    while field_exist(in_table, new_field_name) and counter <= 1000:
        print(field_name + " Exists, creating new name with counter {0}".format(counter))
        new_field_name = "{0}_{1}".format(str(field_name), str(counter))
        counter += 1
    return new_field_name


@arc_tool_report
def constructUniqueStringID(values, delimiter="."):
    """Creates a unique string id based on delimited passed values. The function will strip the last/first
     delimiters added.-David Wasserman"""
    final_chained_id = ""
    for value in values:
        final_chained_id = "{0}{1}{2}".format(final_chained_id, str(delimiter), str(value))
        final_chained_id = final_chained_id
    final_chained_id = final_chained_id.strip("{0}".format(delimiter))
    return final_chained_id


def get_fields(featureClass, excludedTolkens=["OID", "Geometry"], excludedFields=["shape_area", "shape_length"]):
    try:
        fcName = os.path.split(featureClass)[1]
        field_list = [f.name for f in arcpy.ListFields(featureClass) if f.type not in excludedTolkens
                      and f.name.lower() not in excludedFields]
        arc_print("The field list for {0} is:{1}".format(str(fcName), str(field_list)), True)
        return field_list
    except:
        arc_print("Could not get fields for the following input {0}, returned an empty list.".format(str(featureClass)),
                  True)
        arcpy.AddWarning(
            "Could not get fields for the following input {0}, returned an empty list.".format(str(featureClass)))
        field_list = []
        return field_list


def join_record_dictionary(in_feature_class, join_dictionary, unique_id_field, join_fields_order):
    """Uses an arc update cursor to join fields to an input feature class. Inputs are a feature class, a
    join dictionary of form {unique_id_field:[ordered,join,field,list],the feature class join field, and the join fields
    in the same order as the lists in the join dictionary. """
    unique_id_list = join_dictionary.keys()
    cursor_fields = [unique_id_field] + join_fields_order
    feature_name = os.path.split(in_feature_class)[1]
    arc_print("Joining dictionary to input feature class {0}.".format(feature_name), True)
    with arcpy.da.UpdateCursor(in_feature_class, cursor_fields) as join_cursor:
        for row in join_cursor:
            if row[0] in unique_id_list:
                values = join_dictionary[row[0]]
                if len(values) != len(join_fields_order):
                    arcpy.AddError("Length of values in dictionary does not match join_fields_order.")
                value_index_list = enumerate(values, start=1)
                for index_value_pair in value_index_list:
                    try:
                        row[index_value_pair[0]] = index_value_pair[1]
                    except:
                        pass
            join_cursor.updateRow(row)


# End do_analysis function

# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE,
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':
    # Define input parameters
    print("Function library: ArcNumericalLib.py")