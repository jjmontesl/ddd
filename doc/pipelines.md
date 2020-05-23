# DDD Processing Pipelines

In order to define reusable transformation and generation processes, using pure
Python code is not usually the best approach.

DDD Pipelines allow for a _declarative_ style of processing tasks that pave the way
for posterior extension or modification, and to create different versions of
a generation process. This can be useful in order to generate alternative styles
or different levels of detail (LODs).

DDD Pipeline tasks are designed to play nicely with DDD Selectors in order to filter
the nodes that each rule acts upon.

