# FAQ

### When installing FuseTS, I encounter the error `No module named 'numpy'`. What should I do?

If you encounter the `No module named 'numpy'` error during the installation of FuseTS, it's a known issue when
installing the `vam.whittaker` Python library in Python 3.8 - 3.10.
You can resolve this issue by following these steps:

1. Before installing the FuseTS sources, open your terminal or command prompt.
2. Run the following command to install a specific version of numpy and the Cython library:

```python
pip install numpy==1.23.5 cython
```

This command ensures that the required version of numpy is installed, which should resolve the `No module named 'numpy'` error during FuseTS installation.