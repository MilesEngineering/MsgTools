#!/usr/bin/env python3
import sys
#import argparse

class RowInfo:
    def __init__(self, arg):
        row_info = arg.split('=')
        self.row_name = row_info[0]
        self.col_search_strings = row_info[1].split(',')
        self.col_numbers = []
        self.col_number_offsets = {}
        for i in range(len(self.col_search_strings)):
            name = self.col_search_strings[i]
            if '+' in name:
                parts = self.col_search_strings[i].split("+")
                self.col_search_strings[i] = parts[0]
                self.col_number_offsets[self.col_search_strings[i]] = int(parts[1])
                
        self.got_header = False
        self.column_names = []
    
    def ColumnCount(self):
        return len(self.col_search_strings)
    
    def GotHeader(self):
        return self.got_header

    def ProcessData(self, line, blank_columns=0):
        if self.row_name in line:
            cols = line.split(',')
            if self.row_name in cols[1]:
                if self.got_header:
                    output = [cols[0], cols[1]] + [''] * blank_columns
                    # normal row
                    for col_number in self.col_numbers:
                        output.append(cols[col_number])
                    return ','.join(output)
                else:
                    # header row
                    self.got_header = True
                    for col_name in self.col_search_strings:
                        col_number = 0
                        for col in cols:
                            if col_name in col:
                                if not col_number in self.col_numbers:
                                    self.column_names.append(col)
                                    value = col_number
                                    if col_name in self.col_number_offsets:
                                        value += self.col_number_offsets[col_name]
                                    self.col_numbers.append(value)
                            col_number+=1
        return None
        

def GotAllHeaders(row_infos):
    ret = True
    for r in row_infos:
        if not r.GotHeader():
            ret = False
    return ret

def PrintHeader(row_infos):
    ret = ["Time","MessageName"]
    for r in row_infos:
        ret += r.column_names
    return ','.join(ret)
    
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
    
    got_all_headers = False
    output = ""
    with open(file_name, 'r') as csv_file:
        lines = csv_file.read().splitlines()
        for line in lines:
            blank_columns = 0
            for r in row_infos:
                ret = r.ProcessData(line, blank_columns)
                if ret:
                    if output:
                        output = output + '\n' + ret
                    else:
                        output = ret
                blank_columns += r.ColumnCount()
            if got_all_headers:
                if output:
                    print(output)
                    output = ""
            else:
                if GotAllHeaders(row_infos):
                    got_all_headers = True
                    print(PrintHeader(row_infos))
                    print(output)
                    output = ""
                else:
                    pass
                        
            
    

# main starts here
if __name__ == '__main__':
    main()

#grep MotorStatus 20200117-093703_deploy.csv | cut -d, -f 1,29,41