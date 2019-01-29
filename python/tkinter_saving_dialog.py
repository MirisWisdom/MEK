try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk


class SavingDialog(tk.Toplevel):
    def __init__(self, master, tag=None, *args, **kwargs):
        tk.Toplevel.__init__(self, master, *args, **kwargs)

        self.title('Saving, please wait...')
        self.minsize(width=300, height=0)
        self.protocol("WM_DELETE_WINDOW", self.hide)

        self.transient(master)

        self.geometry('%sx%s' % (300, 0))
        self.update()

    def show(self):
        if self.state() == 'withdrawn':
            self.center_on_master()
            self.update()
            self.deiconify()
            self.grab_set()

    def hide(self):
        if self.state() != 'withdrawn':
            self.withdraw()
            self.grab_release()
            self.update()

    def center_on_master(self, x=0, y=0):
        x_base, y_base = self.master.winfo_x(), self.master.winfo_y()
        m_width, m_height = self.master.geometry().split('+')[0].split('x')[:2]
        s_width, s_height = self.geometry().split('+')[0].split('x')[:2]

        m_width, m_height = int(m_width), int(m_height)
        s_width, s_height = int(s_width), int(s_height)

        if m_width == 1 and m_height == 1:
            m_width, m_height = (self.master.winfo_reqwidth(),
                                 self.master.winfo_reqheight())

        if s_width == 1 and s_height == 1:
            s_width, s_height = self.winfo_reqwidth(), self.winfo_reqheight()

        self.geometry('%sx%s+%s+%s' % (
            s_width, s_height,
            x_base + ((m_width  - s_width)  // 2),
            y_base + ((m_height - s_height) // 2)
            ))
