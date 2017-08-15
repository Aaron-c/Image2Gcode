# -*- coding: utf-8 -*-
"""
Created on Sun Aug 13 21:45:09 2017

@author: Aaron
"""
import imagetogcode 
from PIL import Image
initial_dir =r'C:\Users\Aaron\Documents\laser files'
inputfile = r'C:\Users\Aaron\Documents\laser files\MonsterTest2.png'


from tkinter import Tk, filedialog

Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing

inputfile = filedialog.askopenfilename(initialdir = initial_dir,title = "choose your file",filetypes = (("png files","*.png"),("all files","*.*"))) # show an "Open" dialog box and return the path to the selected file
print(inputfile)

output_file = filedialog.asksaveasfile(initialdir =initial_dir, mode='w', defaultextension=".gcode")
print(output_file)
image = Image.open(inputfile).convert('L')
generator = imagetogcode.GCodeGen();

generator.imagetogcodeNoRaster(image, output_file)
#    imagetogcode(image, gcode)
#