# Generate SVD file from a reference manual

Generates an SVD file for the Silicon Labs SiM3U1x7 from the reference manual.

This is currently work in progress and in a early stage.

## Detailed steps


First the sim3u reference manual must be downloaded into the doc folder:

~~~
wget -P doc/ https://www.silabs.com/documents/public/data-sheets/SiM3U1xx-SiM3C1xx-RM.pdf
~~~

Install the pipenv environment:

~~~
pipenv install
~~~

To execute the tool:

~~~
pipenv run python src/parse_sim3u.py --input doc/SiM3U1xx-SiM3C1xx-RM.pdf --out out.svd
~~~

## Use helper script

Or instead of all of the above, execute:

~~~
./create_svd.sh
~~~

This might take half an hour, so be patient...

## Flow

The script executes the following steps:

- read the toc/outtline of the pdf file
- read the peripheral overview
- read register information for all peripherals
  - this contains the registers and the description of the bits inside the registers
  - these information is attached to the corresponding peripheral

## Current status

- svd file is created
- generation of header file from created svd works
- gpio and uart drivers based on the created svd are working
- Most enumeration value names are suboptimal
- most parts are untested

# Info

This created svd file is intended to be used in the SiM3U port of Zephyr that is currently in development: https://github.com/chrta/zephyr-sim3u
