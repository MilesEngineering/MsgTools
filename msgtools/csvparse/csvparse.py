#!/usr/bin/env python3
import sys
#import argparse

def main(args=None):
    #parser = argparse.ArgumentParser(description="Tool to extract rows and columns from a CSV")
    if len(sys.argv) < 4:
        print("need to specify file name, row name, and column names")
        sys.exit(-1)
    file_name = sys.argv[1]
    row_name = sys.argv[2]
    col_names = sys.argv[3:]
    col_numbers = []
    
    first_line = True
    with open(file_name, 'r') as csv_file:
        lines = csv_file.read().splitlines()
        for line in lines:
            if row_name in line:
                cols = line.split(',')
                if row_name in cols[1]:
                    if first_line:
                        first_line = False
                        for col_name in col_names:
                            col_number = 0
                            for col in cols:
                                if col_name in col:
                                    if not col_number in col_numbers:
                                        col_numbers.append(col_number)
                                col_number+=1
                    output = [cols[0]]
                    for col_number in col_numbers:
                        output.append(cols[col_number])
                    print(','.join(output))
                        
            
    

# main starts here
if __name__ == '__main__':
    main()

#grep MotorStatus 20200117-093703_deploy.csv | cut -d, -f 1,29,41