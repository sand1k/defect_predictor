The data collector consists of two parts:
1. `crawler.py` script which walks through commits in `data/atom` repository
2. node.js script `index.js`, which launches a server and waits for requests from `crawler.py` and returns serialized json with collected metrics

To run data collection:
1. `mkdir data` and clone atom repository there
2. `npm install`
3. Run node.js server: `node index.js`
4. Run crawler: `python3 crawler.py`


To run the app in docker do the following:
1. Install docker
2. Run docker container: `docker-compose run --rm metrics /bin/bash`
3. Run any commands
