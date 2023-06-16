# docker build -f notebooks/FOSS4G/infrastructure/Dockerfile . -t foss4g_workshop
FROM python:3.8.17-slim-bullseye

ARG wd=/tmp/foss4g
ARG codedir=/tmp/fusets

ADD . $codedir
ADD ./notebooks/FOSS4G $wd

# INSTALL DEPS
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
RUN apt-get update
RUN apt-get install -y gcc nodejs

# SETUP JUPYTER LAB
RUN pip install jupyterlab ipyleaflet
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager
RUN jupyter nbextension enable --py widgetsnbextension
RUN jupyter serverextension enable --py jupyterlab

# INSTALL LIBS
WORKDIR $wd
RUN pip install -r requirements.txt
RUN pip install numpy cython
RUN cd $codedir  && ls -l && pip install .

# CLEANUP
RUN rm -rf $codedir


CMD ["jupyter", "lab", "--allow-root", "--no-browser", "--NotebookApp.token="]