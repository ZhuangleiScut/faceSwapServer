from urllib.error import HTTPError, URLError
from urllib.request import Request, urlretrieve
import os
import tarfile


def download(url, root, filename, untar=False):
    fpath = os.path.join(root, filename)
    if not os.path.exists(root):
        os.mkdir(root)
    if os.path.exists(fpath):
        print("Data already downloaded")
    else:
        print("Downloading %s to %s" % (url, fpath))
        err_msg = "URL fetch failure on {}: {} -- {}"
        try:
            try:
                urlretrieve(url, fpath)
            except URLError as e:
                raise Exception(err_msg.format(url, e.errno, e.reason))
            except HTTPError as e:
                raise Exception(err_msg.format(url, e.code, e.msg))
        except (Exception, KeyboardInterrupt) as e:
            print(e)
            if os.path.exists(fpath):
                os.remove(fpath)
    if untar is True:
        with tarfile.open(fpath) as tar:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tar, os.path.dirname(fpath))

