# activate conda env
# conda activate hm_dev
# change kernel name
sed -i 's/conda-env-hm_oo-py/python3/g' docs/*.ipynb
# force execution of nbs
sed -i 's/execute_notebooks: off/execute_notebooks: force/g' docs/_config.yml
# build the docs
jupyter-book config sphinx docs/
# jupyter-book build docs
sphinx-build docs docs/_build/html -b html
# turn off forced execution so RTD doesn't try to execute nobs
sed -i 's/execute_notebooks: force/execute_notebooks: off/g' docs/_config.yml
# copy some of the notebooks to hillmaker-examples
cp docs/getting_started.ipynb ../hillmaker-examples/notebooks
cp docs/using_cli.ipynb ../hillmaker-examples/notebooks
cp docs/using_make_hills.ipynb ../hillmaker-examples/notebooks
cp docs/using_oo_api.ipynb ../hillmaker-examples/notebooks
cp docs/example_occupancy_analysis.ipynb ../hillmaker-examples/notebooks
# deactivate conda env
# conda deactivate
