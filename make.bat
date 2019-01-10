python "C:\Python27\Scripts\pyinstaller-script.py" ^
    --log-level WARN ^
    --distpath "dist\win" --workpath "dist\win\build" --specpath "dist\win\spec" ^
    -wFn "Weblogger" ^
    weblogger.pyw

rd /S /Q dist\win\build
rd /S /Q dist\win\spec
