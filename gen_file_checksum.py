import argparse
from enum import Enum
import os
import sys
import tarfile
import traceback

from generator import cksum, md5

class ChecksumType(Enum):
    CKSUM = "cksum"
    MD5   = "md5"

class ZipType(Enum):
    TARGZ = "tar.gz"

def gen_file_checksum(file:str, checksum_type=ChecksumType.MD5, dest_file=""):
    res = ""
    if checksum_type == ChecksumType.CKSUM:
        res = cksum(file)
    elif checksum_type == ChecksumType.MD5:
        res = md5(file)
    else:
        raise Exception("unknown checksum type")
    if not res:
        raise Exception("generate file checksum failed")
    if dest_file:
        with open(dest_file, "w") as f:
            f.write(res)
    return res

def gen_file_checksums(file:str, checksum_types:list[ChecksumType], gen_file=False, zip_type:ZipType=None):
    checksums = {}
    try:
        zip_f = None
        if gen_file and zip_type:
            file_root, _ = os.path.splitext(file)
            zip_file = file_root + "." + zip_type.value
            zip_f = tarfile.open(zip_file, "w:gz")
        for checksum_type in checksum_types:
            checksum_file = ""
            if gen_file:
                checksum_file = file + "." + checksum_type.value
                if os.path.isfile(checksum_file):
                    os.remove(checksum_file)
            checksums[checksum_type.name] = gen_file_checksum(file, checksum_type, dest_file=checksum_file)
            if zip_f:
                zip_f.add(file, arcname=os.path.basename(file))
                zip_f.add(checksum_file, arcname=os.path.basename(checksum_file))
    finally:
        if zip_f: zip_f.close()
    return checksums

def gen_files_checksums_in_dir(dir:str, ext:str, checksum_types:list[ChecksumType], gen_file=False, zip_type:ZipType=None):
    file_checksums = {}
    for childname in os.listdir(dir):
        child = os.path.join(dir, childname)
        if os.path.isfile(child) and child.endswith("."+ext):
            file_checksums[childname] = gen_file_checksums(child, checksum_types, gen_file, zip_type)
    return file_checksums

def main(argv=None):
    arg_checksum_types = [
        ChecksumType.CKSUM.value,
        ChecksumType.MD5.value
    ]
    arg_checksum_types_help = "choose checksum type:\n"
    for checksum_type in arg_checksum_types:
        arg_checksum_types_help += "    {}\n".format(checksum_type)

    arg_zip_types = [
        ZipType.TARGZ.value
    ]
    arg_zip_type_help = "choose checksum type:\n"
    for zip_type in arg_zip_types:
        arg_zip_type_help += "    {}\n".format(zip_type)

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="Tool: Generate File Hash")
    parser.add_argument("-fsdir", "--files-dir", type=str, default="files", help="files directory")
    parser.add_argument("-fext", "--file-ext", type=str, default="txt", help="file's extension")
    parser.add_argument("-f", "--gen_file", action=argparse.BooleanOptionalAction, default=False, help="generate checksum file")
    parser.add_argument("-types", "--checksum-types", choices=arg_checksum_types, nargs="*", default=[ChecksumType.MD5], help=arg_checksum_types_help)
    parser.add_argument("-ztype", "--zip-type", choices=arg_zip_types, default="", help=arg_zip_type_help)
    args = parser.parse_args(argv)

    fsdir = os.path.abspath(args.files_dir)
    fext = args.file_ext
    checksum_types = [ChecksumType(checksum_type) for checksum_type in args.checksum_types]
    gen_file = args.gen_file
    zip_type = ZipType(args.zip_type) if len(args.zip_type) > 0 else ""

    try:
        res = gen_files_checksums_in_dir(fsdir, fext, checksum_types, gen_file, zip_type)
        print(res)
    except:
        print(traceback.format_exc())
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())