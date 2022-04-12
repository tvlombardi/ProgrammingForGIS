# -*- coding: utf-8 -*-

import os
import arcpy
from arcpy import env

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Project 1"
        self.alias = "Project 1 Toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [DailyEarthquakesPerState, QuakeEffectedElderly_CA]

class DailyEarthquakesPerState(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Daily Earthquakes per State Tool"
        self.description = '''This tool converts the USGS 30-day earthquake csv
            file to a point feature class. Earthquakes are queried to a
            user-defined date. The quakes the occurred on the user-defined date
            are counted and summarized within user-defined boundary polygons
            (ex. US States).'''
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = None

        # Input workspace folder
        in_wrksp = arcpy.Parameter(
            displayName="Workspace Folder",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        # Input csv earthquake data
        in_csv = arcpy.Parameter(
            displayName="USGS 30-day earthquake .csv Input",
            name="in_table",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")

        # User-defined date of interest
        in_date = arcpy.Parameter(
            displayName="Date of Interest Input",
            name="in_date",
            datatype="GPDate",
            parameterType="Required",
            direction="Input")

        # Input state boundary features
        in_fc = arcpy.Parameter(
            displayName="State Polygons Input",
            name="in_feature",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")

        # Output earthquake point locations from csv file
        out_fc = arcpy.Parameter(
            displayName="Earthquake Points Output",
            name="out_feature",
            datatype="DEFeatureClass",
            parameterType="Derived",
            direction="Output")

        # Output daily earthquake incidents on the user-defined date
        out_fc2 = arcpy.Parameter(
            displayName="Daily Quakes Output",
            name="out_feature2",
            datatype="DEFeatureClass",
            parameterType="Derived",
            direction="Output")

        # Output daily number of earthquake incidents per state
        out_fc3 = arcpy.Parameter(
            displayName="Daily Quakes per State Output",
            name="out_feature3",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")

        params = [in_wrksp, in_csv, in_date, in_fc, out_fc, out_fc2, out_fc3]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Set parameters as text for geoprocessing tool inputs and outputs.
        in_wrksp =parameters[0].valueAsText
        in_csv = parameters[1].valueAsText
        in_date = parameters[2].valueAsText
        in_fc = parameters[3].valueAsText
        out_fc = parameters[4].valueAsText
        out_fc2 = parameters[5].valueAsText
        out_fc3 = parameters[6].valueAsText

        # Create tool environmental settings.
        arcpy.env.overwriteOutput = True
        arcpy.env.scratchWorkspace = in_wrksp
        arcpy.AddMessage("Tool workspace: " + arcpy.env.scratchGDB)

        # Create derived output naming scheme.
        out_fc = arcpy.CreateUniqueName("AllQuakes", arcpy.env.scratchGDB)
        out_fc2 = arcpy.CreateUniqueName("DailyQuakes", arcpy.env.scratchGDB)

        # Execute XY Table To Point using the input parameters.
        arcpy.AddMessage("Processing earthquake locations...")
        arcpy.management.XYTableToPoint(
            in_table=in_csv,
            out_feature_class=out_fc,
            x_field="longitude",
            y_field="latitude")[0]
        arcpy.SetParameterAsText(4, out_fc)
        arcpy.AddMessage("30-day Quakes complete.")

        # Convert the "time" string (from the csv file) to a new date field.
        arcpy.AddMessage("Preparing to summarize data...")
        arcpy.management.ConvertTimeField(
            in_table=out_fc,
            input_time_field="time",
            input_time_format='''yyyy-MM-ddHH:mm:ss.s''',
            output_time_field="Date",
            output_time_type="DATE",
            output_time_format="yyyy-MM-dd")[0]

        # Select features with user-defined date attribute.
        where_clause = "out_fc.Date = Date'" + in_date + "'"
        out_fc = arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=out_fc,
            selection_type="NEW_SELECTION",
            where_clause=where_clause,
            invert_where_clause=None,)[0]

        # Copy the selected features to a new feature class.
        out_fc2 = arcpy.management.CopyFeatures(
            in_features=out_fc,
            out_feature_class=out_fc2,
            config_keyword=None,
            spatial_grid_1=None,
            spatial_grid_2=None,
            spatial_grid_3=None)[0]
        arcpy.SetParameterAsText(5, out_fc2)
        arcpy.AddMessage("Daily Quakes complete.")

        # Summarize daily quakes within state polygons to a new feature class.
        arcpy.AddMessage("Summarizing daily data...")
        out_fc3 = arcpy.SummarizeWithin_analysis(
            in_polygons=in_fc,
            in_sum_features=out_fc2,
            out_feature_class=out_fc3,
            keep_all_polygons="KEEP_ALL",
            sum_fields=None,
            sum_shape="ADD_SHAPE_SUM",
            shape_unit=None,
            group_field=None,
            add_min_maj="NO_MIN_MAJ",
            add_group_percent="NO_PERCENT",
            out_group_table=None)[0]
        arcpy.SetParameterAsText(6, out_fc3)

        # Delete superfluous fields from summarized attribute table.
        arcpy.AddMessage("Cleaning up daily quake data...")
        keep = [
            'STUSPS10',
            'NAME10',
            'Point_Count',
            'Shape_Area',
            'Shape_Length']
        discard = []
        for field in [f.name for f in arcpy.ListFields(out_fc3)
                      if f.type != 'OID' and f.type != 'Geometry']:
                if field not in keep:
                    discard.append(field)
        arcpy.DeleteField_management(out_fc3, discard)
        arcpy.AddMessage("Daily Quakes Per State completed.")
        return

class QuakeEffectedElderly_CA(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Quake Effected Elderly in CA"
        self.description = '''This tool converts the USGS 30-day earthquake csv
            file to a point feature class. State and county polygons are
            filtered down to California only. The quakes that occurred within
            the 30-day period are summarized within California's county boundary
             polygons and the total number counted. Fields are altered to
             deliver a new data table highlighting relevant census data and
             showing the effected elderly population.'''
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = None

        # Input workspace folder
        in_wrksp = arcpy.Parameter(
            displayName="Workspace Folder",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        # Input csv earthquake data
        in_csv = arcpy.Parameter(
            displayName="USGS 30-day earthquake .csv Input",
            name="in_table",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")

        # Input state boundary features
        in_fc = arcpy.Parameter(
            displayName="State Polygons Input",
            name="in_feature",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")

        # Input county boundary features
        in_fc2 = arcpy.Parameter(
            displayName="County Polygons Input",
            name="in_feature2",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")

        # Output earthquake point locations derived from csv file
        out_fc = arcpy.Parameter(
            displayName="Earthquake Points Output",
            name="out_feature",
            datatype="DEFeatureClass",
            parameterType="Derived",
            direction="Output")

        # Output California counties derived from census boundary polygons
        out_fc2 = arcpy.Parameter(
            displayName="CA counties",
            name="out_feature2",
            datatype="DEFeatureClass",
            parameterType="Derived",
            direction="Output")

        # Output quakes per CA county
        out_fc3 = arcpy.Parameter(
            displayName="Output Quakes per CA County",
            name="out_feature3",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")

        params = [in_wrksp, in_csv, in_fc, in_fc2, out_fc, out_fc2, out_fc3]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Set parameters as text for tool inputs.
        in_wrksp = parameters[0].valueAsText
        in_csv = parameters[1].valueAsText
        in_fc = parameters[2].valueAsText
        in_fc2 = parameters[3].valueAsText
        out_fc = parameters[4].valueAsText
        out_fc2 = parameters[5].valueAsText
        out_fc3 = parameters[6].valueAsText

        # Create tool environmental settings.
        arcpy.env.overwriteOutput = True
        arcpy.env.scratchWorkspace = in_wrksp
        arcpy.AddMessage("Tool workspace: " + arcpy.env.scratchGDB)

        # Create derived output naming scheme.
        out_fc = arcpy.CreateUniqueName("AllQuakes", arcpy.env.scratchGDB)
        out_fc2 = arcpy.CreateUniqueName("CA_counties", arcpy.env.scratchGDB)

        # Execute XY Table To Point using the input parameters.
        arcpy.AddMessage("Processing earthquake locations...")
        arcpy.management.XYTableToPoint(
            in_table=in_csv,
            out_feature_class=out_fc,
            x_field="longitude",
            y_field="latitude")[0]
        arcpy.SetParameterAsText(4, out_fc)
        arcpy.AddMessage("30-day Quakes complete.")

        # Select county polygons within California for filtering quake data.
        arcpy.AddMessage("Processing county data...")
        in_fc = arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=in_fc,
            selection_type="NEW_SELECTION",
            where_clause="STUSPS10 = 'CA'",
            invert_where_clause=None,)[0]

        in_fc2 = arcpy.management.SelectLayerByLocation(
            in_layer=in_fc2,
            overlap_type="WITHIN",
            select_features=in_fc,
            search_distance=None,
            selection_type="NEW_SELECTION",
            invert_spatial_relationship="NOT_INVERT")[0]

        # Copy the selected features to a new feature class.
        out_fc2 = arcpy.management.CopyFeatures(
            in_features=in_fc2,
            out_feature_class=out_fc2,
            config_keyword=None,
            spatial_grid_1=None,
            spatial_grid_2=None,
            spatial_grid_3=None)[0]
        arcpy.SetParameterAsText(5, out_fc2)
        arcpy.AddMessage("CA counties complete.")

        # Summarize 30-day quakes within county polygons to a new feature class.
        arcpy.AddMessage("Summarizing quakes per CA county...")
        out_fc3 = arcpy.SummarizeWithin_analysis(
            in_polygons=out_fc2,
            in_sum_features=out_fc,
            out_feature_class=out_fc3,
            keep_all_polygons="KEEP_ALL",
            sum_fields=None,
            sum_shape="ADD_SHAPE_SUM",
            shape_unit=None,
            group_field=None,
            add_min_maj="NO_MIN_MAJ",
            add_group_percent="NO_PERCENT",
            out_group_table=None)[0]
        arcpy.SetParameterAsText(6, out_fc3)

        # Delete superfluous fields from summarized attribute table.
        arcpy.AddMessage("Cleaning up quakes per CA county...")
        keep = [
            'NAMELSAD10',
            'DP0070001',
            'DP0070002',
            'DP0070003',
            'DP0120009',
            'DP0120012',
            'DP0130013',
            'DP0130015',
            'DP0150001',
            'Point_Count',
            'Shape_Area',
            'Shape_Length']
        discard = []
        for field in [f.name for f in arcpy.ListFields(out_fc3)
                      if f.type != 'OID' and f.type != 'Geometry']:
                if field not in keep:
                    discard.append(field)
        arcpy.DeleteField_management(out_fc3, discard)

        # Alter relevant data field names/aliases to have more meaningful names.
        fields = [
            ('DP0070001', 'TotalPop65_Yrs'),
            ('DP0070002', 'TotalMale65_Yrs'),
            ('DP0070003', 'TotalFemale65_Yrs'),
            ('DP0120009', 'HholdWith65_Related'),
            ('DP0120012', 'HholdWith65_NonRelated'),
            ('DP0150001', 'TotalHholdWith65_Yrs'),
            ('DP0130013', 'HholdsMale65_Alone'),
            ('DP0130015', 'HholdsFemale65_Alone'),
            ('Point_Count', 'QuakesPerCounty_Count')]
        for fld in fields:
            arcpy.management.AlterField(
                in_table=out_fc3,
                field=fld[0],
                new_field_name=fld[1],
                new_field_alias=fld[1])
        arcpy.AddMessage("Quakes per CA county completed.")

        return
