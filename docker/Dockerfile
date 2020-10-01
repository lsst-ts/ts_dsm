ARG deploy_env_tag=salobj_v5.3.0_xml_v4.6.0

FROM lsstts/deploy-env:${deploy_env_tag}

ARG idl_conda_version=1.1.1_v4.7.0
ARG dsm_conda_version=1.1.0

RUN mkdir /home/saluser/telemetry
RUN mkdir /home/saluser/repos

WORKDIR /home/saluser/repos

ENV CSC_INDEX=1
ENV CSC_MODE=0

RUN source ~/miniconda3/bin/activate && \
    source $OSPL_HOME/release.com && \
    conda install -c lsstts ts-idl=${idl_conda_version} && \
    conda install -c lsstts ts-dsm=${dsm_conda_version}

COPY setup.sh /home/saluser/.setup.sh
COPY shutdown.sh /home/saluser/.shutdown.sh

USER saluser

WORKDIR /home/saluser/
