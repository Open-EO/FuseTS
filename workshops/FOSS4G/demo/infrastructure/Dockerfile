# docker build -f notebooks/FOSS4G/infrastructure/Dockerfile . -t foss4g_workshop
FROM jupyter/base-notebook:python-3.8

ARG workdir=./work/foss4g
ARG codedir=./work/fusets

USER root

RUN apt-get update
RUN apt-get install -y build-essential libhdf5-serial-dev netcdf-bin libnetcdf-dev

# copy contents
ADD . ${codedir}
ADD ./notebooks/FOSS4G ${workdir}

# Install FuseTS
RUN \
    pip install numpy==1.23.5 cython && \
    pip install ./${codedir} && \
    rm -rf ${codedir}

# Add notebooks only
WORKDIR ${workdir}
RUN pip install -r requirements.txt

ENV GRANT_SUDO=yes

CMD ["jupyter", "lab", "--allow-root", "--ServerApp.token=''","--ServerApp.password=''"]