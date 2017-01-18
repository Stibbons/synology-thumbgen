#############################################
Thumbnail Generator for Synology PhotoStation
#############################################

Creating thumbnails on the consumer level DiskStation NAS boxes by Synology is incredibly slow which
makes indexing of large photo collections take forever to complete. It's much, much faster (days ->
hours) to generate the thumbnails on your desktop computer over e.g. SMB, AFP or NFS, using this
small Python script.

Usage
=====

Before starting, disable thumbnail generation from within DSM.

Install in a virtualenv:

    virtualenv --python python3 venv
    source venv/bin/activate
    pip install -r requirements.txt -e .

Usage:

    synology_thumbgen --directory <path>

Example:
- Windows: `synology_thumbgen --directory c:\photos`
- Mac: `synology_thumbgen --directory /Volumes/Photo/` (if `Photo` share is mounted in `/Volume`)

Subdirectories will always be processed.

Requirements
============

The script needs the Pillow imaing library (https://pypi.python.org/pypi/Pillow/2.5.1) to be
installed. Use `pip` and virtual env command above to install it properly in your environment.

To do after thumbnail generation
================================

Given a file and folder structure like below:

```
c:\photos\001.jpg
c:\photos\dir1\002.jpg
```

...the utility will create the following:

```
c:\photos\eaDir_tmp\001.jpg\SYNOPHOTO_THUMB_XL.jpg
c:\photos\eaDir_tmp\001.jpg\SYNOPHOTO_THUMB_B.jpg
c:\photos\eaDir_tmp\001.jpg\SYNOPHOTO_THUMB_M.jpg
c:\photos\eaDir_tmp\001.jpg\SYNOPHOTO_THUMB_PREVIEW.jpg
c:\photos\eaDir_tmp\001.jpg\SYNOPHOTO_THUMB_S.jpg
c:\photos\dir1\eaDir_tmp\002.jpg\SYNOPHOTO_THUMB_XL.jpg
c:\photos\dir1\eaDir_tmp\002.jpg\SYNOPHOTO_THUMB_B.jpg
c:\photos\dir1\eaDir_tmp\002.jpg\SYNOPHOTO_THUMB_M.jpg
c:\photos\dir1\eaDir_tmp\002.jpg\SYNOPHOTO_THUMB_PREVIEW.jpg
c:\photos\dir1\eaDir_tmp\002.jpg\SYNOPHOTO_THUMB_S.jpg
```

`eaDir_tmp` is used as a temporary directory name as synology shares (both AFP and SMB) refuse to
let us create `@eaDir` directories directly (and `@` character is not valid in file names on
Windows). Therefore, these folders must be renamed to `@eaDir` after execution for PhotoStation to
recognize the thumbnail. This renaming process must be done via SSH to the DiskStation unless the
volume is mounted by NFS.

Useful commands:

    # remove any existing thumbnail directories, dry-run check print out before running next command!
    find /volume1/photos -type d -name '@eaDir' -exec echo '{}' \;

    # remove any existing thumbnail directories
    find /volume1/photos -type d -name '@eaDir' -exec rm -rf '{}' \;

    # rename directories
    find /volume1/photos -type d -name 'eaDir_tmp' -exec mv '{}' @eaDir \;

Developer's toolbox
===================

This project uses PBR to simplify project management:
- `AUTHORS` and `ChangeLog` auto-generation: on `python setup.py sdist`
- Binaries and wheel generation: `python setup.py bdist bdist_wheel`
