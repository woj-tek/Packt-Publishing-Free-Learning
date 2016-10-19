#!/usr/bin/env python

from __future__ import print_function, unicode_literals, division, absolute_import  # We require Python 2.6 or later

__author__ = "Lukasz Uszko, Daniel van Dorp"
__copyright__ = "Copyright 2016"
__license__ = "MIT"
__version__ = "1.0.0"
__email__ = "lukasz.uszko@gmail.com, daniel@vandorp.biz"

import sys
import time
import logging

PY2 = sys.version_info[0] == 2
if PY2:
    from future import standard_library
    standard_library.install_aliases()
    from builtins import *
    from builtins import str
    from builtins import map
    from builtins import object
    reload(sys)
    sys.setdefaultencoding('utf8')

import requests
import os
import configparser
import argparse
import re
from collections import OrderedDict
from bs4 import BeautifulSoup


logging.basicConfig(format='[%(levelname)s] - %(message)s', level=logging.INFO)
# adding a new logging level
logging.SUCCESS = 13
logging.addLevelName(logging.SUCCESS, 'SUCCESS')
logger = logging.getLogger(__name__)
logger.success = lambda msg, *args: logger._log(logging.SUCCESS, msg, args)
# downgrading logging level for requests
logging.getLogger("requests").setLevel(logging.WARNING)

#################################-MAIN CLASSES-###########################################
class PacktAccountData(object):
    """Contains all needed urls, creates a http session and logs int your account"""

    def __init__(self, cfgFilePath):
        self.cfgFilePath = cfgFilePath
        self.configuration = configparser.ConfigParser()
        if not self.configuration.read(self.cfgFilePath):
            raise configparser.Error('{} file not found'.format(self.cfgFilePath))
        self.logFile = self.__getLogFilename()
        self.packtPubUrl = "https://www.packtpub.com"
        self.myBooksUrl = "https://www.packtpub.com/account/my-ebooks"
        self.loginUrl = "https://www.packtpub.com/register"
        self.freeLearningUrl = "https://www.packtpub.com/packt/offers/free-learning"
        self.reqHeaders = {'Connection': 'keep-alive',
                           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 '
                                         '(KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'}
        self.myPacktEmail, self.myPacktPassword = self.__getLoginData()
        self.downloadFolderPath, self.downloadFormats, self.downloadBookTitles = self.__getDownloadData()
        if not os.path.exists(self.downloadFolderPath):
            message = "Download folder path: '{}' doesn't exist".format(self.downloadFolderPath)
            logger.error(message)
            raise ValueError(message)
        self.session = self.createSession()

    def __getLogFilename(self):
        """Gets the filename of the logging file."""
        return self.configuration.get("DOWNLOAD_DATA", 'logFile')

    def __getLoginData(self):
        """Gets user login credentials."""
        email = self.configuration.get("LOGIN_DATA", 'email')
        password = self.configuration.get("LOGIN_DATA", 'password')
        return email, password

    def __getDownloadData(self):
        """Downloads ebook data from the user account."""
        downloadPath = self.configuration.get("DOWNLOAD_DATA", 'downloadFolderPath')
        downloadFormats = tuple(form.replace(' ', '') for form in
                                self.configuration.get("DOWNLOAD_DATA", 'downloadFormats').split(','))
        downloadBookTitles = None
        try:
            downloadBookTitles = [title.strip(' ') for title in
                                  self.configuration.get("DOWNLOAD_DATA", 'downloadBookTitles').split(',')]
            if len(downloadBookTitles) is 0:
                downloadBookTitles = None
        except configparser.Error as e:
            pass
        return downloadPath, downloadFormats, downloadBookTitles

    def createSession(self):
        """Creates the session"""
        formData = {'email': self.myPacktEmail,
                    'password': self.myPacktPassword,
                    'op': 'Login',
                    'form_build_id': '',
                    'form_id': 'packt_user_login_form'}
        # to get form_build_id
        logger.info("Creating session...")
        r = requests.get(self.loginUrl, headers=self.reqHeaders, timeout=10)
        content = BeautifulSoup(str(r.content), 'html.parser')
        formBuildId = [element['value'] for element in
                       content.find(id='packt-user-login-form').find_all('input', {'name': 'form_build_id'})]
        formData['form_build_id'] = formBuildId[0]
        session = requests.Session()
        rPost = session.post(self.loginUrl, headers=self.reqHeaders, data=formData)
        if rPost.status_code is not 200:
            message = "Login failed!"
            logger.error(message)
            raise requests.exceptions.RequestException(message)
        logger.info("Session created, logged in successfully!")
        return session


