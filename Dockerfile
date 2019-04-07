FROM node:7

RUN useradd --user-group --create-home --shell /bin/false app
ENV HOME=/home/app

COPY package.json $HOME/defpred/
RUN chown -R app:app $HOME/*
USER app
WORKDIR $HOME/defpred
RUN npm install
