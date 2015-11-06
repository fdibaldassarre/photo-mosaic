#!/usr/bin/env python3

import os
import sys
import argparse
from lib import PyLog
from lib import Collager
from lib import CollageImage

path = os.path.abspath(__file__)
MAIN_FOLDER = os.path.dirname(path)
LOG_FOLDER = os.path.join(MAIN_FOLDER, 'log/')

if not os.path.exists(LOG_FOLDER):
  os.mkdir(LOG_FOLDER)

logger = PyLog.new(LOG_FOLDER)

parser = argparse.ArgumentParser(description="Photo Mosaic")
parser.add_argument('--input', help='Base image')
parser.add_argument('--output', help='Result image')
parser.add_argument('--resources', help='Directory with the images to use')
parser.add_argument('--scale', default=1, help='Output scaling, default:1')
parser.add_argument('--images-on-width', dest='images_width', default=8, help='Images along width (approximate), default:8')
parser.add_argument('--images-on-height', dest='images_height', help='Images along height (approximate)')
parser.add_argument('--threshold', default=100, help='Fix a color difference threshold under which an image can be used, default:100')
parser.add_argument('--precision', default=4, help='Precision (higher is better), default:4')
parser.add_argument('--near-size', dest='near_size', default=3, help='Min distance between repeated images, default:3')
parser.add_argument('--shuffle', default=False, action='store_true', help='Use all the images in a uniformely but lose a bit in colour approximation, default:false')
parser.add_argument('--shuffle-distance', dest='shuffle_distance', default=20, help='Distance under which colors are considered similar, default:20')
parser.add_argument('--shuffle-geometry', dest='shuffle_geometry', default=0, help='Makes the images geometry more diverse (uses values between 0 and 1), default:0')
parser.add_argument('--show-previews', dest='show_previews', action='store_true', default=False, help='Save previews during collage, default:false')
parser.add_argument('--load-schema', dest='load_schema', default=None, help='Load collage from schema')
parser.add_argument('--apply-mask', dest='apply_mask', default=None, help='Apply mask to schema (only in conjunction with --load-schema)')
parser.add_argument('--debug', default=False, action='store_true', help='Debug')

args = parser.parse_args()

base_image = args.input
output_image = args.output
images_folder = args.resources
scale_factor = int(args.scale)
images_width = int(args.images_width)
images_height = int(args.images_height) if args.images_height is not None else None
precision = int(args.precision)
threshold = int(args.threshold)
near_size = int(args.near_size)
shuffle = args.shuffle
shuffle_distance = int(args.shuffle_distance)
shuffle_geometry = float(args.shuffle_geometry)
show_partials = int(args.show_previews)
schema_filepath = args.load_schema
apply_mask = args.apply_mask
debug = args.debug

# Check input - Critical
if base_image is not None and not os.path.exists(base_image):
  print("Base image not found")
  sys.exit(1)
if images_folder is None or not os.path.isdir(images_folder):
  print("Missing resources folder")
  sys.exit(1)
if schema_filepath is not None and not os.path.exists(schema_filepath):
  print("Image schema not found")
  sys.exit(1)
# Check input - Warning
if schema_filepath is None and apply_mask is not None:
  print("Warning: you can apply a mask only when loading a schema.")
  print("The mask will be ignored")
  apply_mask = None


if schema_filepath is None:
  # Create collage with image properties
  collager = Collager.new(base_image, images_folder, images_width, images_height, precision, logger, debug)
  # Set collage properties
  collager.setOutputImage(output_image)
  collager.setScaleFactor(scale_factor)
  collager.setShuffleColours(shuffle)
  collager.setShuffleColoursDistance(shuffle_distance)
  collager.setShuffleGeometry(shuffle_geometry)
  collager.setThreshold(threshold)
  collager.setNearSize(near_size)
  collager.setShowPartials(show_partials)
  try:
    collager.collage()
    print('Resizing and saving (it may require some time)')
  except Exception as error:
    print(str(error))
    collager.save()
    sys.exit(2)
  collager.save()
else:
  print('Loading schema')
  # Load collage image
  collage_image = CollageImage.newFromSchema(schema_filepath, images_folder)
  if collage_image is None:
    print("Error reloading collage, exiting.")
    sys.exit(3)
  # Apply mask
  if apply_mask is not None:
    collage_image.applyMask(apply_mask)
  # Resize and save
  print('Resizing and saving')
  collage_image.saveResized(output_image, scale_factor)
  
sys.exit(0)
