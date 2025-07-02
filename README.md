## Dockerfile
```yaml
FROM python:3.9.12

COPY deploy/sources.list /etc/apt/sources.list

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 3B4FE6ACC0B21F32

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get -y install libx11-xcb1
RUN apt-get -y install libgl1-mesa-glx

```

## requirements.txt
```shell script
pandas==1.1.5
numpy==1.25.1
opencv-python==4.9.0.80
cached-property==1.5.2
```
