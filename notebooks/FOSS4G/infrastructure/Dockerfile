# docker build -f notebooks/FOSS4G/infrastructure/Dockerfile . -t foss4g_workshop
FROM jupyter/base-notebook:python-3.8

ARG wd=/tmp/foss4g
ARG codedir=/tmp/fusets

USER root
RUN apt-get update
RUN apt-get install -y build-essential

ADD . $codedir

ADD ./notebooks/FOSS4G $wd

WORKDIR $wd
RUN pip install -r requirements.txt
RUN pip install numpy cython
RUN cd $codedir  && ls -l && pip install .

RUN rm -rf $codedir

ENV GRANT_SUDO=yes

CMD ["jupyter", "lab", "--allow-root", "--ServerApp.token=''","--ServerApp.password=''"]