class FreeEBookGrabber(object):
    """Claims a daily ebook, retrieving its title"""

    def __init__(self, accountData):
        self.accountData = accountData
        self.session = self.accountData.session
        self.bookTitle = ""

    def __writeEbookInfoData(self, data):
        """
        Write result to file
        :param data: the data to be written down
        """
        with open(self.accountData.logFile, "a") as output:
            output.write('\n')
            for key, value in data.items():
                output.write('{} --> {}\n'.format(key.upper(), value))
        logger.info("Complete information for '{}' have been saved".format(data["title"]))

    def getEbookInfoData(self, r):
        """
        Log grabbed book information to log file
        :param r: the previous response got when book has been successfully added to user library
        :return: the data ready to be written to the log file
        """
        logger.info("Retrieving complete information for '{}'".format(self.bookTitle))
        resultHtml = BeautifulSoup(r.text, 'html.parser')
        lastGrabbedBook = resultHtml.find('div', {'id': 'product-account-list'}).find('div')
        bookUrl = lastGrabbedBook.find('a').attrs['href']
        bookPage = self.session.get(self.accountData.packtPubUrl + bookUrl,
                                    headers=self.accountData.reqHeaders, timeout=10).text
        page = BeautifulSoup(bookPage, 'html.parser')

        resultData = OrderedDict()
        resultData["title"] = self.bookTitle
        resultData["description"] = page.find('div', {'class': 'book-top-block-info-one-liner'}).text.strip()
        author = page.find('div', {'class': 'book-top-block-info-authors'})
        resultData["author"] = author.text.strip().split("\n")[0]
        resultData["time"] = author.find('time').attrs["datetime"]
        resultData["downloaded_at"] = time.strftime("%d-%m-%Y %H:%M")
        logger.success("Info data retrieved for '{}'".format(self.bookTitle))
        self.__writeEbookInfoData(resultData)
        return resultData

    def grabEbook(self, logEbookInfodata = False):
        """Grabs the ebook"""
        logger.info("Start grabbing eBook...")
        r = self.session.get(self.accountData.freeLearningUrl,
                             headers=self.accountData.reqHeaders, timeout=10)
        if r.status_code is not 200:
            raise requests.exceptions.RequestException("http GET status code != 200")
        html = BeautifulSoup(r.text, 'html.parser')
        claimUrl = html.find(attrs={'class': 'twelve-days-claim'})['href']
        self.bookTitle = html.find('div', {'class': 'dotd-title'}).find('h2').next_element. \
            replace('\t', '').replace('\n', '').strip(' ')
        r = self.session.get(self.accountData.packtPubUrl + claimUrl,
                             headers=self.accountData.reqHeaders, timeout=10)
        if r.status_code is 200:
            logger.success("eBook: '{}' has been successfully grabbed!".format(self.bookTitle))
            if logEbookInfodata:
                self.getEbookInfoData(r)				
        else:
            message = "eBook: {} has not been grabbed~! ,http GET status code != 200".format(self.bookTitle)
            logger.error(message)
            raise requests.exceptions.RequestException(message)


