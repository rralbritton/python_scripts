#Reports.py
#Author: Rachel Albritton
#Date Created: 10/19/2012
#Useage: Provides two different reports in a .txt file format; an overall summary of selected conservation areas
#and a detailed report about each potential conservation area that was selected.
"-------------------------------------------------------------"


import arcpy, os

arcpy.env.workspace = "C:/GIS540_Project/OutputData"
arcpy.env.overwriteOutput = True

def outName(input,post="_Output"):
    """Returns output name."""
    outName=os.path.basename(input).split(".")[0]+post
    return outName

inputfile="C:/GIS540_Project/OutputData/ReportSummary.txt" 

try:
    infile = open(inputfile,'w')
    infile.write ("REPORT SUMMARY\n\n")
    infile.write("Potential Conservation Areas (PCA's) that intersected with the following counties were selected: ")
    Counties = "SBR_NC_Counties_selected.shp"
    sc = arcpy.SearchCursor(Counties)
    for line in sc:
        infile.write('\n'+(str(line.CO_NAME))+" County")
    del line
    del sc
except:
    print "An error occured while writing", os.path.basename(inputfile)
    infile.close()
    if line:
        del line
    if sc:
        del sc

#Overall summary report
#Get total number of potential areas selected area

try:
    pca_selected = "C:/GIS540_Project/OutputData/SBR_NC_pca_Selected.shp"
    count = int(arcpy.GetCount_management(pca_selected).getOutput(0))
    infile.write ("\n\nPotential Conservation Areas\n-------------------\nTotal number of PCA areas selected:  ")
    infile.write (arcpy.GetCount_management(pca_selected).getOutput(0))
except:
    infile.close()
    print "An error occured getting the total number of PCAs selected"'\n'
    print arcpy.GetMessages()
    
#total acreage of selected PCA areas
    
try:
    out_table = outName(pca_selected,"_TABLEsum.dbf")
    field = [["Acres","SUM"]]
    arcpy.Statistics_analysis(pca_selected,out_table,field)

except:
    print arcpy.GetMessages()

try:
    sc = arcpy.SearchCursor(out_table)
    row = sc.next()
    infile.write ("\nTotal PCA acreage:  ")
    infile.write(str(row.getValue("SUM_Acres")))
    del row
    del sc
except:
    print "An error occured writing PCA acreage summary"
    infile.close()
    if row:
        del row
    if sc:
        del sc

#Acreage by GAP Status

infile.write("\n\nAcreage by GAP Status\n---------------------------")

try:
    intable = "C:/GIS540_Project/OutputData/gapstatus_clip.shp"
    GAP_Table = outName(intable,"_TABLEsum.dbf")
    gapstat = [["Acres","SUM"]]
    gapcase = ["GAPSTAT"]
    arcpy.Statistics_analysis(intable,GAP_Table,gapstat,gapcase)
except:
    print arcpy.GetMessages()
    infile.close()
    
try:
    sc=arcpy.SearchCursor(GAP_Table)
    row = sc.next()
    for row in sc:
        infile.write("\nTotal acreage designated as GAP ")
        infile.write(str(row.getValue("GAPSTAT")))
        infile.write(": ")
        infile.write(str(row.getValue("SUM_Acres")))
    del row
    del sc
except:
    infile.close()
    print "An error occured"
    if row:
        del row
    if sc:
        del sc
        
#Acreage by Management Entity         

infile.write("\n\nAcreage by Management Entity\n----------------------------")
try:
    MGMT_intable = "C:/GIS540_Project/OutputData/ownership_clip.shp"
    MGMT_outtable = outName(MGMT_intable,"_TABLEsum.dbf")
    mgmtstat = [["Acres","SUM"]]
    mgmtcase = ["OWNER_CAT"]
    arcpy.Statistics_analysis(MGMT_intable,MGMT_outtable,mgmtstat,mgmtcase)
except:
    arcpy.GetMessages()

