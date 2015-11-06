#!/usr/bin/env python3

import os
import sys
import numpy
import random
import time
from lib import ImageManager
from lib import CollageImage

random.seed(time.time())

VALID_FILETYPES = ['.png', '.jpg', '.jpeg']

MAX_DIFF_CLASSES = 10
RESIZE_DIFFERENCE_BOUND = 0.01
LOWER_ADAPT_HEIGHT_BOUND = 0.2

PREVIEWS_NUMBER = 10

DEFAULT_PRECISION = 4
DEFAULT_THRESHOLD = 100
DEFAULT_NEAR_SIZE = 3
DEFAULT_SHUFFLE_COLOURS_DISTANCE = 10
DEFAULT_SHUFFLE_GEOMETRY = 0

DEFAULT_COLLAGE_IMAGE_SIZE_PRECISION = 0.8
DEFAULT_COLLAGE_SAME_HEIGHT_STREAK = 4

class Collager():
  
  def __init__(self, imagepath):
    # Base options
    self.base_image = ImageManager.newFromPath(imagepath)
    self.base_image.load()
    self.colours = None
    self.collage_image = CollageImage.new(self.base_image.size)
    self.output_image_savepath = None
    self.images_folder = None
    self.debug = False
    self.log = None
    # Collage options
    self.precision = DEFAULT_PRECISION
    self.threshold = DEFAULT_THRESHOLD
    self.near_size = DEFAULT_NEAR_SIZE
    self.scale_factor = 1
    self.shuffle_colours = False
    self.shuffle_colours_distance = DEFAULT_SHUFFLE_COLOURS_DISTANCE
    self.shuffle_geometry = DEFAULT_SHUFFLE_GEOMETRY
    # Workflow options
    self.show_partials = False
    # Class variables
    self.sector_size = None
    self.collage_image_size = None
    self.collage_image_size_precision = DEFAULT_COLLAGE_IMAGE_SIZE_PRECISION
    self.collage_image_size_min = None # Enforced limit
    self.collage_image_size_max_width = None # Non-enforced limit
    self.collage_image_size_max_height = None # Non-enforced limit
    # Collage variables
    self.collage_same_height_streak = DEFAULT_COLLAGE_SAME_HEIGHT_STREAK
    self.collage_same_height_streak_max = DEFAULT_COLLAGE_SAME_HEIGHT_STREAK
  
  def setScaleFactor(self, value):
    self.scale_factor = value
  
  def setShuffleColours(self, value=True):
    self.shuffle_colours = value
  
  def setShuffleColoursDistance(self, value=True):
    self.shuffle_colours_distance = value
  
  def setThreshold(self, threshold):
    self.threshold = threshold
  
  def setPrecision(self, value):
    self.precision = value
  
  def setNearSize(self, size):
    self.near_size = size
  
  def setShuffleGeometry(self, percent):
    self.shuffle_geometry = percent
  
  def setShowPartials(self, value):
    self.show_partials = value
  
  def setImagesNumberOnWidth(self, n):
    self.collage_image_size = int(numpy.ceil(1.0 * self.base_image.width / n))
  
  def setImagesNumberOnHeight(self, n):
    self.collage_image_size = int(numpy.ceil(1.0 * self.base_image.height / n))
  
  def setOutputImage(self, savepath):
    self.output_image_savepath = savepath
  
  def setDebug(self, value=True):
    self.debug = value
  
  def setLogger(self, logger):
    if self.debug:
      self.log = logger.createDebugLogger('main.txt', self)
    else:
      self.log = logger.createInfoLogger('main.txt', self)
  
  def loadColours(self, folder):
    self.images_folder = folder
    self.colours = []
    self.sector_size = max(int(1.0 * self.collage_image_size / self.precision), 1)
    self.collage_image_size = self.sector_size * self.precision
    self.loadColoursComplete()
    
  def loadColoursComplete(self):
    self.log.info('loadColoursComplete == Loading colours')
    self.log.debug('loadColoursComplete == Collage image size: ' + str(self.collage_image_size))
    self.log.debug('loadColoursComplete == Collage image size precision: ' + str(self.collage_image_size_precision))
    self.log.debug('loadColoursComplete == Sector size: ' + str(self.sector_size))
    # Set min size
    self.collage_image_size_min = int(numpy.ceil(self.collage_image_size * self.collage_image_size_precision))
    self.log.info('loadColoursComplete == Min size: ' + str(self.collage_image_size_min))
    # Save width and height
    images_width = []
    images_height = []
    print('Loading resources')
    self.log.info('loadColoursComplete == Loading from images')
    loading_folder = self.images_folder
    for name in os.listdir(loading_folder):
      path = os.path.join(loading_folder, name)
      if not os.path.isdir(path) and self.hasValidExtension(path): # Ignore folders and invalid files
        try:
          img = ImageManager.new(path)
          img.setSectorSize(self.sector_size)
          # resize
          img.resizeMaximal(self.collage_image_size)
          # partition
          img.partition()
          # load colour
          colour = CollageImage.newColour(img, self.sector_size)
          # add to self.colours
          self.colours.append(colour)
          # add sizes
          images_width.append(img.width)
          images_height.append(img.height)
          # Show progress
          sys.stdout.write('.')
          sys.stdout.flush()
        except Exception as error:
          self.log.info('loadColoursComplete == Error loading: ' + path)
          print('\n*Error loading ' + path)
          continue
    self.collage_image_size_avg_width = int(numpy.ceil(numpy.mean(images_width)))
    self.collage_image_size_avg_height = int(numpy.ceil(numpy.mean(images_height)))
    self.collage_image_size_max_width = int(numpy.max(images_width))
    self.collage_image_size_max_height = int(numpy.max(images_height))
    self.log.info('loadColoursComplete == Collage image size avg width: ' + str(self.collage_image_size_avg_width))
    self.log.info('loadColoursComplete == Collage image size avg height: ' + str(self.collage_image_size_avg_height))
    self.log.info('loadColoursComplete == Collage image size max width: ' + str(self.collage_image_size_max_width))
    self.log.info('loadColoursComplete == Collage image size max height: ' + str(self.collage_image_size_max_height))
    print('\nLoaded ' + str(len(self.colours)) + ' resources')
  
  def collage(self):
    self.fixParameters()
    self.setupBaseImage()
    self.collageStart()
  
  def fixParameters(self):
    if self.near_size > 0 and len(self.colours) < 4*self.near_size**2:
      # Fix near size
      self.setNearSize(int(numpy.floor(numpy.sqrt(len(self.colours)) / 2)))
      print('Warning: Near size is too high! Lowered to ' + str(self.near_size))
      print('If you want to set an higher near size you need more images!')
      print('Note: it\'s recommended not to have high near size and few images in collection.')
  
  def setupBaseImage(self):
    self.base_image.setSectorSize(self.sector_size)
  
  def collageStart(self):
    self.log.info('collageStart == Starting')
    # Setup partials
    tot_pixels = self.collage_image.width * self.collage_image.height
    partials = []
    if self.show_partials:
      skip = max(int(numpy.floor(self.collage_image.height / PREVIEWS_NUMBER)), 1)
      for i in range(PREVIEWS_NUMBER):
        partials.append(skip*i)
    # Start collage
    print('Collage!') 
    for y in range(self.collage_image.height):
      index = y * self.collage_image.width
      perc = round(100.0 * index / tot_pixels)
      sys.stdout.write('\r Progression: ' + str(perc) + ' %   ')
      sys.stdout.flush()
      if y in partials:
        self.log.info('collageStart == Save preview')
        self.savePreview()
      for x in range(self.collage_image.width):
        if self.collage_image.isPositionEmpty((x, y)):
          self.log.info('collageStart == Filling point ' + str(x) + ', ' + str(y))
          max_area, min_area = self.findAvailableArea((x,y))
          self.log.info('collageStart == Max area ' + str(max_area[0]) + ', ' + str(max_area[1]))
          self.log.info('collageStart == Min area ' + str(min_area[0]) + ', ' + str(min_area[1]))
          # Try to adapt height
          if self.collage_same_height_streak < self.collage_same_height_streak_max:
            max_area, min_area, adapted = self.tryAdaptHeight((x,y), max_area, min_area)
            self.collage_same_height_streak += 1 # I assume adapted is always True
            '''
            if adapted:
              self.collage_same_height_streak += 1
            else:
              self.collage_same_height_streak = 0
            '''
          else:
            # Start new
            p = random.random()
            if p < self.shuffle_geometry:
              self.log.info('collageStart == Start new streak')
              self.collage_same_height_streak = 0
          # Fill Area
          self.log.info('collageStart == Prepare to fill area')
          self.log.info('collageStart == Max area ' + str(max_area[0]) + ', ' + str(max_area[1]))
          self.log.info('collageStart == Min area ' + str(min_area[0]) + ', ' + str(min_area[1]))
          self.fillArea((x,y), max_area, min_area)
          if self.debug:
            self.savePreview()
            input('Press any key to continue...')
    sys.stdout.write('\r Progression: 100 %   \n')
    sys.stdout.flush()
  
  def findAvailableArea(self, position):
    x, y = position
    base_width, base_height = self.collage_image.getMaxSpaceAt(position, self.collage_image_size_max_width, self.collage_image_size_max_height)
    min_width = self.collage_image_size_min
    min_height = self.collage_image_size_min
    # Check space right and bottom
    right_space = self.collage_image.getMaxSpaceRight((x+base_width, y), self.collage_image_size_max_width)
    bottom_space = self.collage_image.getMaxSpaceBottom((x, y+base_height), self.collage_image_size_max_height)
    # Setup right
    if right_space == 0:
      if base_width >= 2 * self.collage_image_size_min:
        base_width = base_width - self.collage_image_size_min
      else:
        min_width = base_width
    elif right_space < self.collage_image_size_min:
      # missing space right
      if base_width + right_space >= 2 * self.collage_image_size_min:
        base_width = base_width - self.collage_image_size_min
        # Now I have the min space on the right
      else:
        # include right area (and I must fill all the width)
        base_width = base_width + right_space
        min_width = base_width
    # Setup bottom
    if bottom_space == 0:
      if base_height >= 2 * self.collage_image_size_min:
        base_height = base_height - self.collage_image_size_min
      else:
        min_height = base_height
    elif bottom_space < self.collage_image_size_min:
      # missing space bottom
      if base_height + bottom_space >= 2 * self.collage_image_size_min:
        base_height = base_height - self.collage_image_size_min
        # Now I have the min space on the bottom
      else:
        # include right area (and I must fill all the width)
        base_height = base_height + bottom_space
        min_height = base_height
    
    return (base_width, base_height) , (min_width, min_height)
    
  def tryAdaptHeight(self, position, max_area, min_area):
    # Analyze area
    x, y = position
    self.log.info('tryAdaptHeight == Adapt at ' + str(x) + ', ' + str(y))
    min_area_width, min_area_height = min_area
    max_area_width, max_area_height = max_area
    adapted = False
    # If I have a bit of freedom on the width I try to adapt the height to the image on the left
    if (max_area_width - min_area_width / min_area_width) > LOWER_ADAPT_HEIGHT_BOUND:
    # Constrain the height if possible
      left_pos = self.collage_image.getColourIndexAtPosition((x - 1, y))
      if left_pos is not None:
        _, left_height = self.collage_image.getImageSizeAt(left_pos)
        _, left_y = left_pos
        new_height = left_y + left_height - y
        if min_area_height <= new_height and new_height <= max_area_height:
          max_area = (max_area_width, new_height)
          min_area = (min_area_width, new_height)
          adapted = True
      else:
        # Try adapting right
        right_pos = self.collage_image.getColourIndexAtPosition((x + max_area_width + 1, y))
        if right_pos is not None:
          _, right_height = self.collage_image.getImageSizeAt(right_pos)
          _, right_y = right_pos
          new_height = right_y + right_height - y
          if min_area_height <= new_height and new_height <= max_area_height:
            max_area = (max_area_width, new_height)
            min_area = (min_area_width, new_height)
            adapted = True
    return max_area, min_area, adapted
  
  def fillArea(self, position, max_area, min_area):
    # Get the base partition
    base_partition = self.base_image.createShiftedPartition(position, max_area)
    # Refer average colour
    base_colour = base_partition.getAverageColour()
    # Get near images
    near_images = self.getNearImages(position)
    if len(near_images) >= len(self.colours):
      # Warning
      print('Too many images considered near, decreasing near size.')
      self.near_size = self.near_size - 1
      return self.fillArea(position, max_area, min_area)
    # Threshold
    best_threshold = None
    best_fit_threshold = None
    # Fits list
    best_fits = []
    best_fit_difference = None
    # check colours
    for colour in self.colours:
      img = colour.getBaseImage()
      if not img in near_images:
        diff = img.getAverageColourDifference(base_colour)
        # Check best threshold
        if best_threshold is None or diff < best_threshold:
            best_threshold = diff
            best_fit_threshold = colour
        if diff > self.threshold:
          # threshold too high, skip
          continue
        else:
          # Check fitting
          new_size, factor_difference = self.checkFitting(img, max_area, min_area)
          # Calculate colour difference
          img_resized = colour.getResizedImage(new_size)
          img_partition = img_resized.getPartition()
          colour_difference = self.computeSectorsDistance(img_partition, base_partition)
          # Add to fits list
          current_fit = (colour, new_size, factor_difference, colour_difference)
          if best_fit_difference is None or colour_difference < best_fit_difference + self.shuffle_colours_distance:
            best_fits.append(current_fit)
            if best_fit_difference is None or colour_difference < best_fit_difference:
              # Update best difference
              best_fit_difference = colour_difference
              # Update best fits
              rm = []
              for el in best_fits:
                colour, _, _, diff = el
                if diff >= best_fit_difference + self.shuffle_colours_distance:
                  rm.append(el)
              for el in rm:
                best_fits.remove(el)
    
    if len(best_fits) == 0:
      # No colours available -> use best threshold
      # NOTE: best_fit_threshold cannot be None since I check the length of near_images at the start of the function
      self.forceFitting(best_fit_threshold, position, max_area, min_area)
    else:
      self.log.info('fillArea == Select best fit')
      colour, size = self.selectBestFit(best_fits)
      self.addSectionToImage(colour, position, size)
    
  def selectBestFit(self, fits):
    # NOTE: I assume fits is not empty
    if self.shuffle_colours:
      return self.selectBestFitShuffle(fits)
    else:
      return self.selectBestFitStandard(fits)
      
  def selectBestFitShuffle(self, fits):
    # Pick a random colour with 0 resize difference
    # or the colour with the better resize
    zero_resize_colours = []
    for fit in fits:
      colour, size, resize_difference, colour_difference = fit
      if resize_difference == 0:
        zero_resize_colours.append((colour, size))
    if len(zero_resize_colours) > 0:
      # pick random
      r = random.randint(0, len(zero_resize_colours)-1)
      best_colour = zero_resize_colours[r]
    else:
      # pick element with min resize difference
      best_fit = min(fits, key=lambda el : el[2])
      colour, size, _, _ = best_fit
      best_colour = (colour, size)
    return best_colour
  
  def selectBestFitStandard(self, fits):
    # Pick the colour with the best colour+resize
    best_colour_difference = min(fits, key=lambda el : el[3])[3]
    #best_factor_difference = min(fits, key=lambda el : el[2]) # Assume is 1
    # Pick the colour with min factor
    best_factor = None
    best_colour = None
    for fit in fits:
      colour, size, resize_difference, colour_difference = fit
      factor = (1 + colour_difference) / (1 + best_colour_difference) * ( 1 + numpy.log(1 + resize_difference) )
      if best_factor is None or factor < best_factor:
        best_factor = factor
        best_colour = (colour, size)
    return best_colour
    
  def checkFitting(self, img, max_area, min_area):
    min_width, min_height = min_area
    min_factor = max( min_width / img.width, min_height / img.height)
    max_width, max_height = max_area
    max_factor = min( max_width / img.width, max_height / img.height)
    # Lower bound for height and width: I need at least this resize
    lower_factor = self.collage_image_size_min / min(img.width, img.height)
    min_factor = max(lower_factor, min_factor)
    if max_factor >= min_factor:
      # Any factor in this interval is fine
      factor = min_factor + random.random() * (max_factor - min_factor)
      factor_difference = 0.0
      new_size_width = int(numpy.ceil(img.width * factor))
      new_size_height = int(numpy.ceil(img.height * factor))
    else:
      # I have min_factor > max_factor
      #factor_difference = min_factor - max_factor
      if img.width > img.height:
        new_size_width = max_width
        new_size_height = max(min_height, self.collage_image_size_min)
      else:
        new_size_width = max(min_width, self.collage_image_size_min)
        new_size_height = max_height
      factor_difference = abs(new_size_width / img.width - new_size_height / img.height)
    
    new_size = new_size_width, new_size_height
    
    return new_size, factor_difference
  
  def forceFitting(self, colour, position, max_area, min_area): 
    self.log.info('forceFitting == Force at ' + str(position[0]) + ', ' + str(position[1]))
    img = colour.getBaseImage() 
    new_size, _ = self.checkFitting(img, max_area, min_area)
    self.addSectionToImage(colour, position, new_size)
    
  def addSectionToImage(self, colour, position, size):
    self.collage_image.addColourAtPosition(colour, position, size)
  
  def getNearImages(self, position):
    imgs = []
    x, y = position
    if self.near_size > 0:
      near_dimension_width = self.collage_image_size_avg_width * self.near_size
      near_dimension_height = self.collage_image_size_avg_height * self.near_size
      for el in self.collage_image.colours:
        i, j = el
        if i >= x - near_dimension_width - 1 and i <= x + near_dimension_width + 1 and \
           j >= y - near_dimension_height - 1 and j <= y + near_dimension_height + 1:
          imgs.append(self.collage_image.colours[i,j].getBaseImage())
    return imgs
  
  def computeSectorsDistance(self, colour_partition, refer_partition, refer_shift=None):
    diff = []
    if refer_shift is None:
      i_shift = 0
      j_shift = 0
    else:
      i_shift, j_shift = refer_shift
    #real_colour_partition = colour_partition.get()
    #real_refer_partition = refer_partition.get()
    for index in colour_partition:
      i, j = index
      r_i = i + i_shift
      r_j = j + j_shift
      if (r_i, r_j) in refer_partition:
        diff.append( colour_partition[index] - refer_partition[r_i, r_j] )
    # DEBUG WARNING
    if len(diff) == 0:
      self.log.warn('computeSectorsDistance == Partitions incompatible?')
      # What happened??
      print('ERROR Partition are incompatible????')
      print('***************************')
      return 1.0
    diff_mean = numpy.mean(diff)
    return diff_mean
  
  def save(self):
    self.log.info('save == Saving...')
    self.collage_image.saveResized(self.output_image_savepath, self.scale_factor)
    self.saveSchema()
  
  def saveSchema(self):
    schema_savepath = self.output_image_savepath + '.schema.cls'
    self.collage_image.saveSchema(schema_savepath)
  
  def savePreview(self):
    self.collage_image.save(self.output_image_savepath)
  
  def hasValidExtension(self, path):
    _, ext = os.path.splitext(path)
    return ext.lower() in VALID_FILETYPES
      
  
def new(base_image, images_folder, images_width, images_height, precision, logger, debug):
  collager = Collager(base_image)
  collager.setDebug(debug)
  collager.setLogger(logger)
  # Set properties
  collager.setPrecision(precision)
  if images_height is not None:
    collager.setImagesNumberOnHeight(images_height)
  else:
    collager.setImagesNumberOnWidth(images_width)
  # Load images
  collager.loadColours(images_folder)
  return collager
