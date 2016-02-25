# crest_getter
A Python 3.5 application to dump data from CREST

A fork and modification of the `crawler` application over at the [500 Lines or Less](https://github.com/aosabook/500lines/blob/master/crawler/crawler.markdown) repository, this is currently used as a test bench for feasibility tests / learning the `asyncio`/`aiohttp` libraries in python3.

Eventual goal is to expand functionality to gather and dump data from CREST to compile a database suitable for pyfa (to get away from Phobos / reverence dependence and thus cache scraping) (and also give project a better name <_<)

### Usage

`python3.5 crawl.py https://crest-tq.eveonline.com/types/`

### Authentication

If you need authentication, please edit `client_app.ini` with your client details. Please note that this client must support the `publicData` scope (to get a valid refresh token) as well as have the callback set to `http://localhost:6789/`

I'm actually not sure if this is needed for the use-case of collecting data for pyfa (I think it's all public), however if this ever gets to that point I also want this to be mostly general-purpose, hence getting basic Authentication out of the way now.