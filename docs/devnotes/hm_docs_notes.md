Writing docs resources
------------------------

- Overview of structuring documentation - https://documentation.divio.com/
- Hitchhikders Guide - https://docs.python-guide.org/writing/documentation/

jupyter-book
------------

Ran into issue with trying to use jupyter-book to create documentation. Jupyter Book is unable to correctly determine and use the jupyter kernel name in the Jupyter notebook to be turned into documentation. The issue is described well in:

https://github.com/executablebooks/jupyter-book/issues/1348

The hack around is to manually change the "name" parameter of the kernel to "python3". However, once you re-edit the notebook and switch to the necessar conda env for running hillmaker, the error reappears next time you try to build the Jupyter Book (unless you again change the name to python3.

Create script that uses sed to make the edit described above and then runs the book build.

```
conda activate hm_dev
sh ./change_kernel_name.sh 
jupyter-book build .
conda deactivate
```
