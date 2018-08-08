import csv, sys, itertools, os
from os import listdir
from collections import defaultdict

def find_csv_filenames( path_to_dir, suffix=".csv" ):
    filenames = listdir(path_to_dir)
    return [ filename for filename in filenames if filename.endswith( suffix ) ]

fileDirectory = r"C:/Temp/CSVReports/"
outFile = r"C:/Temp/CSVReports/MergeFileTest.csv"

#Get list of header names
headerFile = fileDirectory+find_csv_filenames(fileDirectory)[0]
with open(headerFile, "rb") as f:
    reader = csv.reader(f)
    header = reader.next()
    rest = [row for row in reader]

#print header

header_saved = False
with open(outFile,'wb') as fout:
    for files in "C:/Temp/CSVReports/":
        #print files
        with open (os.path.relpath(files)) as fin:
            header = next(fin)
            if not header_saved:
                fout.write(header)
                header_saved = True
            for line in fin:
                fout.write(line)

##for files in fileDirectory:
##    with open(outfile, 'w') as f_out:
##        dict_writer = None
##        for files in "C:/Temp/CSVReports/":
##            with open(files, 'r') as f_in:
##                dict_reader = csv.DictReader(f_in)
##                if not dict_writer:
##                    dict_writer = csv.DictWriter(f_out, lineterminator='\n', fieldnames=dict_reader.fieldnames)
##                    dict_writer.writeheader()
    ##            for row in dict_reader:
    ##                if row['Campaign'] in campaign_names:
    ##                    dict_writer.writerow(row)
