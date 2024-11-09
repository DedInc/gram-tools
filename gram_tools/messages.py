from string import Template

class T(Template):
    def text(self, *args, **kwargs):
        return self.substitute(*args, **kwargs)
