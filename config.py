
# Vendor modules
import os
import ConfigParser as configparser
# Local modules
import table

def load(exec_path):
    # Normalize and extract exec_dir from exex_path file name
    exec_relpath = os.path.realpath(exec_path)
    exec_dir = os.path.dirname(exec_relpath)
    exec_name = os.path.basename(exec_relpath)

    conf_file = '.settings.conf'
    conf_path = os.path.join(exec_dir, conf_file)

    try:
        fp = open(conf_path, 'r')
    except OSError:
        die('Failed to read config')

    config = configparser.ConfigParser()
    config.readfp(fp)

    options = table.Table(config.defaults())

    # Update options values
    normalize(options, exec_dir, exec_name)
    # Execute default options
    execute(options)

    return options

def normalize(options, exec_dir, exec_name):
    if not options.base_dir:
        options.base_dir = exec_dir

    if not options.exec_name == '':
        options.exec_name = exec_name

def execute(options):
    os.chdir(options.base_dir)
    if options.log_dir and not os.path.exists(options.log_dir):
        os.mkdir(options.log_dir)
    if options.cache_dir and not os.path.exists(options.cache_dir):
        os.mkdir(options.cache_dir)
    if options.archive_dir and not os.path.exists(options.archive_dir):
        os.mkdir(options.archive_dir)
    if options.storage_dir and not os.path.exists(options.storage_dir):
        os.mkdir(options.storage_dir)
