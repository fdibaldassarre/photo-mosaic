# photo-mosaic
Application to generate photomosaics.

Requirements
------------

python3, python-pil, python-numpy
    
To install type:

```sh
apt-get install python3 python3-pil python3-numpy
```
    
Usage
------------
  
To generate a simple photomosaic run:

```sh
./pm.py --input my_image.png --output my_photo_mosaic.png --resources /path/to/photos --images-on-width 32
```

- input is the base image
- output is the result image
- resources is the folder with the images to use in the mosaic
- images-on-width is the "resolution" of the mosaic, higher means more defined
 
This command will create the file my_photo_mosaic.png and a schema my_photo_mosaic.png.schema.cls which can be loaded
to create bigger versions of the newly created photomosaic.
    
To load the schema and create a photomosaic of size 4x the original image run:

```sh
./pm.py --load-schema my_photo_mosaic.png.schema.cls --resources /path/to/photos --scale 4 --output my_photo_mosaic_4x.png
```

There are several parameters which can be changed to improve the photomosaic. To view the complete list type:

```sh
./pm.py --help
```

WARNING: the program is slow.

Examples
--------

Input:

![input](https://raw.githubusercontent.com/fdibaldassarre/photo-mosaic/master/examples/input.jpg)

Result (--images-on-width 32):

![input](https://raw.githubusercontent.com/fdibaldassarre/photo-mosaic/master/examples/res32.jpg)

Result (--images-on-width 128 --shuffle --shuffle-geometry 0.7 --near-size 5):

![input](https://raw.githubusercontent.com/fdibaldassarre/photo-mosaic/master/examples/res128.jpg)

The images used are taken from the INRIA Holidays dataset.
