echo Checking Relative

python -msphinx.ext.intersphinx "sphinx-documentation/source/extrobject/objects.inv" > debug_sphinx.txt
python -msphinx.ext.intersphinx "https://docs.blender.org/api/2.79/objects.inv" > debug_sphinx2.txt