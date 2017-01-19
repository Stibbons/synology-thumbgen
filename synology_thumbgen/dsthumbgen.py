import argparse
import errno
import logging
import os
import re
import sys
import time

from multiprocessing import cpu_count
from multiprocessing import Pool
from multiprocessing import Value
from PIL import ExifTags
from PIL import Image


class State(object):
    def __init__(self, args):
        self.counter = Value('i', 0)
        self.start_ticks = Value('d', time.perf_counter())
        self.args = args

    def increment(self, n=1):
        with self.counter.get_lock():
            self.counter.value += n

    @property
    def value(self):
        return self.counter.value

    @property
    def start(self):
        return self.start_ticks.value


def init(args):
    global state
    state = args


def main():
    FORMAT = '%(asctime)-15s - %(levelname)-8s - %(message)s'
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format=FORMAT)
    state = State(args)

    logging.info("Starting conversion script")
    logging.info("Finding files to convert...")
    files = find_files(args.directory)

    nb_cores = cpu_count()

    with Pool(processes=nb_cores, initializer=init, initargs=(state, )) as pool:
        for _ in pool.imap_unordered(process_file, files, chunksize=10):
            pass

    logging.info("{0} files processed in total.".format(state.value))
    logging.info("Do not forget to log to your Synology in SSH and manually rename "
                 "eaDir directories. See README.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create thumbnails for Synology Photo Station.")
    parser.add_argument("--directory", required=True,
                        help=("Directory to generate thumbnails for. "
                              "Subdirectories will always be processed."))
    parser.add_argument("--no-tmp", action="store_true", dest="no_tmp",
                        help=("Create '@eaDir' directly. "
                              "Use it if you have configured the NFS share."))
    parser.add_argument("--verbose", action="store_true", dest="verbose",
                        help=("Enable verbose logging."))
    parser.add_argument("--overwrite", action="store_true", dest="overwrite",
                        help=("Overwrite existing thumbnail."))

    return parser.parse_args()


def find_files(dir):
    valid_exts = ('jpeg', 'jpg', 'bmp', 'gif')
    valid_exts_re = "|".join(
        map((lambda ext: ".*\\.{0}$".format(ext)), valid_exts))

    for root, dirs, files in os.walk(dir):
        for name in files:
            if (re.match(valid_exts_re, name, re.IGNORECASE) and
                    not name.startswith('SYNOPHOTO_THUMB') and
                    "#recycle" not in root):
                yield os.path.join(root, name)
            else:
                logging.debug("Ignoring  : %s/%s", root, name)


def print_progress():
    global state
    state.increment(1)
    processed = state.value
    if processed % 10 == 0:
        logging.info("{0} files processed so far, averaging {1:.2f} files per second."
                     .format(processed,
                             float(processed) / (float(time.perf_counter() - state.start))))


def process_file(file_path):
    logging.debug("Processing: %r", file_path)

    (dir, filename) = os.path.split(file_path)

    global state
    if not state.args.no_tmp:
        thumb_dir = os.path.join(dir, 'eaDir_tmp', filename)
    else:
        thumb_dir = os.path.join(dir, '@eaDir', filename)
    ensure_directory_exists(thumb_dir)

    create_thumbnails(file_path, thumb_dir)

    print_progress()


def ensure_directory_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def create_thumbnails(source_path, dest_dir):
    to_generate = (('SYNOPHOTO_THUMB_XL.jpg', 1280),
                   ('SYNOPHOTO_THUMB_B.jpg', 640),
                   ('SYNOPHOTO_THUMB_M.jpg', 320),
                   ('SYNOPHOTO_THUMB_PREVIEW.jpg', 160),
                   ('SYNOPHOTO_THUMB_S.jpg', 120))
    jpeg_quality = 70
    im_read = 0

    for thumb in to_generate:
        thumb_filename = os.path.join(dest_dir, thumb[0])
        if not state.args.overwrite and os.path.exists(thumb_filename):
            continue
        if im_read == 0:
            try:
                im = Image.open(source_path)
            except:
                logging.exception("Error opening image %s. Ignoring it.", source_path)
                return
            logging.debug("Reading: %s", source_path)
            im_read = 1
        logging.debug("Generating: %s", thumb_filename)
        try:
            im.thumbnail((thumb[1], thumb[1]), Image.ANTIALIAS)
        except:
            logging.exception("Thumbnail generation failure on: %s. Continueing...", source_path)
        try:
            if hasattr(im, '_getexif'):
                exif = {ExifTags.TAGS[k]: v
                        for k, v in im._getexif().items()
                        if k in ExifTags.TAGS}
                orientation = exif.get("Orientation", 1)
                if orientation == 3:
                    logging.debug("Rotating thumbnail 180 deg")
                    im = im.rotate(180, expand=True)
                elif orientation == 6:
                    logging.debug("Rotating thumbnail 270 deg")
                    im = im.rotate(270, expand=True)
                elif orientation == 8:
                    logging.debug("Rotating thumbnail 90 deg")
                    im = im.rotate(90, expand=True)
        except:
            logging.exception("Cannot get EXIF information for %s", source_path)
        im.save(thumb_filename, quality=jpeg_quality)


if __name__ == "__main__":
    sys.exit(main())
