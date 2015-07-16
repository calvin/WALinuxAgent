# Windows Azure Linux Agent
#
# Copyright 2014 Microsoft Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Requires Python 2.4+ and Openssl 1.0+
#

import platform
import os
import re
import shutil
import pwd
import tempfile
import subprocess
import azurelinuxagent.logger as logger
import azurelinuxagent.utils.textutil as textutil

"""
File operation util functions
"""
def GetFileContents(filepath, asbin=False, removeBom=False):
    """
    Read and return contents of 'filepath'.
    """
    mode='r'
    if asbin:
        mode+='b'
    with open(filepath, mode) as F :
        c=F.read()
    if (not asbin) and removeBom:
        c = textutil.RemoveBom(c)
    return c

def SetFileContents(filepath, contents):
    """
    Write 'contents' to 'filepath'.
    """
    #if type(contents) == str :
        #contents=contents.encode('latin-1', 'ignore')
    with open(filepath, "wb+") as F :
        F.write(contents)

def AppendFileContents(filepath, contents):
    """
    Append 'contents' to 'filepath'.
    """
    #if type(contents) == str :
        #contents=contents.encode('latin-1')
    with open(filepath, "a+") as F :
        F.write(contents)

def ReplaceFileContentsAtomic(filepath, contents):
    """
    Write 'contents' to 'filepath' by creating a temp file, and replacing original.
    """
    handle, temp = tempfile.mkstemp(dir = os.path.dirname(filepath))
    #if type(contents) == str :
        #contents=contents.encode('latin-1')
    try:
        os.write(handle, contents)
    except IOError, e:
        logger.Error('Write to file {0}, Exception is {1}', filepath, e)
        return 1
    finally:
        os.close(handle)

    try:
        os.rename(temp, filepath)
    except IOError, e:
        logger.Info('Rename {0} to {1}, Exception is {2}',temp,  filepath, e)
        logger.Info('Remove original file and retry')
        try:
            os.remove(filepath)
        except IOError, e:
            logger.Error('Remove {0}, Exception is {1}',temp,  filepath, e)

        try:
            os.rename(temp, filepath)
        except IOError, e:
            logger.Error('Rename {0} to {1}, Exception is {2}',temp, filepath, e)
            return 1
    return 0

def GetLastPathElement(path):
    head, tail = os.path.split(path)
    return tail

def GetLineStartingWith(prefix, filepath):
    """
    Return line from 'filepath' if the line startswith 'prefix'
    """
    for line in GetFileContents(filepath).split('\n'):
        if line.startswith(prefix):
            return line
    return None

#End File operation util functions

def CreateDir(dirpath, mode=None, owner=None):
    if not os.path.isdir(dirpath):
        os.makedirs(dirpath)
    if mode is not None:
        ChangeMod(dirpath, mode)
    if owner is not None:
        ChangeOwner(dirpath, owner)

def ChangeOwner(path, owner):
    ownerInfo = pwd.getpwnam(owner)
    os.chown(path, ownerInfo[2], ownerInfo[3])   

def ChangeMod(path, mode):
    os.chmod(path, mode)

def RemoveFiles(*args, **kwargs):
    for path in args:
        if os.path.isfile(path):
            os.remove(path)

def CleanupDirs(*args, **kwargs):
    """
    Remove all the contents under the directry
    """
    for dirName in args:
        if os.path.isdir(dirName):
            for item in os.listdir(dirName):
                path = os.path.join(dirName, item)
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)

def UpdateConfigFile(path, lineStart, val, chk_err=False):
    config = []
    if not os.path.isfile(path) and chk_err:
        raise Exception("Can't find config file:{0}".format(path))
    config = GetFileContents(path).split('\n')
    config = filter(lambda x : not x.startswith(lineStart), config)
    config.append(val)
    ReplaceFileContentsAtomic(path, '\n'.join(config))

def SearchForFile(dirName, fileName):
    for root, dirs, files in os.walk(dirName):
        for f in files:
            if f == fileName:
                return os.path.join(root, f)
    return None

def ChangeTreeMod(path, mode):
    for root, dirs, files in os.walk(path):
        for f in files:
            os.chmod(os.path.join(root, f), mode)

def FindStringInFile(fname, matchs):
    """
    Return match object if found in file.
    """
    try:
        ms=re.compile(matchs)
        for l in (open(fname,'r')).readlines():
            m=re.search(ms,l)
            if m:
                return m
    except:
        raise
    
    return None
