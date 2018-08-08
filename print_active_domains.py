#list_active_domains.py
import arcpy

#Set workspace environment to geodatabase
arcpy.env.workspace = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde"

#Get list of feature classes in geodatabase
FCs = arcpy.ListFeatureClasses()

#Loop through feature datasets and list all feature classes and there Active Domains 
for fds in arcpy.ListDatasets('','feature')+['']:
    for fc in arcpy.ListFeatureClasses('','',fds):
        for field in arcpy.ListFields(fc):
            if field.domain !="":
                #print "Feature Dataset: "+fds+"\nFeature Class: "+fc+"\nField Name: "+ field.name +"\nActive Domain: "+field.domain+"\n\n"
                print field.domain

#Loop through all feature classes not in a feature dataset and list active domains
for features in arcpy.ListFeatureClasses():
    for flds in arcpy.ListFields(features):
        if flds.domain !="":
            #print "Feature Class: "+features+"\nActive Domain: "+flds.domain+"\n"
            print flds.domain

#Loop through all tables and list active domains
            
for table in arcpy.ListTables():
    for f in arcpy.ListFields(table):
        if f.domain !="":
            #print "Table: "+table+"\nActive Domain: "+f.domain+"\n\n"
            print f.domain
        
