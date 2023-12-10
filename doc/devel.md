# Development Doc

## Running tests

    pytest tests/*


## Render only selected OSM objects:

Vigo Town Hall only:

    ddd osm-build --xyztile=62358,48540,17 --name=ddd_http -o --cache-clear -p ddd:terrain:splatmap=False -p 'ddd:osm:filter=[osm:id="relation-10460599"];[osm:id="way-461933786"];[osm:id="way-757871353"];[osm:id="way-31564510"];[osm:id="way-642240797"];[osm:id="way-642240793"]'
