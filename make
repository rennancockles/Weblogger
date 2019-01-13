#! /bin/bash

python -m PyInstaller -wF \
    --log-level WARN \
    --distpath "./dist/linux" --workpath "./dist/linux/build" --specpath "./dist/linux/spec" \
    -wFn "Weblogger" \
    -i "./weblogger.ico" \
    weblogger.pyw

rm -rf dist/linux/build
rm -rf dist/linux/spec
