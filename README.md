## Free Learning PacktPublishing script

**packtPublishingFreeEbook.py** - script that automatically grabs and download a daily free eBook from https://www.packtpub.com/packt/offers/free-learning
  You can use it also to download the already claimed eBooks from your account https://www.packtpub.com/account/my-ebooks


### Requirements:
* Install either Python 2.x or 3.x
* Install pip (if you have not installed it yet).
  To install pip, download:  https://bootstrap.pypa.io/get-pip.py ,
  then run the following command:

  ```  
  python get-pip.py
  ```
  
  Once pip has been installed, run the following command:
  ```
  pip install -r requirements.txt
  ```

* change a name of **configFileTemplate.cfg** to **configFile.cfg**  
* change your login credentials in **configFile.cfg** file
  

### Usage:
* The script **[packtPublishingFreeEbook.py]** might be fired up with one of 6 arguments:

  - Option -g [--grab] - claims (grabs) a daily eBook into your account
  ```
  python packtPublishingFreeEbook.py -g
  ```

  - Option -gl [--grabl] - claims (grabs) a daily eBook into your account and save book info to log file specified in config file
  ```
  python packtPublishingFreeEbook.py -gl
  ```

  - Option -gd [--grabd] - claims (grabs) a daily ebook and downloads the title afterwards to the location specified under *[downloadFolderPath]* field (configFile.cfg file)
  ```
  python packtPublishingFreeEbook.py -gd
  ```
  
  - Option -da [--dall] - downloads all ebooks from your account
  ```
  python packtPublishingFreeEbook.py -da
  ```
  
  - Option -dc [--dchosen] - downloads chosen titles specified under *[downloadBookTitles]* field in *configFile.cfg*
  ```
  python packtPublishingFreeEbook.py -dc
  ```

  - Option -sgd [--sgd] - claims and sends a book to *[gdFolderName]* folder onto Google Drive (more about setup Google Drive API below)  
  ```
  python packtPublishingFreeEbook.py -sgd
  ```
  
* You can set the script to be invoked automatically:
  
  **LINUX** (tested on UBUNTU 16.04):
  
  modify access permissions of the script:
  
  ```
  $ chmod a+x packtPublishingFreeEbook.py 
  ```
  
  **CRON** setup (more: https://help.ubuntu.com/community/CronHowto) :
  
  ```
  $ sudo crontab -e
  ```
  
  paste (modify all paths correctly according to your setup):
  
  ```
  0 12 * * * cd /home/me/Desktop/PacktScripts/ && /usr/bin/python3 packtPublishingFreeEbook.py -gd > /home/me/Desktop/PacktScripts/packtPublishingFreeEbook.log 2>&1
  ```
  
  and save the crontab file. To verify if CRON fires up the script correctly, run a command:
  
  ```
  $ sudo grep CRON /var/log/syslog
  ```
  
  **WINDOWS** (tested on win7):
  
  **schtasks.exe** setup (more info: https://technet.microsoft.com/en-us/library/cc725744.aspx) :
  
  To create the task that will be called at 12:00 everyday, run the following command in **cmd** (modify all paths according to your setup):
  
  ```
  schtasks /create /sc DAILY /tn "grabEbookFromPacktTask" /tr "C:\Users\me\Desktop\GrabPacktFreeBook\grabEbookFromPacktTask.bat" /st 12:00
  ```
  
  To check if the "grabEbookFromPacktTask" has been added to all scheduled tasks on your computer:
  
  ```
  schtasks /query
  ```
  
  To run the task manually:
  
  ```
  schtasks /run /tn "grabEbookFromPacktTask"
  ```  
  
  To delete the task:
  
  ```
  schtasks /delete /tn "grabEbookFromPacktTask"
  ```
  
  If you want to log all downloads add -l switch to grabEbookFromPacktTask i.e.
  ```
  schtasks /create /sc DAILY /tn "grabEbookFromPacktTask" /tr "C:\Users\me\Desktop\GrabPacktFreeBook\grabEbookFromPacktTask.bat -l" /st 12:00
  ``` 
  
  If you want to additionaly make command line windows stay open after download add -p switch i.e.
  ```
  schtasks /create /sc DAILY /tn "grabEbookFromPacktTask" /tr "C:\Users\me\Desktop\GrabPacktFreeBook\grabEbookFromPacktTask.bat -l -p" /st 12:00
  ``` 


* GOOGLE_DRIVE_API Setup:
Full info about the Google Drive python API can be found [here](https://developers.google.com/drive/v3/web/quickstart/python)  

Step 1: Turn on the Drive API
    
    Use [this wizard](https://console.developers.google.com/flows/enableapi?apiid=drive) to create or select a project in the Google Developers Console and automatically turn on the API. Click Continue, then Go to credentials.
    On the *Add credentials to your project page*, click the *Cancel* button.
    At the top of the page, select the OAuth consent screen tab. Select an Email address, enter a *Product name* if not already set, and click the Save button.
    Select the Credentials tab, click the Create credentials button and select *OAuth client ID*.
    Select the application type *Other*, enter the name *"GoogleDriveManager"*, and click the Create button.
    Click *OK* to dismiss the resulting dialog.
    Click the file_download (Download JSON) button to the right of the client ID.
    Move this file to your working directory and rename it *"client_secret.json"*

Step 2: Install the Google Client Library
  
  Run the following command to install the library using pip:
  ```
  pip install --upgrade google-api-python-client  or pip install --upgrade google-api-python-client-py3
  ``` 

Step 3: Create credentials folder:
  
  Simply, just fire up the script without any arguments; you will see a prompt in your browser asking for permissions, click then *allow*
  ```
  python packtPublishingFreeEbook.py 
  ```  

Step 4: Already done!
  
  Run the below command to send the claimed book to your Google Drive
  ```
  python packtPublishingFreeEbook.py -sgd
  ``` 

* EXAMPLE: download **'Unity 4.x Game AI Programming'** and  **'Multithreading in C# 5.0 Cookbook'** books in all available formats  (pdf, epub, mobi) with zipped source code file from your packt account
  
  To download chosen titles from your account, you must put them into **downloadBookTitles** in **configFile.cfg** as shown below:
  
  **configFile.cfg** example:
  ```
    [LOGIN_DATA]
    email= youremail@youremail.com
    password= yourpassword    
    
    [DOWNLOAD_DATA]
    downloadFolderPath: C:\Users\me\Desktop\myEbooksFromPackt
    downloadFormats: pdf, epub, mobi, code
    downloadBookTitles: Unity 4.x Game AI Programming , Multithreading in C# 5.0 Cookbook
    logFile: logfile.log
  ```
  
  run:
  ```
    python packtPublishingFreeEbook.py -dc
  ```

In case of any questions feel free to ask, happy grabbing!
