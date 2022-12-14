# With this Dockerfile we create the Docker image with which we run our pipeline
# To create the image, navigate to this folder and
# docker build -t collaborating.tuhh.de:5005/ckv0173/scilab-rl/scilabrl .
# or
# docker buildx build --platform linux/amd64 -t collaborating.tuhh.de:5005/ckv0173/scilab-rl/scilabrl .
# on an ARM device
# To push it to the repo, create a GitLab Personal Access Token and login with
# docker login collaborating.tuhh.de:5005
# then push the image to the repo with
# docker push collaborating.tuhh.de:5005/ckv0173/scilab-rl/scilabrl
# 1. Base image
FROM ubuntu:22.04

# Get necessary system libraries
# adapted from https://github.com/openai/mujoco-py/blob/master/Dockerfile
# and https://github.com/CoppeliaRobotics/docker-image-coppeliasim/blob/master/Dockerfile
RUN apt-get update -q \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git \
    curl \
    libgl1-mesa-dev \
    libgl1-mesa-glx \
    libglew-dev \
    libosmesa6-dev \
    wget \
    python3-pip \
    patchelf \
    libstdc++6 \
    libx11-6  \
    libxcb1  \
    libxau6  \
    xvfb  \
    dbus-x11  \
    x11-utils  \
    libxkbcommon-x11-0 \
    libavcodec-dev  \
    libavformat-dev  \
    libswscale-dev \
    && apt-get autoclean -y && apt-get autoremove -y && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# # Get mujoco
# # adapted from https://github.com/openai/mujoco-py/issues/676#issuecomment-1107798580
# RUN mkdir -p /root/.mujoco \
#     && wget https://github.com/deepmind/mujoco/releases/download/2.1.0/mujoco210-linux-x86_64.tar.gz -O mujoco.tar.gz \
#     && tar -xf mujoco.tar.gz -C /root/.mujoco/ \
#     && rm mujoco.tar.gz
#
# # # Get CoppeliaSim
# RUN wget http://www.coppeliarobotics.com/files/CoppeliaSim_Edu_V4_1_0_Ubuntu20_04.tar.xz \
#     && tar -xf CoppeliaSim_Edu_V4_1_0_Ubuntu20_04.tar.xz \
#     && rm CoppeliaSim_Edu_V4_1_0_Ubuntu20_04.tar.xz
#
# # # Install miniconda
# RUN wget \
#     https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
#     && bash Miniconda3-latest-Linux-x86_64.sh -b \
#     && rm -f Miniconda3-latest-Linux-x86_64.sh
#
ENV PATH="/root/miniconda3/bin:${PATH}"
# RUN . $(conda info --base)/etc/profile.d/conda.sh \
# 	&& conda create --name scilabrl python=3.8
