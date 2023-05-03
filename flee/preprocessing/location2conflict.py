from dflee import dInputGeography
import numpy as np
import sys

if __name__ == "__main__":
    """
    Usage <this> <end_time> <input> <output>
    """

    if len(sys.argv)>1:
        if (sys.argv[1]).isnumeric():
            end_time = int(sys.argv[1])

    ig = dInputGeography.InputGeography()

    ig.ReadLocationsFromCSV(sys.argv[2])

    file = open(sys.argv[3],"w")

    output_header_string = "#Day,"

    for l in ig.locations:

        if l[5] == "conflict_zone":
            output_header_string += " %s," % (l[0])

    output_header_string = output_header_string[:-1]

    output_header_string += "\n"

    file.write(output_header_string)

    for t in range(0,end_time):

        output = "%s" % t

        for l in ig.locations:
            # print(l)
            if l[5] == "conflict_zone":
                flood_date = int(l[6])
                if flood_date <= t:
                    output +=",1"
                else: 
                    output +=",0"


        output += "\n"
        file.write(output)

    file.close()