class BookDownloader(object):
    """Downloads already claimed ebooks from your account"""

    def __init__(self, accountData):
        self.accountData = accountData
        self.session = self.accountData.session

    def getDataOfAllMyBooks(self):
        """Gets data from all available ebooks"""
        logger.info("Getting data of all your books...")
        r = self.session.get(self.accountData.myBooksUrl,
                             headers=self.accountData.reqHeaders, timeout=10)
        if r.status_code is not 200:
            message = "Cannot open {}, http GET status code != 200".format(self.accountData.myBooksUrl)
            logger.error(message)
            raise requests.exceptions.RequestException(message)
        logger.info("Opened '{}' successfully!".format(self.accountData.myBooksUrl))

        myBooksHtml = BeautifulSoup(r.text, 'html.parser')
        all = myBooksHtml.find(id='product-account-list').find_all('div', {'class': 'product-line unseen'})
        self.bookData = [{'title': re.sub(r'\s*\[e\w+\]\s*', '', attr['title'],
                                          flags=re.I).strip(' '), 'id': attr['nid']} for attr in all]
        for i, div in enumerate(myBooksHtml.find_all('div', {'class': 'product-buttons-line toggle'})):
            downloadUrls = {}
            for a_href in div.find_all('a'):
                m = re.match(r'^(/[a-zA-Z]+_download/(\w+)(/(\w+))*)', a_href.get('href'))
                if m:
                    if m.group(4) is not None:
                        downloadUrls[m.group(4)] = m.group(0)
                    else:
                        downloadUrls['code'] = m.group(0)
            self.bookData[i]['downloadUrls'] = downloadUrls

    def downloadBooks(self, titles=None, formats=None):
        """
        Downloads the ebooks.
        :param titles: list('C# tutorial', 'c++ Tutorial') ;
        :param formats: tuple('pdf','mobi','epub','code');
        """
        # download ebook
        if formats is None:
            formats = self.accountData.downloadFormats
            if formats is None:
                formats = ('pdf', 'mobi', 'epub', 'code')
        if titles is not None:
            tempBookData = [data for i, data in enumerate(self.bookData) if
                            any(data['title'] == title for title in titles)]
        else:
            tempBookData = self.bookData
        nrOfBooksDownloaded = 0
        for i, book in enumerate(tempBookData):
            for form in formats:
                if form in list(tempBookData[i]['downloadUrls'].keys()):
                    if form == 'code':
                        fileType = 'zip'
                    else:
                        fileType = form
                    forbiddenChars = ['?', ':', '*', '/', '<', '>', '"', '|', '\\']
                    for ch in forbiddenChars:
                        if ch in tempBookData[i]['title']:
                            tempBookData[i]['title'] = tempBookData[i]['title'].replace(ch, ' ')
                    title = tempBookData[i]['title']
                    try:
                        logger.info("Title: '{}'".format(title))
                    except Exception as e:
                        title = str(title.encode('utf_8', errors='ignore'))  # if contains some unicodes
                    fullFilePath = os.path.join(self.accountData.downloadFolderPath,
                                                "{}.{}".format(tempBookData[i]['title'], fileType))
                    if os.path.isfile(fullFilePath):
                        logger.info("'{}.{}' already exists under the given path".format(title, fileType))
                        pass
                    else:
                        if form == 'code':
                            logger.info("Downloading code for eBook: '{}'...".format(title))
                        else:
                            logger.info("Downloading eBook: '{}' in .{} format...".format(title, form))
                        try:
                            r = self.session.get(self.accountData.packtPubUrl + tempBookData[i]['downloadUrls'][form],
                                                 headers=self.accountData.reqHeaders, timeout=100)

                            if r.status_code is 200:
                                with open(fullFilePath, 'wb') as f:
                                    f.write(r.content)
                                if form == 'code':
                                    logger.success("Code for eBook: '{}' downloaded successfully!".format(title))
                                else:
                                    logger.success("eBook: '{}.{}' downloaded successfully!".format(title, form))
                                nrOfBooksDownloaded = i + 1
                            else:
                                message = "Cannot download '{}'".format(title)
                                logger.error(message)
                                raise requests.exceptions.RequestException(message)
                        except Exception as e:
                            logger.error(e)
                            
        logger.info("{} eBooks have been downloaded!".format(str(nrOfBooksDownloaded)))


#####################################################################################################
#################################-USEFUL OPTIONAL CLASSES-###########################################
#####################################################################################################



####################################-GOOGLE DRIVE MANAGER############################################
##Google Drive:
#pip install virtualenv 
#virtualenv -p python3 env
# or 
#sudo apt-get install python3-venv
#python3 -m venv env
#source env/bin/activate    and  deactivate

