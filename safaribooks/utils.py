import errno
import os


def pkg_path(relpath):
    """Return a directory relative to the package root"""
    dirname = os.path.dirname(__file__)
    return os.path.join(dirname, os.path.expanduser(relpath))


def mkdirp(path):
    """Creates all non-existing directories encountered in the passed in path

    Args:
        path (str):
            Path containing directories to create

    Returns:
        str: The passed in path

    Raises:
        OSError:
            If some underlying error occurs when calling :func:`os.makedirs`,
            that is not errno.EEXIST.
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

    return path
