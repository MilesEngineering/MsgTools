#!/usr/bin/env python3
import sys
#import argparse

class RowInfo:
    def __init__(self, arg):
        row_info = arg.split('=')
        self.row_name = row_info[0]
        self.col_names = row_info[1].split(',')
        self.col_numbers = []
        self.col_number_offsets = {}
        for i in range(len(self.col_names)):
            name = self.col_names[i]
            if '+' in name:
                parts = self.col_names[i].split("+")
                self.col_names[i] = parts[0]
                self.col_number_offsets[self.col_names[i]] = int(parts[1])
                
        self.first_line = True

    def ProcessData(self, line):
        if self.row_name in line:
            cols = line.split(',')
            if self.row_name in cols[1]:
                # normal row (offsets included)
                output = [cols[0], cols[1]]
                if self.first_line:
                    self.first_line = False
                    for col_name in self.col_names:
                        col_number = 0
                        for col in cols:
                            if col_name in col:
                                output.append(col)
                                if not col_number in self.col_numbers:
                                    value = col_number
                                    if col_name in self.col_number_offsets:
                                        value += self.col_number_offsets[col_name]
                                    self.col_numbers.append(value)
                            col_number+=1
                else:
                    for col_number in self.col_numbers:
                        output.append(cols[col_number])
                return ','.join(output)
        return None
        

def main(args=None):
    #parser = argparse.ArgumentParser(description="Tool to extract rows and columns from a CSV")
    if len(sys.argv) < 3:
        print("Like this:")
        print(sys.argv[0] + ' MsgName1=Field1,Field[+1] MsgName2=FieldA,FieldB[+2]')
        sys.exit(-1)
    file_name = sys.argv[1]
    row_infos = []
    for arg in sys.argv[2:]:
        row_infos.append(RowInfo(arg))
    
    with open(file_name, 'r') as csv_file:
        lines = csv_file.read().splitlines()
        for line in lines:
            for r in row_infos:
                output = r.ProcessData(line)
                if output:
                    print(output)
                        
            
    

# main starts here
if __name__ == '__main__':
    main()

#grep MotorStatus 20200117-093703_deploy.csv | cut -d, -f 1,29,41