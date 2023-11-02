# activate conda env
# conda activate hm_dev
# change kernel name
sed -i 's/conda-env-hm_oo-py/python3/g' *.ipynb
# build the docs
jupyter-book build .
# copy some of the notebooks to hillmaker-examples
cp getting_started.ipynb ../../../hillmaker-examples/notebooks
cp using_cli.ipynb ../../../hillmaker-examples/notebooks
cp using_make_hills.ipynb ../../../hillmaker-examples/notebooks
cp using_oo_api.ipynb ../../../hillmaker-examples/notebooks
cp example_occupancy_analysis.ipynb ../../../hillmaker-examples/notebooks
# deactivate conda env
# conda deactivate
