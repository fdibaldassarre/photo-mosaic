#!/usr/bin/env python3

import os
import sys
from json import JSONEncoder
from json import JSONDecoder
from PIL import Image
from lib import ImageManager

JSON_encoder = JSONEncoder()
JSON_decoder = JSONDecoder()

MAX_IMAGES_MEM = 1 # DO NOT SET LOWER THAN 1
MAX_COLOURS_MEM = 200
DATA_IMAGE_SIZE = 'ImageSize'
DATA_COLOURS = 'Colours'

class CollageColour():

  def __init__(self, base_img, sector_size):
    self.base_img = base_img
    self.sector_size = sector_size
    self.images = {}
  
  def getBaseImage(self):
    return self.base_img
  
  def reload(self):
    self.images = {}
    imgpath = self.base_img.getFilepath()
    self.base_img = ImageManager.newFromPath(imgpath)
  
  def getResizedImage(self, size, antialias=False, partition=True, memorize=True):
    width, height = size
    if size in self.images:
      img = self.images[width, height]
      img.setSectorSize(self.sector_size)
      if partition and not img.isPartitioned():
        img.partition()
    else:
      img_raw = self.base_img.getResizedCopy(size, antialias)
      img = ImageManager.newFromData(img_raw)
      img.setSectorSize(self.sector_size)
      if partition:
        img.partition()
      if memorize and MAX_IMAGES_MEM > 0:
        if len(self.images) > MAX_IMAGES_MEM:
          # delete one element
          del_key = list(self.images.keys())[0]
          del self.images[del_key]
        # Add this image
        self.images[width, height] = img
    return img
  
