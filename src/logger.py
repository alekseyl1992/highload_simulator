
class Logger:
    def __init__(self, *allowed_source_class_names):
        self.allowed_source_class_names = allowed_source_class_names

    def log(self, source_object, message):
        if source_object.__class__.__name__ in self.allowed_source_class_names:
            print(message)