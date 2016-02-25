# crest_getter
A Python 3.5 application to dump data from CREST

A fork and modification of the `crawler` application over at the [500 Lines or Less](https://github.com/aosabook/500lines/blob/master/crawler/crawler.markdown) repository, this is currently used as a test bench for feasibility tests / learning the `asyncio`/`aiohttp` libraries in python3.

Eventual goal is to expand functionality to gather and dump data from CREST to compile a database suitable for pyfa (to get away from Phobos / reverence dependence and thus cache scraping) (and also give project a better name <_<)

### Usage

`python3.5 crawl.py https://crest-tq.eveonline.com/types/`