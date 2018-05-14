#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys
import imp
import marshal
from pocsuite.lib.core.data import conf
from pocsuite.lib.core.data import paths
from pocsuite.lib.core.exception import PocsuiteValueException


def string_importer(fullname, content):
    """
    Use custom meta hook to import modules available as strings.
    https://www.python.org/dev/peps/pep-0302/#specification-part-1-the-importer-protocol
    https://docs.python.org/3/library/importlib.html
    http://python3-cookbook.readthedocs.io/zh_CN/latest/c10/p11_load_modules_from_remote_machine_by_hooks.html
    """
    try:
        return sys.modules[fullname],
    except KeyError:
        pass

    mod = sys.modules.setdefault(fullname, imp.new_module(fullname))
    mod.__file__ = "<{}>".format(fullname)
    mod.__package__ = ''

    if conf.is_pyc_file:
        try:
            code = marshal.loads(content[8:])
        except ValueError:
            raise PocsuiteValueException("pyc file can not be read")
    else:
        code = compile(content, mod.__file__, "exec")

    exec(code, mod.__dict__)

    return mod


def multiple_replace(text, adict):
    """
    学到了，
    这么做的话即使内部文件结构发生变化，
    也可以继续使用旧有的导入路径而不做更改

    >>>text
    from pocsuite.net import
    from pocsuite.poc import
    from pocsuite.utils import
    >>>adict
    {
        "from pocsuite.net import": "from pocsuite.lib.request.basic import",
        "from pocsuite.poc import": "from pocsuite.lib.core.poc import",
        "from pocsuite.utils import register": \
            "from pocsuite.lib.core.register import registerPoc as register",
    }
    >>>text = multiple_replace(text, adict)
    >>>text
    from pocsuite.lib.request.basic import
    from pocsuite.lib.core.poc import
    from pocsuite.lib.core.register import registerPoc as register
    """
    rx = re.compile("|".join((re.escape(i) for i in adict)))

    def one_xlat(match):
        return adict[match.group(0)]

    return rx.sub(one_xlat, text)
    # re.sub(rx, one_xlat, text)


def file_path_parser(path):
    """
    ntpath是win用的，
    也不是不能跑，但越过os.path不就把跨平台但优势给干没了吗

    >> file_path_parser("/tmp/poc/poc_1_0_test.py")
    >> ("tmp/poc", "poc_1_0_test")

    >> file_path_parser("poc_1_0_test.py")
    >> ("", poc_1_0_test)
>> file_path_parser("poc_1_0_test")
    >> ("", poc_1_0_test)
    """

    return os.path.split(os.path.splitext(path)[0])


def parse_target_url(url):
    """
    自动给url加协议头
    只验证了http/https/ws/wss
    """

    if re.search("^http[s]*://", url, re.I) or \
            re.search("^ws[s]*://", url, re.I):

        return url

    if re.search(":443[/]*$", url):
        url = "".join(["https://", url])
    else:
        url = "".join(["http://", url])

    return url


def del_module(mod_name, paranoid=None):
    try:
        mod = sys.modules[mod_name]
    except KeyError:
        # raise ValueError(mod_name)
        pass
    else:
        del sys.modules[mod]

    # TODO

    # paranoid


def set_paths():
    paths.POCSUITE_DATA_PATH = os.path.join(paths.POCSUITE_ROOT_PATH, "data")
    paths.USER_AGENTS = os.path.join(paths.POCSUITE_DATA_PATH,
                                     "user-agents.txt")
    paths.WEAK_PASS = os.path.join(paths.POCSUITE_DATA_PATH,
                                   "password-top100.txt")
    paths.LARGE_WEAK_PASS = os.path.join(paths.POCSUITE_DATA_PATH,
                                         "password-top100.txt")
    paths.POCSUITE_HOME_PATH = os.path.expanduser("~")

    _pocsuite = os.path.join(paths.POCSUITE_HOME_PATH, ".pocsuite")
    _output = os.path.join(_pocsuite, "output")
    paths.POCSUITE_OUTPUT_PATH = paths.POCSUITE_OUTPUT_PATH or _output

    paths.POCSUITE_RC_PATH = os.path.join(paths.POCSUITE_HOME_PATH,
                                          ".pocsuiterc")
