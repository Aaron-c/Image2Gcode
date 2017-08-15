#!/usr/bin/python
#
#    imagetogcode
#    Copyright 2013 Brian Adams, modified by aaron callard
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>

"""Convert an image file to gcode a Marlin powered laser cutter can understand"""
import sys, getopt
import os
import numpy as np
from PIL import Image
from PIL import ImageOps
from LineKDTree import LineTree, Line


def remove_transparency(im, bg_colour=(255, 255, 255)):

    # Only process if image has transparency (http://stackoverflow.com/a/1963146)
    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):

        # Need to convert to RGBA if LA format due to a bug in PIL (http://stackoverflow.com/a/1963146)
        alpha = im.convert('RGBA').split()[-1]

        # Create a new background image of our matt color.
        # Must be RGBA because paste requires both images have the same format
        # (http://stackoverflow.com/a/8720632  and  http://stackoverflow.com/a/9459208)
        bg = Image.new("RGBA", im.size, bg_colour + (255,))
        bg.paste(im, mask=alpha)
        return bg

    else:
        return im

class ScalePt2mm:
    def __init__(self,image_size, desired_size, laser_width_mm):
        # image size in pixels
        # desired size in mm
        self.image_size_pixels = image_size;
        self.desired_size = desired_size;
        self.laser_width_mm = laser_width_mm;
        self.ratio_x = image_size[0]/desired_size[0]
        self.num_engraving_lines = desired_size[1]/self.laser_width_mm
        self.number_engraving_lines_per_image_row = self.num_engraving_lines/desired_size[1]
        
    def scale_x(self, x_point):
        return(x_point*self.ratio_x)

    # returns which line in the image to read for this point in the engraving
    def find_pixel_row(self, y_point):
        # the
        line_number = y_point/self.laser_width_mm
        return(int(line_number/self.number_engraving_lines_per_image_row) )
        
        
class ReorderGcode:
    def __init__(self):
        self.lines = []
        self.Last_position = (0,0)
        self.laser_strength = 255
        self.postfix = []
        
    def addLine(self, line):
        self.lines.append(line)
        
    def OutputGcode(self, file):
        tree = LineTree(self.lines)
        start_point, line = tree.nearest_neighbor([-1000,-1000]);
        while True:
            tree.RemoveLine(line)
            end_point = line.other(start_point)
            self.OutputLine(file, start_point, end_point)
            if tree.isempty():
                break
            start_point, line = tree.nearest_neighbor(end_point);

    def point2gcodePos(self, point, last_pos):
        delta_pos = (point[0]-last_pos[0], point[1]- last_pos[1])
        return ' X' + str(delta_pos[0]) +  ' Y' + str(delta_pos[1])
            

    def OutputLine(self, f, start_point, end_point, laser_on = True):
        #    print laser_on, point_on, point_off, OutputLine.Last_position
        if not (laser_on):
            return
            
        
        # move to begining of line
        out = 'G0 ' + self.point2gcodePos(start_point, self.Last_position) + self.postfix
        f.write(out)
        # move to end of line
        f.write('M3 S' + str(self.laser_strength) + '\n')
        out = 'G1 ' + self.point2gcodePos(end_point, start_point) + self.postfix
        f.write(out)
        f.write('M5 \n')
        self.Last_position = end_point;


    
def PIL2array(img):
    return np.array(img.getdata(), np.uint8).reshape(img.size[1], img.size[0])    
    
class GCodeGen:
    def __init__(self):
        self.engraved_size_mm =[216, 279]
        self.laser_width_mm = 0.1
        self.threshold = 10
        self.start_pt = [0,0]
        self.laser_strength = 20
        self.postfix = ' F4000\n'
        self.absolute_position = False
        self.save_test_file =False    

    def isChanged(self, value, laser_on):
        if (laser_on):
            return value < self.threshold
        else:
            return value > self.threshold

    def rowToGCode(self, row, output, y_point, scaler):
        laser_on = row[0] > self.threshold
        point_start = 0;
        for index, value in np.ndenumerate(row):
            if self.isChanged(value, laser_on):
                index = index[0]
                if (laser_on):
                    line = Line((y_point, scaler.scale_x(point_start)),(y_point, scaler.scale_x(index)))
                    output.addLine(line)
    #                sys.stdin.read(1)
    
                point_start = index
                laser_on = not(laser_on)
        if (laser_on):
            output.addLine(Line((y_point, scaler.scale_x(point_start)),(y_point, scaler.scale_x(row.size))))
    
    def imagetogcodeNoRaster(self, image, f):
        image = remove_transparency(image)
        img = ImageOps.invert(image)
        #img = image;
        width, height = img.size
    
        f.write("; Image pixel size: "+str(width)+"x"+str(height)+"\n");
        if (self.absolute_position):
           f.write('G90; Absolute positioning\n')
        else:
           f.write('G91; Relative positioning\n')
    
        f.write('M649 S20; Set intensity to 20\n')
        pixels = list(img.getdata())
    
        threshold = sum(pixels)/len(pixels)
        print(threshold)
        matrix = PIL2array(img)
        if (self.save_test_file):
            x = [x > self.threshold for x in matrix]
            np.savetxt('test.csv', x, delimiter="", fmt= "%i")
        
    #    print  matrix
        y_point = 0;
        reorderer = ReorderGcode()
        reorderer.postfix = self.postfix
        reorderer.laser_strength = self.laser_strength
        scaler = ScalePt2mm(matrix.shape, self.engraved_size_mm, self.laser_width_mm)
        print(scaler.__dict__)
        for line in range(int(scaler.num_engraving_lines)):
            y_point = line*self.laser_width_mm
            index = scaler.find_pixel_row(y_point)
            row = matrix[index]
            self.rowToGCode(row, reorderer, y_point, scaler)
            
        reorderer.OutputGcode(f)


def main(argv):
    inputfile = None
    
    def showhelp():
        print( "imagetogcode: Process an input image to gcode for a Marlin laser cutter.")
        print()
        print( "Usage: imagetogcode -i <input file> -o [output file]")
        print( "-o with no file outputs to the same location with extension.gcode")
    
    outputfile = None
    print( argv)
    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["input=", "output="])
    except getopt.GetoptError:
        showhelp()    
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            showhelp()
            sys.exit()
        if opt in ('-i', '--input'):
            inputfile = arg
            if opt not in ('-o', '--output'):
                in_filename, file_extension = os.path.splitext(inputfile)
                outputfile = in_filename + ".gcode"
        elif opt in ('-o', '--output'):
            outputfile = arg
            print( arg)            
    if inputfile is None:
        showhelp()
        sys.exit(2)
    try:
        image = Image.open(inputfile).convert('L')
    except IOError:
        print("Unable to open image file.")
        sys.exit(2)
    if outputfile is None:
        gcode = sys.stdout
    else:
        try:
            gcode = open(outputfile, "w")
        except IOError:
            print("Unable to open output file.")
    a= GCodeGen();
    a.imagetogcodeNoRaster(image, gcode)
#    imagetogcode(image, gcode)
    

if __name__ == "__main__":
    main(sys.argv[1:])
