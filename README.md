# copy_tmp
A simple python tool to catch temporary files.  
In some cases, files are protected from copying even with the privilege escalation (for example, antivirus files). For such situations, you can use the help of [RawCopy.exe](https://github.com/jschicht/RawCopy), which must be placed in the script directory or specify the full path to the executable file.

---
```
usage: copy_tmp.py [-h] -from from\dir\path -to to\dir\path [-checkdirs] [-kill procname.exe] [-once] [-exc extension]
                   [-d milliseconds] [-rc] [-rcpath path\to\RC]

optional arguments:
  -h, --help           show this help message and exit
  -from from\dir\path  path to the dir to catch file.
  -to to\dir\path      path to the dir to store file.
  -checkdirs           check dirs and their contents at 1st level.
  -kill procname.exe   if access denied try to kill a process by name. multiple -kill supported.
  -once                kills the specified process once without repeating.
  -exc extension       exclude extension from monitoring. multiple -exc supported.
  -d milliseconds      delay between file checks in milliseconds. 200 is default.
  -rc                  use RawCopy.exe to copy blocked files.
  -rcpath path\to\RC   path to the RawCopy.exe. "script dir\RawCopy.exe" is default.
```
---
