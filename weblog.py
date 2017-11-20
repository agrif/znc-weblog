import znc
import os

def is_safe_path(basedir, path):
    return os.path.abspath(path).startswith(basedir)

class weblog(znc.Module):
    module_types = [znc.CModInfo.GlobalModule]
    description = "Allowings viewing of log files from the ZNC webadmin"
    wiki_page = "Weblog"

    def OnLoad(self, args, message):
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
            if sock.GetRawParam('scope', True):
                scope = sock.GetRawParam('scope', True)
                self.setscope(scope, sock, tmpl)
            try:
                self.listdir(tmpl, dir, sock)
            except KeyError:
                row = tmpl.AddRow("ErrorLoop")
                row["error"] = "No scope set. Please set one above."
        elif page == "log" or page == "raw":
            self.viewlog(tmpl, dir, sock, page)
        self.getscopes(sock, tmpl)

        return True

    def listdir(self, tmpl, dir, sock):
        base = self.getbase(sock)

        try:
            dir_list = sorted(os.listdir(base + dir))

            self.breadcrumbs(tmpl, dir, False)

            if len(dir_list) > 0:
                for item in dir_list:
                    row = tmpl.AddRow("ListLoop")

                    rel = dir + '/' + item if dir else item

                    path = base + rel

                    if os.path.isfile(path):
                        url = 'log?dir=' + rel.replace('#', '%23')
                        size = str(os.path.getsize(path) >> 10) + " KB"
                    elif os.path.isdir(path):
                        url = '?dir=' + rel.replace('#', '%23')
                        size = len([name for name in os.listdir(path)])

                    row["scope"] = url
                    row["item"] = item

                    row["size"] = str(size)

            else:
                row = tmpl.AddRow("ErrorLoop")
                row["error"] = "Directory empty."

        except FileNotFoundError:
            row = tmpl.AddRow("ErrorLoop")
            row["error"] = "Directory does not exist. Please make sure you have the log module enabled and that you are attempting to access logs at the appropriate level (global, user, or network)."

    def viewlog(self, tmpl, dir, sock, page):
        base = self.getbase(sock)

        if not is_safe_path(base, base + dir):
            if page == "raw":
                row = tmpl.AddRow("LogLoop")
                row['log'] = "Error: invalid directory provided."
                return
            row = tmpl.AddRow("ErrorLoop")
            row["error"] = "Invalid directory provided."
            return

        path = base + dir
        row = tmpl.AddRow("LogLoop")
        with open(path, 'r', encoding='utf8') as log:
            log = log.read()
        if page == "raw":
            log = log.replace('<', '&lt;').replace('>', '&gt;')
        row['log'] = log
        if page == "log":
            self.breadcrumbs(tmpl, dir, True)
            row['raw'] = 'raw?dir=' + dir.replace('#', '%23')

    def breadcrumbs(self, tmpl, dir, islog):
        folders = dir.split('/')
        crumbs = ['<a href="">logs / </a>']

        row = tmpl.AddRow("BreadcrumbLoop")
        row["crumbtext"] = "logs"
        row["crumburl"] = ""
        for i in range(0, len(folders)):
            if folders[i]:
                row = tmpl.AddRow("BreadcrumbLoop")
                row["crumbtext"] = folders[i]
                url = '/'.join(folders[0:i+1])
                url = url.replace('#', '%23')
                row["crumburl"] = url
                if i == len(folders) - 1 and islog:
                    row["islog"] = "True"

    def getbase(self, sock):
        base = znc.CZNC.Get().GetZNCPath()
        user = sock.GetUser()
        scope = self.nv[user]
        if scope == "Global":
            base = base + '/moddata/log/' + user + '/'
        elif scope == "User":
            base = base + '/users/' + user + '/moddata/log/'
        else:
            base = base + '/users/' + user + '/networks/' + self.nv[user] + '/moddata/log/'

        return base

    def getscopes(self, sock, tmpl):
        user_string = sock.GetUser()
        user = znc.CZNC.Get().FindUser(user_string)
        networks = user.GetNetworks()
        net_array = []
        for network in networks:
            net_array.append(network.GetName())
        net_array = sorted(net_array)
        net_array.insert(0, 'User'); net_array.insert(0, 'Global')
        for net in net_array:
            row = tmpl.AddRow("ScopeLoop")
            try:
                if net == self.nv[user_string]:
                    row["active"] = "True"
            except KeyError:
                pass
            row["network"] = net

    def setscope(self, scope, sock, tmpl):
        user = sock.GetUser()
        self.nv[user] = scope
        row = tmpl.AddRow("MessageLoop")
        row["message"] = "Scope successfully set."
