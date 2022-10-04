from copy import deepcopy
import shlex


class File:

    def __init__(self, parent=0, name="/", size=0, dir=True, hidden=False, user="root"):
        self.parent = parent
        self.name = name
        self.size = size
        self.dir = dir
        self.hidden = hidden
        self.subdir = []
        self.fullpath = ""
        self.owner = user
        if self.dir:
            self.permission = "drwxr-x"
        else:
            self.permission = "-rw-r--"

    def __repr__(self) -> str:
        return self.fullpath

    def uperm(self) -> str:
        return self.permission[1:4]

    def operm(self) -> str:
        return self.permission[4:]

    def type(self) -> str:
        return self.permission[0]


fs = []
curDir = 0
usergroup = []
user = "root"
IS_EXIT = False
permission = {}


def newSession():
    fs.clear()
    fs.append(File())
    curDir = 0
    fs[curDir].fullpath = '/'
    fs[curDir].onwer = user
    curDir = 0
    IS_EXIT = False
    global usergroup
    usergroup = []
    usergroup.append("root")


def invalid_syntax(command: str):
    return command+": Invalid syntax"


def command_not_found(command: str):
    return command+": Command not found"


def findFileInDirectory(node: int, name: str):
    # print(fs)
    subdir = fs[node].subdir
    for i in subdir:
        if fs[i].name == name:
            return i
    return -1


def printDetail(i, name=""):
    s = fs[i].permission+" "+fs[i].owner+" "
    if name != "":
        s += name
    else:
        s += fs[i].name
    return s


# def checkPermissionInAncestor(permission,path: str):
#     if path == "":
#         return checkpermission(curDir,permission,user)
#     node = curDir
#     if path[0] == "/":
#         node = 0
#     dirs = list(filter(None, path.split("/")))
#     for i in dirs:
#         if checkpermission(node,permission,user)==False:
#             return False
#         if i == ".":
#             continue
#         elif i == "..":
#             if node == 0:
#                 return 0
#             node = fs[node].parent
#         else:
#             x = findFileInDirectory(node, i)
#             if x == -1:
#                 return -1
#             node = x
#     return checkpermission(node,permission,user)


def getDirNode(path: str):
    if path == "":
        return curDir
    node = curDir
    if path[0] == "/":
        node = 0
    dirs = list(filter(None, path.split("/")))
    for i in dirs:
        if i == ".":
            continue
        elif i == "..":
            if node == 0:
                return 0
            node = fs[node].parent
        else:
            x = findFileInDirectory(node, i)
            if x == -1:
                return -1
            node = x
    return node


def createDirs(path: str):
    if path == "":
        return curDir
    node = curDir
    if path[0] == "/":
        node = 0
    dirs = list(filter(None, path.split("/")))
    # print(dirs)
    for i in dirs:
        x = findFileInDirectory(node, i)
        if x == -1:
            x = createFileInDirectory(node, i, True, False)
        node = x
    return node


def joinPath(path: str, name: str) -> str:
    if path[-1] != "/":
        path += "/"
    return path+name


def getAbsolutePath(node):
    if node == 0:
        return "/"
    return joinPath(getAbsolutePath(fs[node].parent), fs[node].name)


def checks(s: str) -> bool:
    if len(s) < 2:
        return False
    if s[0] not in "uoa":
        return False
    if s[1] not in "-+=":
        return False
    if len(s) == 2:
        return True
    else:
        for i in s[2:]:
            if i not in "rwx":
                return False
        return True


def createFileInDirectory(node: int, name: str, dir: bool, hidden):
    fs.append(File(parent=node, name=name, dir=dir, hidden=hidden))
    x = len(fs)-1
    fs[x].fullpath = joinPath(getAbsolutePath(node), name)
    fs[x].owner = user
    fs[node].subdir.append(x)
    return x


def removeFileInDirectory(node: int, name: str, x: int):
    fs[x] = None
    fs[node].subdir.remove(x)


