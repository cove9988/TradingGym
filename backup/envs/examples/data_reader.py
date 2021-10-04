import os
import csv
filename = r'C:\paulwork\_tx\txgym\examples\ue_2.csv'
four_in_line = False
capped = 10000
destfile = r'C:\paulwork\_tx\txgym\examples\usdeur.csv'
with open(filename,'r') as csvfile, open(destfile,'w') as nw :
    reader = csv.reader(csvfile)
    joinline =''
    for n, row in enumerate(reader):
        li = row[1] + ',' + row[2]
        if four_in_line:
            if n % 2 == 1:
                joinline += ',' + li + '\n'
                nw.write(joinline)
            else: 
                joinline = li
        else:
            joinline +=  li + '\n'
            nw.write(joinline)

        if n > capped:
            break;
print('done')