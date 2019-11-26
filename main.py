#!/usr/bin/python3
#
# main.py
#
# Print calculated tables from easybj module
#
# Note: you may not change this file
#

import easybj

#
# Pretty print 2D table in standard format
#
def print_2d_table(name, table):
    # column width
    colwidth = 6 if table.celltype is float else 2
    
    # y-label width (for first column)
    ylwidth = max([len(str(y)) for y in table.ylabels])
    
    # print table name
    print(name + ":")
    
    # print title row (space delimited labels)
    print(" ".join([ " "*ylwidth ] + 
          [ str(x)[:colwidth].center(colwidth) for x in table.xlabels ]))
    
    # print each row from the table
    for y in table.ylabels:
        row = [ str(y).ljust(ylwidth) ]
        for x in table.xlabels:
            val = table[y,x]
            if val is None:
                text = '-' * colwidth
            elif table.unit == '%':
                # crash now if probability table has a value error
                assert(isinstance(val, float) and val >= 0.)
                text = "%.3f%%"%(val*100)
            elif isinstance(val, float):
                text = "%.3f"%val if val < 0 else " %.3f"%val
            else:
                text = str(val)[:colwidth].center(colwidth)
            row.append(text)
        print(" ".join(row))

#
# Prints out all the dealer tables for all dealer starting hands
# Note: we do not print the table for dealer 21 or dealer bust
# since neither of the two are "initial" hands
#
def print_dealer_tables(tables):
    for dc in easybj.DEALER_CODE:
        table = tables[dc]
        keys = sorted(table.keys())
        print("Dealer %s"%dc)
        print(" ".join(["{:>2}: {:01.6f}".format(k, float(table[k]))
            for k in keys ]))

def print_result(name, result):
    if name == "advantage":
        print("Player Advantage: %2.4f%%"%(result*100))
    elif name == "dealer":
        print_dealer_tables(result)
    elif name == "resplit":
        for i, element in enumerate(result):
            print_2d_table(name + str(i), element)
    else:
        print_2d_table(name, result)
          
#
# Parses command line and prints selected tables
#
def main(argc, argv):
    errors = []
    results = easybj.calculate()
    
    if argc == 1:
        # print all results
        for name, result in results.items():
            print_result(name, result)
    else:
        # print only specified tables
        for name in argv[1:]:
            if name in results:
                print_result(name, results[name])
            else:
                errors.append(name)
      
    if len(errors) > 0:
        print("%s: result(s) not found:"%argv[0], " ".join(errors))


if __name__ == "__main__":
    import sys
    main(len(sys.argv), sys.argv)