def sortedInDetail(res):
    items = [i.split(" ") for i in res]
    # print(items)
    newRes = sorted(items, key=lambda x: x[2])
    # print(newRes)
    newRes = [" ".join(i) for i in newRes]
    return newRes


def splitFilename(fullpath: str):
    f = fullpath.split("/")
    dir = f[:-1]
    dirs = "/".join(dir)
    filename = f[-1]
    return getDirNode(dirs), filename


def FindFileorDir(path: str):
    dir, file = splitFilename(path)
    if file == "":
        return getDirNode(path)
    else:
        return findFileInDirectory(dir, file)


def checkpermission(node, checktype, nowuser):
    if nowuser == "root":
        return True
    if fs[node].owner == nowuser:
        p = fs[node].uperm()
    else:
        p = fs[node].operm()
    # print(node,checktype,nowuser,p)
    if checktype in p:
        return True
    else:
        return False


def permission_denied(cmd):
    return cmd+": Permission denied"


def setperm(perm, op, perm2="---"):
    p = perm2
    for item in perm:
        if item == "r":
            if op in "+=":
                p = "r"+p[1:]
            else:
                p = "-"+p[1:]
        if item == 'w':
            if op in "+=":
                p = p[0]+"w"+p[2:]
            else:
                p = p[0]+"-"+p[2:]
        if item == "x":
            if op in "+=":
                p = p[0:2]+"x"
            else:
                p = p[0:2]+"-"
    return p


def changeMod(node: int, newmod: str):
    operm = fs[node].operm()
    uperm = fs[node].uperm()
    type = fs[node].type()
    uoa = newmod[0]
    op = newmod[1]
    perm = ""
    if len(newmod) > 2:
        perm = newmod[2:]
    if op == "=":
        if uoa == "o" or uoa == "a":
            operm = setperm(perm, op)
        if uoa == "u" or uoa == "a":
            uperm = setperm(perm, op)
    else:
        if uoa == "o" or uoa == "a":
            operm = setperm(perm, op, operm)
        if uoa == "u" or uoa == "a":
            uperm = setperm(perm, op, uperm)
    fs[node].permission = type+uperm+operm


def changemode(s, path):
    node = FindFileorDir(path)
    dir, file = splitFilename(path)

    def change(s: str):
        prev = ""; after = ""; mid = ""
        for i in range(len(s)):
            if s[i] in "+-=":
                prev = s[:i]
                after = s[i+1:]
                mid = s[i]
        p = ""; a = ""
        for item in prev:
            if item not in "uoa":
                return item+mid+after
            if "u" in prev and "o" not in prev and "a" not in prev:
                p = "u"
            elif "o" in prev and "u" not in prev and "a" not in prev:
                p = "o"
            else:
                p = "a"
            a = after
            return p+mid+a
    s=change(s)
    if node == -1:
        return "chmod: No such file or directory"
    if checkpermission(dir,"w",user)==False:
        return "chmod: Operation not permitted"
    if checks(s) == False:
        return "chmod: Invalid mode"
    if fs[node].owner != user and user != "root":
        return "chmod: Operation not permitted"
    changeMod(node, s)
    return ""
def changeModeRecur(s,path):
    Q=[]
    node=FindFileorDir(path)
    Q.append(node)
    msg=[]
    while len(Q):
        front=Q.pop(0)
        
        m=changemode(s,fs[front].fullpath)
        # print(fs[front].fullpath,m)
        if m!="":
            msg.append(m) 
        for i in fs[front].subdir:
            Q.append(i)
    return msg
