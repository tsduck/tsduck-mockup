#!/usr/bin/env python
#
# Update the TSDuck mockup project using the TSDuck real project.
# Parameter: optional tsduck project directory.
#

import sys, os, shutil, glob, subprocess

SCRIPT = os.path.abspath(sys.argv[0] if __name__ == '__main__' else __file__)
SCRIPT_NAME = os.path.basename(SCRIPT)
MOCKUP_ROOT = os.path.dirname(SCRIPT)
TSDUCK_ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(MOCKUP_ROOT + '/../tsduck')

# Files to keep.
KEEP_FILES = [
    'tsVersion.h',
    'tsPlatform.h',
    'tsPreConfiguration.h',
    'tsBeforeStandardHeaders.h',
    'tsAfterStandardHeaders.h',
    'tsLibTSCoreVersion.h',
    'tsLibTSCoreVersion.cpp',
    'tscore.cpp',
    'tsduck.cpp'
]

# Dummy code.
DUMMY_CODE = '[[maybe_unused]] static int dummy = 0;\n'
DUMMY_MAIN = 'int main() {}\n'

# Print an information or error message.
def info(message):
    print('%s: %s' % (os.path.basename(SCRIPT), message), file=sys.stderr)

# Print a fatal error and exit.
def fatal(message):
    info(message)
    exit(1)

# Write the content of a text file.
def write_file(filename, content):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

# Create mockup files for specific source files.
def mockup_file(pattern, content):
    for infile in glob.glob(TSDUCK_ROOT + os.sep + pattern):
        write_file(infile.replace(TSDUCK_ROOT, MOCKUP_ROOT), content)

# Run a command and get stdout+stderr. Need a list of strings as command.
def run(cmd, err=subprocess.STDOUT, cwd=None):
    try:
        return subprocess.check_output(cmd, stderr=err, cwd=cwd).decode('utf-8')
    except:
        return ''

# Handler for rmtree() error.
def rmtree_error(func, file_path, excinfo):
    info('error removing %s' % file_path)

# Remove all files and directories in a directory, except a list of names.
def remove_tree(root, skip=[]):
    for name in os.listdir(root):
        if name not in skip:
            path = root + os.sep + name
            if os.path.isdir(path):
                shutil.rmtree(path, onerror=rmtree_error)
            else:
                os.remove(path)
    
# Handler for copytree() ignore.
def copytree_ignore(dirname, files):
    if os.path.samefile(dirname, TSDUCK_ROOT):
        # Files to ignore at top-level.
        return ['.git', 'bin', 'README.md', SCRIPT_NAME]
    elif os.path.samefile(dirname, TSDUCK_ROOT + '/.github'):
        # Do not copy .github/workflows.
        return ['workflows']
    else:
        # Any other directory: skip C++ and Java file.
        skip = ['__pycache__']
        for name in files:
            # Files to keep anyway.
            if name not in KEEP_FILES:
                # Remove all files with these extensions:
                for ext in ['.cpp', '.h', '.java']:
                    if name.endswith(ext):
                        skip.append(name)
        return skip

# Main program
if __name__ == "__main__":

    # Check root of TSDuck project.
    if not os.path.isdir(TSDUCK_ROOT):
        fatal('%s does not exist' % TSDUCK_ROOT)

    # Cleanup the mockup tree.
    remove_tree(MOCKUP_ROOT, ['.git', '.github', 'README.md', SCRIPT_NAME])
    remove_tree(MOCKUP_ROOT + '/.github', ['workflows'])

    # Copy files from the TSDuck project tree.
    shutil.copytree(TSDUCK_ROOT, MOCKUP_ROOT, symlinks=True, ignore=copytree_ignore, dirs_exist_ok=True)
    shutil.copytree(TSDUCK_ROOT + '/.github/workflows', MOCKUP_ROOT + '/.github/workflows.tsduck', symlinks=True, dirs_exist_ok=True)

    # Build dummy sources for plugins and executables.
    mockup_file('src/tsplugins/*.cpp', DUMMY_CODE)
    mockup_file('src/tstools/*.cpp', DUMMY_MAIN)
    mockup_file('src/utils/*.cpp', DUMMY_MAIN)
    write_file(MOCKUP_ROOT + '/src/libtsduck/dtv/tables/tables.cpp', DUMMY_CODE)
    write_file(MOCKUP_ROOT + '/src/libtsduck/dtv/descriptors/descriptors.cpp', DUMMY_CODE)
    write_file(MOCKUP_ROOT + '/src/libtsduck/dtv/charset/charset.cpp', DUMMY_CODE)
    write_file(MOCKUP_ROOT + '/src/libtsduck/plugins/plugins/plugins.cpp', DUMMY_CODE)
    write_file(MOCKUP_ROOT + '/src/utest/utest.cpp', DUMMY_MAIN)

    # Run the cleanup code.
    print(run([MOCKUP_ROOT + '/scripts/cleanup.py']), end='')
