FROM python:3.9

ENV HOME=/opt/app

WORKDIR $HOME

COPY requirements.txt $HOME
RUN pip uninstall pyOpenSSL
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

COPY . $HOME

ENV PYTHONUNBUFFERED=true

CMD ["/bin/sh", "deploy/run.sh"]
