@echo off
if "%1" == "-l" (
    echo ***Date: %DATE:/=-% [%TIME::=:%] *** >> src\packtPublishingFreeEbook.log
    echo *** Grabbing free eBook from Packt Publishing.... *** >> src\packtPublishingFreeEbook.log
    python src\packtPublishingFreeEbook.py -gd >> src\packtPublishingFreeEbook.log 2>&1
    echo:
    echo:>> src\packtPublishingFreeEbook.log
) ELSE (
    echo *** Grabbing free eBook from Packt Publishing.... ***
    python src\packtPublishingFreeEbook.py -gd
    echo *** Done ! ***
)
pause
if "%1" == "-p" (
    pause
)
if "%2" == "-p" (
    pause
)