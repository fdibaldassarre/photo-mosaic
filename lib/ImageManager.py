#!/usr/bin/env python3

import os
from PIL import Image
import numpy

class ImageSection():
  
  def __init__(self, position, size, colour):
    self.position = position
    self.size = size
    self.colour_real = colour
    red, green, blue = self.colour_real
    self.colour = (int(red), int(green), int(blue))
  
  def getPosition(self):
    return self.position
  
  def getSize(self):
    return self.size
  
  def getColour(self):
    return self.colour
  
  def getColourReal(self):
    return self.colour_real
  
  def __sub__(self, b):
    r1, g1, b1 = self.colour_real
    r2, g2, b2 = b.colour_real
    return numpy.linalg.norm( (r1-r2, g1-g2, b1-b2) )
  
  def getData(self):
    return (self.position, self.size, self.colour_real)

class ImagePartition():
  
  def __init__(self, width, height):
    self._partition = {}
    self._average_colour = (255, 255, 255)
    self.size = (width, height)
  
  def __iter__(self):
    return self._partition.__iter__()
  
  def __getitem__(self, key):
    return self._partition[key]
  
  def __setitem__(self, key, value):
    self._partition[key] = value
  
  def keys(self):
    return self._partition.keys()
  
  def getSize(self):
    return self.size
  
  def getAverageColour(self):
    return self._average_colour
  
  def addColour(self, x, y, colour):
    self._partition[x,y] = colour
  
  def computeAverageColour(self):
    r_list = []
    g_list = []
    b_list = []
    for el in self._partition:
      r,g,b = self._partition[el].getColourReal()
      r_list.append(r)
      g_list.append(g)
      b_list.append(b)
    self._average_colour = ( numpy.mean(r_list), numpy.mean(g_list), numpy.mean(b_list) )


class ImageManager():
  
  def __init__(self, imgpath=None, image=None):
    self.imgpath = imgpath
    if self.imgpath is not None:
      self.img = Image.open(self.imgpath)
    else:
      self.img = image
    self.size = self.img.size
    self.width, self.height = self.size
    self.pixelManager = None
    self._partition = None
    self._partition_square_size = None
  
  def getFilepath(self):
    return self.imgpath
  
  def getImage(self):
    return self.img
  
  def isPartitioned(self):
    return self._partition is not None
  
  def setSectorSize(self, sector_size):
    self._partition_square_size = sector_size
  
  def load(self):
    self.img = self.img.convert('RGB')
    self.pixelManager = self.img.load()
  
  def save(self, filepath):
    self.img.save(filepath)
  
  def resize(self, width, height):
    self.img = self.img.resize((width, height), Image.ANTIALIAS)
    self.width, self.height = self.img.size
  
  def getResizedCopy(self, size, antialias=False):
    if antialias:
      new_img = self.img.resize(size, Image.ANTIALIAS)
    else:
      new_img = self.img.resize(size)
    return new_img
  
  def resizeMinimal(self, size):
    # Resize the image so that both width and height are <= size
    factor = 1.0 * size / max(self.width, self.height)
    new_width = int(numpy.ceil(self.width*factor))
    new_height = int(numpy.ceil(self.height*factor))
    self.resize(new_width, new_height)
  
  def resizeMaximal(self, size):
    # Resize the image so that width or height are of the given size
    factor = 1.0 * size / min(self.width, self.height)
    new_width = int(numpy.ceil(self.width*factor))
    new_height = int(numpy.ceil(self.height*factor))
    self.resize(new_width, new_height)
  
  def resizeBest(self, size):
    # Resize to the best approx of n*size x m*size
    if self.width < self.height:
      width = size
      factor = 1.0 * size / self.width
      height_true = int(numpy.ceil(self.height*factor))
      n = numpy.rint(height_true / size)
      height = size*int(n)
    else:
      height = size
      factor = 1.0 * size / self.height
      width_true = int(numpy.ceil(self.width*factor))
      n = numpy.rint(width_true / size)
      width = size*int(n)
    self.resize(width, height)
  
  def partitionWidth(self, lines):
    square_width = int(numpy.ceil(1.0 * self.width / lines))
    self.setSectorSize(square_width)
    self.partiton()
  
  def partitionHeight(self, lines):
    square_width = int(numpy.ceil(1.0 * self.height / lines))
    self.setSectorSize(square_width)
    self.partiton()
  
  def partition(self):
    partition = self.createShiftedPartition((0, 0), (self.width, self.height))
    self._partition = partition
    return self._partition
    
  def createShiftedPartition(self, start, size):
    if self.pixelManager is None:
      self.load()
    x, y = start
    width, height = size
    square_width = self._partition_square_size
    width_lines = int(numpy.ceil(1.0 * width / square_width))
    height_lines = int(numpy.ceil(1.0 * height / square_width))
    size = (width_lines, height_lines)
    partition = ImagePartition(width_lines, height_lines)
    for i in range(width_lines):
      for j in range(height_lines):
        partition.addColour(i, j, self.computeShiftedSection(x, y, i, j, square_width))
    partition.computeAverageColour()
    return partition
  
  def computeShiftedSection(self, x0, y0, i, j, square_width):
    x = x0 + i*square_width
    y = y0 + j*square_width
    red = []
    green = []
    blue = []
    for i in range(x, x+square_width):
      if i < self.width:
        for j in range(y, y+square_width):
          if j < self.height:
            red.append(self.pixelManager[i,j][0])
            green.append(self.pixelManager[i,j][1])
            blue.append(self.pixelManager[i,j][2])
    if len(red) > 0:
      median = (numpy.mean(red), numpy.mean(green), numpy.mean(blue))
    else:
      median = (255, 255, 255) # Note: the section is empty
    section = ImageSection((x, y), square_width, median)
    return section
  
  def computeSection(self, i, j, square_width):
    return self.computeShiftedSection(0, 0, i, j, square_width)
  
  def getPartition(self):
    return self._partition

  def getPartitionSize(self):
    return self.getPartition().getSize()
  
  def getAverageColour(self):
    return self.getPartition().getAverageColour()
  
  def getAverageColourDifference(self, colour):
    r, g, b = colour
    img_r, img_g, img_b = self.getAverageColour()
    return numpy.linalg.norm( [r - img_r, g - img_g, b - img_b] )
  
  def debugCreatePartitionImage(self, savepath):
    new_image = Image.new("RGB", (self.width, self.height), "white")
    for el in  self.getPartition():
      section = img_partition[el]
      colour_img = Image.new("RGB", section.getSize(), section.getColour())
      new_image.paste(colour_img, section.getPosition())
    new_image.save(savepath)
      
def new(*args, **kwargs):
  img = ImageManager(*args, **kwargs)
  return img

def newFromPath(filepath):
  img = ImageManager(filepath)
  return img

def newFromData(data):
  img = ImageManager(image=data)
  return img
