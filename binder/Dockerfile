FROM tschm/jupyter:1.2.0 as builder

# File Author / Maintainer
# MAINTAINER Thomas Schmelzer "thomas.schmelzer@gmail.com"
ENV HOME /home/${NB_USER}
ENV APP_ENV docker

COPY --chown=jovyan:users  . /tmp/finmarketpy

COPY . ${HOME}
USER root
RUN chown -R ${NB_UID} ${HOME}

# Install snappy for pystore and ODBC
USER root

# Minimal dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libsnappy-dev gcc g++ unixodbc-dev

# Dependencies for pystore and weasyprint in buildDeps
# If we don't want to use weasyprint we
# build-essential libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
# RUN buildDeps='gcc g++ libsnappy-dev unixodbc-dev build-essential libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info' && \
#    apt-get update && apt-get install -y $buildDeps --no-install-recommends

# Switch back to jovyan to avoid accidental container runs as root
USER $NB_UID

RUN pip install --no-cache-dir -r /tmp/finmarketpy/requirements.txt && \
    rm -rf /tmp/finmarketpy

RUN ln -s /home/${NB_USER}/finmarketpy /home/${NB_USER}/work/finmarketpy
RUN ln -s /home/${NB_USER}/finmarketpy_examples /home/${NB_USER}/work/finmarketpy_examples
RUN ln -s /home/${NB_USER}/finmarketpy_examples/finmarketpy_notebooks /home/${NB_USER}/work/finmarketpy_examples/finmarketpy_notebooks