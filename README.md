# Generate SVD file from a reference manual

Generates an SVD file for the Silicon Labs SiM3U1x7 from the reference manual.

This is currently work in progress and in a early stage.

First the sim3u reference manual must be downloaded into the doc folder:

~~~
mkdir doc
cd doc
wget https://www.silabs.com/documents/public/data-sheets/SiM3U1xx-SiM3C1xx-RM.pdf
cd ..
~~~

Install the pipenv environment:

~~~
pipenv install
~~~

To execute the tool:

~~~
pipenv run python src/parse_sim3u.py --input docs/SiM3U1xx-SiM3C1xx-RM.pdf --out out.svd
~~~

This might take half an hour, so be patient...

## Flow

The script executes the following steps:

- read the toc/outtline of the pdf file
- read the peripheral overview
- read register information for all peripherals
  - this contains the registers and the description of the bits inside the registers
  - these information is attached to the corresponding peripheral

## Currently missing

- parse register content details to create enum information
- check validity of parsed information
- create classes with pyxb for svd file creation
- create the svd file

# Links

http://pyxb.sourceforge.net
