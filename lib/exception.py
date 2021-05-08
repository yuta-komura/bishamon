class ConfigException(Exception):

    def __init__(self):
        msg = "Please specify your valid config."
        super(ConfigException, self).__init__(msg)


class MysteriousException(Exception):

    def __init__(self):
        msg = "Mysterious !!!"
        super(MysteriousException, self).__init__(msg)


class SingletonException(Exception):

    def __init__(self):
        msg = "This is singleton class."
        super(SingletonException, self).__init__(msg)