import httplib2
import io
import oauth2client
from oauth2client import client
from oauth2client import tools
import apiclient
from apiclient import discovery
from apiclient.http import MediaFileUpload
from apiclient.http import MediaIoBaseDownload

SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
FILE_TYPE=frozenset(["FILE","FOLDER"])

class GoogleDriveManager():
    
    def __init__(self, cfg_file_path):
        self.__set_config_data(cfg_file_path)
        self._root_folder= GoogleDriveFile(self.folder_name)
        self._credentials = self.get_credentials()
        self._http_auth = self._credentials.authorize(httplib2.Http())
        self._service = discovery.build('drive', 'v3', http=self._http_auth)
        self._root_folder.id=self.check_if_file_exist_create_new_one(self._root_folder.name)
        self._mimetypes = {'pdf':'application/pdf', 'zip':'application/zip', 'mobi':'application/x-mobipocket-ebook', 'epub':'application/epub+zip'}
        # downgrading logging level for google api
        logging.getLogger("apiclient").setLevel(logging.WARNING)


    def __set_config_data(self, cfg_file_path):
        """Sets all the config data for Google drive manager"""
        configuration = configparser.ConfigParser()
        if not configuration.read(cfgFilePath):
            raise configparser.Error('{} file not found'.format(cfgFilePath))
        self.app_name = configuration.get("GOOGLE_DRIVE_DATA", 'gdAppName')
        self.folder_name = configuration.get("GOOGLE_DRIVE_DATA", 'gdFolderName')
	        
    def get_credentials(self):
        '''Gets valid user credentials from storage.
        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.
        Returns:
            Credentials, the obtained credential.
        '''
        home_dir = os.getcwd()
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir, self.app_name+'.json')
        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = self.app_name
            try:
                import argparse
                flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
            except ImportError:
                flags = None
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            logger.debug('Storing credentials to ' + credential_path)
        return credentials
       
    def __find_folder_or_file_by_name(self,file_name,parent_id=None):
        if(file_name ==None or len(file_name)==0):
            return False
        page_token = None
        if parent_id is not None:
            query=("name = '%s' and '%s' in parents"%(file_name,parent_id))
        else:
            query=("name = '%s'"%file_name)
        while True:
            response = self._service.files().list(q=query,spaces='drive',fields='nextPageToken, files(id, name, parents)',pageToken=page_token).execute()
            for file in response.get('files', []):
                logger.debug('Found file: %s (%s) %s' % (file.get('name'), file.get('id'),file.get('parents')))
                return file.get('id')
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                return False;
        
    def check_if_file_exist_create_new_one(self,file_name,file_type="FOLDER",parent_id=None):
        if file_type not in FILE_TYPE:
            raise ValueError("Incorrect file_type arg. Allowed types are: %s"%(', '.join(list(FILE_TYPE))))
        id = self.__find_folder_or_file_by_name(file_name,parent_id)
        if id:
            logger.debug(file_name + " exists")
        else:
            logger.debug(file_name + " does not exist")
            if file_type is "FILE":
                pass #TODO
            else: #create new folder
                id=self.__create_new_folder(file_name,parent_id)

        return id
        
    
    def list_all_files_in_main_folder(self):
        results = self._service.files().list().execute()
        items = results.get('files', [])
        if not items:
            logger.debug('No files found.')
        else:
            logger.debug('Files:')
            for item in items:
                logger.debug('{0} ({1})'.format(item['name'], item['id']))
        
    def __create_new_folder(self,folder_name,parent_folders_id =None):
        parent_id= parent_folders_id if parent_folders_id is None else [parent_folders_id]
        file_metadata = {
            'name' : folder_name,
            'mimeType' : 'application/vnd.google-apps.folder',
            'parents': parent_id
        }
        file = self._service.files().create(body=file_metadata, fields='id').execute()
        logger.success('Created Folder ID: %s' % file.get('id'))
        return file.get('id')
    

    def __extract_filename_ext_and_mimetype_from_path(self, path):
        splitted_path= os.path.split(path)
        file_name = splitted_path[-1]
        file_extension = file_name.split('.')[-1]
        mime_type = None
        if  file_extension in self._mimetypes:
            mime_type = self._mimetypes[file_extension]
        return file_name, file_extension, mime_type

    def __insert_file_into_folder(self, file_name, path, parent_folder_id, file_mime_type=None):
        parent_id= parent_folders_id if parent_folder_id is None else [parent_folder_id]
        file_metadata = {
          'name' : file_name,
          'parents': parent_id
        }
        media = MediaFileUpload(path,mimetype=file_mime_type,  # if None, it will be guessed 
                                resumable=True)
        file = self._service.files().create(body=file_metadata,media_body=media,fields='id').execute()
        logger.debug('File ID: {}'.format(file.get('id')))
        return file.get('id') 
       
    def send_files(self, file_paths):
        if file_paths is None or len(file_paths)==0:
            raise ValueError("Incorrect file paths argument format")
        for path in file_paths:
            if os.path.exists(path):
                try:
                    file_attrs = self.__extract_filename_ext_and_mimetype_from_path(path)
                    if not self.__find_folder_or_file_by_name(file_attrs[0], self._root_folder.id):
                        self.__insert_file_into_folder(file_attrs[0], path, self._root_folder.id, file_attrs[2])
                        logger.success('File {} succesfully sent to Google Drive'.format(file_attrs[0]))
                    else:
                        logger.info('File {} already exists on Google Drive'.format(file_attrs[0]))
                except Exception as e:
                        logger.error('Error {} occurred while sending file: {} to Google Drive'.format(e, file_attrs[0]))
                               
    def download_file(self,file_name,file_id):
        request = self._service.files().get_media(fileId=file_id)
        fh = io.FileIO(file_name, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            logger.debug("Download %d%%." % int(status.progress() * 100))
               
class GoogleDriveFile():
    ''' Helper class that describes File or Folder stored on GoogleDrive server'''
    def __init__(self,file_name):
        self.name= file_name
        self.id =None
        self.parent_id=''

#####################################################################################################














if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grab", help="grabs daily ebook",
                        action="store_true")
    parser.add_argument("-gl", "--grabl", help="grabs and log data",
                        action="store_true")
    parser.add_argument("-gd", "--grabd", help="grabs daily ebook and downloads the title afterwards",
                        action="store_true")
    parser.add_argument("-da", "--dall", help="downloads all ebooks from your account",
                        action="store_true")
    parser.add_argument("-dc", "--dchosen", help="downloads chosen titles described in [downloadBookTitles] field",
                        action="store_true")
    parser.add_argument("-sgd", "--sgd", help="sends the grabbed eBook to google drive",
                        action="store_true")
    
    args = parser.parse_args()
    cfgFilePath = os.path.join(os.getcwd(), "configFile.cfg")
    try:
        myAccount = PacktAccountData(cfgFilePath)
        grabber = FreeEBookGrabber(myAccount)
        downloader = BookDownloader(myAccount)
        googleDrive= GoogleDriveManager(cfgFilePath)  
        if args.grab or args.grabl or args.grabd or args.sgd:
            if not args.grabl:
                grabber.grabEbook()
            else:
                grabber.grabEbook(logEbookInfodata=True)
        if args.grabd or args.dall or args.dchosen or args.sgd:
            downloader.getDataOfAllMyBooks()
        if args.grabd or args.sgd:
            if args.sgd:
                myAccount.downloadFolderPath = os.getcwd()              
            downloader.downloadBooks([grabber.bookTitle])
            if args.sgd:
               paths = [os.path.join(myAccount.downloadFolderPath, path) \
                       for path in os.listdir(myAccount.downloadFolderPath) \
                           if os.path.isfile(path) and path.find(grabber.bookTitle) is not -1]
               googleDrive.send_files(paths)
               [os.remove(path) for path in paths]                
        elif args.dall:
            downloader.downloadBooks()
        elif args.dchosen:
            downloader.downloadBooks(myAccount.downloadBookTitles)
        logger.success("Good, looks like all went well! :-)")
    except Exception as e:
        logger.error("Exception occurred {}".format(e))