try:
    sc=arcpy.SearchCursor(MGMT_outtable)
    row = sc.next()
    for row in sc:
        infile.write("\nTotal acreage under ")
        infile.write(str(row.getValue("OWNER_CAT"))) #name of management entity
        infile.write(" ownership: ")
        infile.write(str(row.getValue("SUM_Acres")))#acreage
    del row
    del sc
except:
    infile.close()
    print "An error occured writing ownership summary"
    if row:
        del row
    if sc:
        del sc

#Acreage by Land Cover Type
infile.write("\n\nAcreage by Land Cover Type\n-----------------------------------")
try:
    LC_intable = "C:/GIS540_Project/OutputData/nlcd06p_clip.shp"
    LC_outtable = outName(LC_intable,"_TABLEsum.dbf")
    lcstat = [["Acres","SUM"]]
    lccase =["TYPE"]
    arcpy.Statistics_analysis(LC_intable, LC_outtable,lcstat,lccase)
except:
    print arcpy.GetMessages()

#Write Landcover Summary statistics to textfile
try:
    sc = arcpy.SearchCursor(LC_outtable)
    row = sc.next()
    for row in sc:
        infile.write("\nTotal acreage of ")
        infile.write(str(row.getValue("TYPE")))#land cover type
        infile.write(" landcover: ")
        infile.write(str(row.getValue("SUM_Acres"))) #acreage of each land cover type
    del row
    del sc
except:
    infile.close()
    print "An error occured writing land cover summary"
    if row:
        del row
    if sc:
        del sc
               
#Measures of Central Tendency for Species Richness
infile.write ("\n\nSpecies Richness Summary for selected PCA's\n--------------------------------------")
try:
    SR_intable = "C:/GIS540_Project/OutputData/gap_richnessp_clip.shp"
    SR_outtable = outName(SR_intable,"_TABLEsum.dbf")
    srstat = [["GRIDCODE","RANGE"],["GRIDCODE", "MEAN"]]
    arcpy.Statistics_analysis(SR_intable,SR_outtable,srstat)
except:
    print arcpy.GetMessages()
    
#Write Species Richness summary to text file

try:
    sc = arcpy.SearchCursor(SR_outtable)
    row = sc.next
    for row in sc:
        infile.write("\nSpecies richness RANGE in selected PCA areas: ")
        infile.write(str(row.getValue("RANGE_GRID")))
        infile.write("\nSpecies richness MEAN in selected PCA areas: ")
        infile.write(str(row.getValue("MEAN_GRIDC")))

except:
    infile.close()
    print "An error occured while writing species richness summary report"
    print arcpy.GetMessages()

#Statistics on miles and density of classified maintenace level 1 & 2 Forest Service Roads
infile.write("\n\nMiles and Density of Classified Maintenace Level 1 & 2 Forest Service Roads\n----------------------------------------------------")

try:
    FR_intable = pca_selected
    FR_outtable = "FR12_TABLEsum.dbf"
    frstat = [["FR12_Miles","SUM"],["FR12_densi","SUM"]]
    arcpy.Statistics_analysis(FR_intable,FR_outtable,frstat)

except:
    print arcpy.GetMessages()

#Print FR 1 & 2 summary statistics to summary report
try:
    sc = arcpy.SearchCursor(FR_outtable)
    row = sc.next
    for row in sc:
        infile.write("\nMileage of classified maintenance level 1 &2 Forest Service Roads within selected PCA's: ")
        infile.write(str(row.getValue("SUM_FR12_M")))
        infile.write("\nDensity (miles per sq.mile) of classified maintenace level 1 & 2 Forest Service Roads within selected PCA's: ")
        infile.write(str(row.getValue("SUM_FR12_d")))
except:
    infile.close()
    print "An error occured while trying to write FR 1&2 statistics to summary report",'\n'
    print arcpy.GetMessages()
    
infile.close()
print "Summary report created and stored in",arcpy.env.workspace
    