def runCommandLine(commandLine: str):
    commandLine = commandLine.strip()
    if commandLine == "":
        return ""
    # commandLine=commandLine.split(" ")
    shlexLine = shlex.split(commandLine)
    params = shlexLine[1:]
    # print(shlexLine,params)
    command = shlexLine[0]
    for item in params:
        if "@" in item or "!" in item:
            return invalid_syntax(command)

    if command == "exit":
        if len(params) != 0:
            return invalid_syntax(command)
        global IS_EXIT
        IS_EXIT = True
        global user
        return "bye, "+user
    elif command == "pwd":
        if len(params) != 0:
            return invalid_syntax(command)
        global curDir
        return fs[curDir].fullpath
    elif command == "mkdir":
        # print(params)
        if len(params) == 1:
            node, filename = splitFilename(params[0])
            if checkpermission(node,"w",user)==False:
                return permission_denied(command)
            if checkpermission(node,"x",user)==False:
                return permission_denied(command)
            if node == -1:
                return "mkdir: Ancestor directory does not exist"
            x = findFileInDirectory(node, filename)
            if x != -1:
                return "mkdir: File exists"
            
            createFileInDirectory(node, filename, True, False)
            return ""
        elif len(params) == 2 and params[0] == "-p":
            node, filename = splitFilename(params[1])
            if node == -1:
                createDirs(params[1])
            else:
                createFileInDirectory(node, filename, True, False)
            return ""
        else:
            return invalid_syntax(command)
    elif command == "touch":
        if len(params) != 1:
            return invalid_syntax(command)
        node, filename = splitFilename(params[0])
        if node == -1:
            return "touch: Ancestor directory does not exist"
        if checkpermission(node,"x",user)==False:
            return permission_denied(command)
        if checkpermission(node,"w",user)==False:
            return permission_denied(command)
        x = findFileInDirectory(node, filename)
        if x == -1:
            createFileInDirectory(node, filename, False, False)
        return ""
    elif command == "cd":
        if len(params) != 1:
            return invalid_syntax(command)
        node = getDirNode(params[0])

        if node == -1:
            return "cd: No such file or directory"
        if fs[node].dir == False:
            return "cd: Destination is a file"
        if checkpermission(node, "x", user) == False:
            return permission_denied(command)
        curDir = node
        return ""
    elif command == "cp":
        if len(params) != 2:
            return invalid_syntax(command)
        else:
            src = params[0]
            dst = params[1]
            dstnode, dstfilepath = splitFilename(dst)
            if dstnode == -1 or fs[dstnode].dir == False:
                return "cp: No such file or directory"
            
            dstx = findFileInDirectory(dstnode, dstfilepath)
            if dstx != -1:
                if fs[dstx].dir == True:
                    return "cp: Destination is a directory"
                return "cp: File exists"
            srcnode, srcfilepath = splitFilename(src)
            srcx = findFileInDirectory(srcnode, srcfilepath)
            if srcx == -1:
                return "cp: No such file"
            if fs[srcx].dir == True:
                return "cp: Source is a directory"
            if checkpermission(srcnode,"x",user)==False or checkpermission(dstnode,"x",user)==False:
                return permission_denied(command)
            if checkpermission(srcnode,"w",user)==False or checkpermission(dstnode,"w",user)==False:
                return permission_denied(command)
            if checkpermission(srcx,"r",user)==False or checkpermission(dstx,"r",user)==False:
                return permission_denied(command)
            createFileInDirectory(dstnode, dstfilepath, False, False)
            return ""
    elif command == "mv":
        if len(params) != 2:
            return invalid_syntax(command)
        else:
            src = params[0]
            dst = params[1]
            srcnode, srcfilename = splitFilename(src)
            dstnode, dstfilename = splitFilename(dst)

            if dstnode == -1:
                return "mv: No such file or directory"
            elif fs[dstnode].dir == False:
                return "mv: No such file or directory"
            dstx = findFileInDirectory(dstnode, dstfilename)
            if dstx != -1:
                if fs[dstx].dir == True:
                    return "mv: Destination is a directory"
                return "mv: File exists"
            if srcnode == -1:
                return "mv: No such file"
            srcx = findFileInDirectory(srcnode, srcfilename)
            if srcx == -1:
                return "mv: No such file"
            if fs[srcx].dir == True:
                return "mv: Source is a directory"
            if checkpermission(srcnode,"x",user)==False or checkpermission(dstnode,"x",user)==False:
                return permission_denied(command)
            if checkpermission(srcnode,"w",user)==False or checkpermission(dstnode,"w",user)==False:
                return permission_denied(command)
            if checkpermission(srcx,"r",user)==False or checkpermission(dstx,"r",user)==False:
                return permission_denied(command)
            createFileInDirectory(dstnode, dstfilename, False, False)
            removeFileInDirectory(srcnode, srcfilename, srcx)
            return ""
    elif command == "rm":
        if len(params) != 1:
            return invalid_syntax(command)
        else:
            rmnode, rmfilename = splitFilename(params[0])
            if rmnode == -1:
                return "rm: No such file"
            elif fs[rmnode].dir == False:
                return "rm: No such file"
            rmfile = findFileInDirectory(rmnode, rmfilename)
            if rmfile == -1:
                return "rm: No such file"
            elif fs[rmfile].dir == True:
                return "rm: Is a directory"
            if checkpermission(rmfile,"w",user)==False:
                return permission_denied(command)
            if checkpermission(rmnode,"x",user)==False:
                return permission_denied(command)
            if checkpermission(rmnode,"w",user)==False:
                return permission_denied(command)
            removeFileInDirectory(rmnode, rmfilename, rmfile)
            return ""
    elif command == "rmdir":
        if len(params) != 1:
            return invalid_syntax(command)
        else:
            rmdir = getDirNode(params[0])
            if rmdir == -1:
                return "rmdir: No such file or directory"
            
            elif fs[rmdir].dir == False:
                return "rmdir: Not a directory"
            elif checkpermission(fs[rmdir].parent,"w",user)==False:
                return permission_denied(command)
            elif checkpermission(fs[rmdir].parent,"x",user)==False:
                return permission_denied(command)
            else:
                subdir = fs[rmdir].subdir
                if len(subdir) != 0:
                    return "rmdir: Directory not empty"
                if curDir == rmdir:
                    return "rmdir: Cannot remove pwd"
                rmnode, rmfilename = splitFilename(params[0])
                rmfile = findFileInDirectory(rmnode, rmfilename)
                removeFileInDirectory(rmnode, rmfilename, rmfile)
                return ""
    elif command == "chmod":
        if len(params) == 2:
            s = params[0]
            path = params[1]
            node = FindFileorDir(path)
            dir,file=splitFilename(path)
            def change(s:str):
                prev=""; after="";mid=""
                for i in range(len(s)):
                    if s[i] in "+-=":
                        prev=s[:i]
                        after=s[i+1:]
                        mid=s[i]
                p="";a=""
                for item in prev:
                    if item not in "uoa":
                        return item+mid+after
                if "u" in prev and "o" not in prev and "a" not in prev:
                    p="u"
                elif "o" in prev and "u" not in prev and "a" not in prev:
                    p="o"
                else:
                    p="a"
                a=after
                return p+mid+a
            s=change(s)
            if node == -1:
                return "chmod: No such file or directory"
            if checkpermission(dir,"w",user)==False:
                return permission_denied(command)
            if checks(s) == False:
                return "chmod: Invalid mode"
            if fs[node].owner != user and user != "root":
                return "chmod: Operation not permitted"
            changeMod(node, s)
            return ""
        elif len(params) == 3:
            if params[0]!="-r":
                return invalid_syntax(command)
            else:
                s = params[1]
                path = params[2]
                msg=changeModeRecur(s,path)
                msg=sorted(msg)
            return "\n".join(msg)
        else:
            return invalid_syntax(command)
    elif command == "chown":
        if user != "root":
            return "chown: Operation not permitted"
        if len(params) == 2:
            u = params[0]
            path = params[1]
            node = FindFileorDir(path)
            if u not in usergroup:
                return "chown: Invalid user"
            if node == -1:
                return "chown: No such file or directory"
            fs[node].owner = u
            return ""
        elif len(params) == 3:
            if params[0]!="-r":
                return invalid_syntax(command)
            u=params[1]
            path=params[2]
            node=FindFileorDir(path)
            if u not in usergroup:
                return "chown: Invalid user"
            if node == -1:
                return "chown: No such file or directory"
            def chown_file(user,node):
                if user not in usergroup:
                    return "chown: Invalid user"
                if node == -1:
                    return "chown: No such file or directory"
                fs[node].owner = u
                return ""
            Q=[]
            Q.append(node)
            msg=[]
            while len(Q):
                front=Q.pop(0)
        
                m=chown_file(user,front)
                # print(fs[front].fullpath,m)
                if m!="":
                    msg.append(m) 
                for i in fs[front].subdir:
                    Q.append(i)
            msg=sorted(msg)
            return "\n".join(msg)
        else:
            return invalid_syntax(command)
    elif command == "adduser":
        if len(params) != 1:
            return invalid_syntax(command)
        if user != "root":
            return "adduser: Operation not permitted"
        user_toadd = params[0]
        if user_toadd in usergroup:
            return "adduser: The user already exists"
        else:
            usergroup.append(user_toadd)
            return ""
    elif command == "deluser":
        if len(params) != 1:
            return invalid_syntax(command)
        user_todel = params[0]
        if user != "root":
            return "deluser: Operation not permitted"
        if user_todel not in usergroup:
            return "deluser: The user does not exist"
        elif user_todel == "root":
            return '''WARNING: You are just about to delete the root account
Usually this is never required as it may render the whole system unusable
If you really want this, call deluser with parameter --force
(but this `deluser` does not allow `--force`, haha)
Stopping now without having performed any action'''
        else:
            usergroup.remove(user_todel)
            if user_todel == user:
                user = "root"
            return ""
    elif command == "su":
        # print(usergroup,params)
        if len(params) == 0 or params[0] == "root":
            user = "root"
            return ""
        elif len(params) == 1:
            if params[0] not in usergroup:
                return "su: Invalid user"
            else:
                user = params[0]
                return ""
        else:
            return invalid_syntax(command)
    elif command == "ls":
        option = []
        path = "#"
        for item in params:
            if item[0] == "-":
                if item not in ["-a", "-d", "-l"]:
                    return invalid_syntax(command)
                option.append(item)
            else:
                path = item
        noarg = False
        if path == "#":
            path = fs[curDir].fullpath
            noarg = True
        dir, file = splitFilename(path)
        findfile = findFileInDirectory(dir, file)
        if findfile != -1:
            node = findfile
        else:
            node = getDirNode(path)
        res = []
        if node == -1:
            return "ls: No such file or directory"
        isDir=fs[node].dir
        if isDir and checkpermission(node,"r",user)==False:
            return permission_denied(command)
        if (not isDir or "-d"  in option) and checkpermission(dir,"r",user)==False:
            return permission_denied(command)
        if checkpermission(dir,"x",user)==False:
            return permission_denied(command)
        if noarg:
            if fs[node].dir == False:
                name = fs[node].name
                if node == curDir:
                    name = "."
                if name[0] == ".":
                    flag = True
                    if "-a" not in option:
                        flag = False
                    if flag and "-l" in option:
                        info = fs[node].permission+" "+fs[node].owner+" "+name
                        res.append(info)
                    elif flag:
                        info = name
                        res.append(info)
                else:
                    if flag and "-l" in option:
                        info = fs[node].permission+" "+fs[node].owner+" "+name
                        res.append(info)
                    elif flag:
                        info = name
                        res.append(info)
            else:
                if "-d" in option:
                    name = fs[node].name
                    if node == curDir:
                        name = "."
                    if name[0] == ".":
                        flag = True
                        if "-a" not in option:
                            flag = False
                        if flag and "-l" in option:
                            info = fs[node].permission + \
                                " "+fs[node].owner+" "+name
                            res.append(info)
                        elif flag:
                            info = name
                            res.append(info)
                    else:
                        if "-l" in option:
                            info = fs[node].permission + \
                                " "+fs[node].owner+" "+name
                            res.append(info)
                        elif flag:
                            info = name
                            res.append(info)
                else:
                    subdir = deepcopy(fs[node].subdir)
                    subdir.append(node)
                    if fs[node].parent != node:
                        subdir.append(fs[node].parent)
                    if node == fs[node].parent:
                        subdir.append(-1)
                    for i in subdir:
                        if i == -1:
                            name = ".."
                        else:
                            name = fs[i].name
                            if i == node:
                                name = '.'
                            if i == fs[node].parent and node != fs[node].parent:
                                name = '..'
                        if name[0] == ".":
                            if "-a" not in option:
                                continue
                            if "-l" in option:
                                if i == -1:
                                    info = fs[0].permission + \
                                        " "+fs[0].owner+" "+".."
                                elif i == node or i == fs[node].parent:
                                    info = fs[i].permission + \
                                        " "+fs[i].owner+" "+name
                                else:
                                    info = printDetail(i)
                                res.append(info)
                            else:
                                info = name
                                res.append(info)
                        else:
                            if "-l" in option:
                                info = printDetail(i)
                                if i == node or i == fs[node].parent:
                                    info = fs[i].permission + \
                                        " "+fs[i].owner+" "+name
                                res.append(info)
                            else:
                                info = name
                                res.append(info)
        else:
            if fs[node].dir == False:
                name = fs[node].name
                if name[0] == "." or path[0] == '.':
                    flag = True
                    if "-a" in option:
                        flag = False
                    if not flag and "-l" in option:
                        info = printDetail(node, path)
                        res.append(info)
                    elif not flag:
                        info = path
                        res.append(info)
                else:
                    if "-l" in option:
                        info = printDetail(node, path)
                        res.append(info)
                    else:
                        info = path
                        res.append(info)
            else:
                flag = False
                if "-d" in option:
                    name = path
                    if name[0] == '.':
                        if "-a" in option:
                            flag = True
                        if flag and "-l" in option:
                            info = printDetail(node, path)
                            res.append(info)
                        elif flag:
                            info = path
                            res.append(info)
                    else:
                        if "-l" in option:
                            info = printDetail(node, path)
                            res.append(info)
                        else:
                            info = path
                            res.append(info)
                else:
                    subdir = deepcopy(fs[node].subdir)
                    subdir.append(node)
                    if fs[node].parent != -1 and node != fs[node].parent:
                        subdir.append(fs[node].parent)
                    if node == fs[node].parent:
                        subdir.append(-1)
                    for i in subdir:
                        if i == -1:
                            name = ".."
                        else:
                            name = fs[i].name
                            if i == node:
                                name = '.'
                            if i == fs[node].parent and node != fs[node].parent:
                                name = '..'
                        if name[0] == ".":
                            if "-a" not in option:
                                continue
                            if "-l" in option:
                                info = printDetail(i)
                                if name == "." or name == "..":
                                    info = fs[i].permission + \
                                        " "+fs[i].owner+" "+name
                                res.append(info)
                            else:
                                info = name
                                res.append(info)
                        else:
                            if "-l" in option:
                                if i == node:
                                    info = printDetail(i, path)
                                else:
                                    info = printDetail(i)
                                if name == "." or name == "..":
                                    info = fs[i].permission + \
                                        " "+fs[i].owner+" "+name
                                res.append(info)
                            else:
                                if i == node:
                                    info = path
                                else:
                                    info = name
                                res.append(info)
        res = sorted(res)
        if "-l" in option:
            res = sortedInDetail(res)
        # print(res)
        return "\n".join(res)
    else:
        return command_not_found(command)


def main():
    newSession()
    cmd = ""
    while True:
        path = fs[curDir].fullpath
        cmd = input(user+":"+path+"$ ")
        output = runCommandLine(cmd)
        if output != "":
            print(output)
        if IS_EXIT:
            exit(0)


def test():
    # print(splitFilename("a/b/c/d"))
    return ""


if __name__ == '__main__':
    main()
