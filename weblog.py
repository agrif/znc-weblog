import znc
#from os import listdir, path
import os

class weblog(znc.Module):
    module_types = [znc.CModInfo.GlobalModule]
    description = "Allowings viewing of log files from the ZNC webadmin"

    def OnLoad(self, args, message):
        self.AddSubPage(znc.CreateWebSubPage('path', title='Set Path'))
        return True

    def WebRequiresLogin(self):
        return True

    def WebRequiresAdmin(self):
        return False

    def GetWebMenuTitle(self):
        return "Log Viewer"

    def OnWebRequest(self, sock, page, tmpl):
        user = sock.GetUser()

        dir = sock.GetParam('dir', False)
        if page == "index":
            try:
                self.listdir(tmpl, dir, user)
            except KeyError:
                sock.Redirect(self.GetWebPath() + 'path')
        elif page == "log":
            self.viewlog(tmpl, dir, user)
        elif page == "path":
            try:
                path = sock.GetRawParam('path', True)
            except:
                path = "None"
            self.setpath(path, sock, tmpl)

        return True

    def listdir(self, tmpl, dir, user):
        base = self.nv[user].replace("$USER", user)
        rel_dir = base + dir
        dir_list = sorted(os.listdir(rel_dir))

        self.breadcrumbs(tmpl, dir)

        for item in dir_list:
            short_dir = dir + '/' + item if dir else item
            full_path = base + short_dir
            row = tmpl.AddRow("ListLoop")

            if os.path.isfile(full_path):
                path = 'log?dir=' + short_dir.replace('#', '%23')
                size = str(os.path.getsize(full_path) >> 10) + " KB"
            elif os.path.isdir(full_path):
                path = '?dir=' + short_dir.replace('#', '%23')
                size = len([name for name in os.listdir(full_path)])

            row["Path"] = path
            row["Item"] = item

            row["Size"] = str(size)

    def viewlog(self, tmpl, dir,  user):
        self.breadcrumbs(tmpl, dir)
        base = self.nv[user].replace("$USER", user)
        full_path = base + dir
        row = tmpl.AddRow("LogLoop")
        with open(full_path, 'r', encoding='utf8') as log:
            log = log.read()
        row['log'] = log

    def breadcrumbs(self, tmpl, dir):
        folders = dir.split('/')
        crumbs = ['<a href="">logs / </a>']

        row = tmpl.AddRow("BreadcrumbLoop")
        row["CrumbText"] = "logs"
        row["CrumbURL"] = ""
        for i in range(0, len(folders)):
            if folders[i]:
                row = tmpl.AddRow("BreadcrumbLoop")
                row["CrumbText"] = folders[i]
                row["CrumbURL"] = '/'.join(folders[0:i+1])

    def setpath(self, path, sock, tmpl):
        user = sock.GetUser()
        row = tmpl.AddRow("MessageLoop")
        if path:
            if "$USER" not in path:
                row["Message"] = 'You must include a "$USER" variable (ALL CAPS).'
            else:
                user = sock.GetUser()
                if os.path.exists(path.replace("$USER", user)):
                    if not path.endswith('/'):
                        path = path + '/'
                    self.nv[user] = path
                    row["Message"] = "Path successfully set."
                else:
                    row["Message"] = "Path invalid."
        else:
            row["Message"] = "Please set a path."

        row = tmpl.AddRow("PathLoop")
        try:
            row["Path"] = self.nv[user]
        except KeyError:
            row["Path"] = ""