class CollageImage():

  def __init__(self, size):
    width, height = size
    self.width = width
    self.height = height
    self.size = size
    self.img = Image.new("RGBA", self.size, color=(255, 255, 255, 0))
    self.pixelManager = self.img.load()
    self.colours = {}
    self.colours_size = {}
    self.colours_usage = {}
  
  def isPositionEmpty(self, position):
    x, y = position
    if x < 0 or x >= self.width or y < 0 or y >= self.height:
      return False
    else:
      return self.pixelManager[position][3] == 0
  
  def addColourAtPosition(self, colour, position, size):
    self.colours[position] = colour
    self.colours_size[position] = size
    if colour in self.colours_usage:
      self.colours_usage[colour] += 1
    else:
      self.colours_usage[colour] = 1
    image = colour.getResizedImage(size, partition=False)
    self.img.paste(image.getImage(), position)
          
  def getColourIndexAtPosition(self, position):
    x, y = position
    pos = None
    if x < 0 or x >= self.width or y < 0 or y >= self.height:
      return pos
    for position in self.colours:
      i, j = position
      w, h = self.colours_size[position]
      if i <= x and x < i + w and j <= y and y < j + h:
        pos = (i,j)
        break
    return pos
  
  def getImageSizeAt(self, position):
    return self.colours_size[position]
  
  def removeImageAtPosition(self, position):
    img_size = self.colours_size[position]
    blank_img = Image.new("RGBA", img_size, color=(255, 255, 255, 0))
    self.img.paste(blank_img, position)
    colour = self.colours[position]
    self.colours_usage[colour] -= 1
    del self.colours[position]
    del self.colours_size[position]
  
  def getMaxSpaceAt(self, position, max_width, max_height):
    return self.getMaxSpaceRight(position, max_width), self.getMaxSpaceBottom(position, max_height)
  
  def getMaxSpaceRight(self, position, max_width):
    x, y = position
    width = 0
    if x < 0 or x >= self.width or y < 0 or y >= self.height:
      return width
    for i in range(max_width):
      if not self.isPositionEmpty((x+i, y)):
        break
      else:
        width += 1
    return width
  
  def getMaxSpaceBottom(self, position, max_height):
    x, y = position
    height = 0
    if x < 0 or x >= self.width or y < 0 or y >= self.height:
      return height
    for j in range(max_height):
      if not self.isPositionEmpty((x, y+j)):
        break
      else:
        height += 1
    return height
  
  def isSectionFree(self, x, y, width, height):
    for i in range(width):
      if self.pixelManager[x+i, y][3] != 0:
        return False
    for j in range(height):
      if self.pixelManager[x, y+j][3] != 0:
        return False
    return True
  
  def getColourUsage(self, colour):
    if colour in self.colours_usage:
      return self.colours_usage[colour]
    else:
      return 0
  
  def save(self, savepath):
    self.img.save(savepath)
  
  def debugFillEmptySpace(self, position, colour):
    width, height = self.getMaxSpaceAt(position, self.width, self.height)
    self.debugFillSpace(position, (width, height), colour)
  
  def debugFillImageAt(self, position, colour):
    width, height = self.colours_size[position]
    self.debugFillSpace(position, (width, height), colour)
  
  def debugFillSpace(self, position, size, colour):
    img = Image.new("RGBA", size, color=colour)
    self.img.paste(img, position)

  def saveResized(self, savepath, scale=1):
    # Create new image with rescaled size
    width, height = self.size
    new_width, new_height = width*scale, height*scale
    img = Image.new("RGBA", (new_width, new_height), color=(255, 255, 255, 0))
    # Paint new image
    reloaded_colours = []
    tot_colours = len(self.colours)
    actual_pos = 0
    for pos in self.colours:
      # Show progression
      perc = round(100.0 * actual_pos / tot_colours)
      sys.stdout.write('\r Progression: ' + str(perc) + ' %   ')
      sys.stdout.flush()
      actual_pos += 1
      # Resize and paste the image
      x, y = pos
      new_x, new_y = x*scale, y*scale
      width, height = self.colours_size[x,y]
      new_width, new_height = width*scale, height*scale
      colour = self.colours[x,y]
      if not colour in reloaded_colours:
        colour.reload()
        reloaded_colours.append(colour)
      image = colour.getResizedImage((new_width, new_height), antialias=True, partition=False, memorize=False)
      img.paste(image.getImage(), (new_x, new_y))
      if len(self.colours) > MAX_COLOURS_MEM :
        colour.reload() # Free the memory of the base image (otherwise I use too much RAM)
    sys.stdout.write('\r Progression: 100 %   \n')
    sys.stdout.flush()
    print("Saving")
    # save
    img.save(savepath)

  def saveSchema(self, savepath):
    data = {}
    data[DATA_IMAGE_SIZE] = self.size
    colours = []
    for pos in self.colours:
      colour = self.colours[pos]
      imgname = os.path.basename(colour.getBaseImage().getFilepath())
      size = self.colours_size[pos]
      colour_data = (imgname, pos, size)
      colours.append(colour_data)
    data[DATA_COLOURS] = colours
    # encode to json and save
    hand = open(savepath, 'w')
    # Size
    size_string = JSON_encoder.encode(data[DATA_IMAGE_SIZE])
    hand.write(size_string + '\n')
    for colour in data[DATA_COLOURS]:
      colour_string = JSON_encoder.encode(colour)
      hand.write(colour_string + '\n')
    hand.close()
  
  def applyMask(self, maskpath):
    mask = Image.open(maskpath).convert('RGBA')
    mask = mask.resize((self.img.size), Image.ANTIALIAS)
    mask_width, mask_height = mask.size
    maskPixelManager = mask.load()
    delete_list = []
    for pos in self.colours:
      x, y = pos
      colour = self.colours[x,y]
      colour_width, colour_height = self.colours_size[x,y]
      # check if delete
      colour_delete = True
      for i in range(x, x+colour_width):
        if i < mask_width:
          for j in range(y, y+colour_width):
            if j < mask_height:
              if maskPixelManager[i, j][3] != 0:
                colour_delete = False
                break
      if colour_delete:
        delete_list.append(pos)
     
    for pos in delete_list:
      # NOTE/WARNING: this function makes colours_usage useless (which at this point should be useless)
      colour = self.colours[pos]
      self.colours_usage[colour] = 2
      self.removeImageAtPosition(pos)
     
def new(*args, **kwargs):
  coll = CollageImage(*args, **kwargs)
  return coll

def newColour(*args, **kwargs):
  colour = CollageColour(*args, **kwargs)
  return colour

def newColourFromPath(imgpath, sector_size=None):
  img = ImageManager.newFromPath(imgpath)
  colour = CollageColour(img, sector_size)
  return colour

def newFromSchema(filepath, images_folder): 
  with open(filepath, 'r') as hand:
    # Read size
    line = hand.readline()
    size = JSON_decoder.decode(line)
    # Read images
    images = []
    for line in hand:
      # append colour
      image_data = JSON_decoder.decode(line)
      images.append(image_data)
  # Create collage
  collage = CollageImage(size)
  colours_dict = {}
  # Add colours
  for img_data in images:
    imgname, position, size = img_data
    imgpath = os.path.join(images_folder, imgname)
    if not os.path.exists(imgpath):
      print("Image: " + imgpath + ' not found!')
      print("Please select the correct images folder")
      return None, None
    if imgpath in colours_dict:
      colour = colours_dict[imgpath]
    else:
      colour = newColourFromPath(imgpath)
      colours_dict[imgpath] = colour
    i, j = position
    collage.colours[i, j] = colour
    collage.colours_size[i, j] = size
  
  return collage
