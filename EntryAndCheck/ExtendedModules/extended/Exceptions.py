# -*- encoding: UTF-8 -*-


class ParamTypeError(TypeError):
    def __init__(self, param_name: str, param_target_type, param):
        self.name = param_name
        self.got_type = str(type(param))
        if isinstance(param_target_type, str):
            self.target_type = param_target_type
        elif isinstance(param_target_type, (list, tuple, set, frozenset)):
            target_type_list = list()
            for item in param_target_type:
                if isinstance(item, str):
                    target_type_list.append(item)
                elif isinstance(item, type):
                    target_type_list.append(item.__name__)
                else:
                    raise NotImplementedError()
            self.target_type = '/'.join(target_type_list)
        elif isinstance(param_target_type, type):
            self.target_type = param_target_type.__name__
        else:
            raise TypeError

    def __repr__(self):
        return 'param {0:s} expect type {1:s} but got type {2:s}'.format(
            self.name, self.target_type, self.got_type,
        )


class ParamOutOfRangeError(ValueError):
    def __init__(self, param_name: str, value_range, param):
        self.name = param_name
        if isinstance(value_range, tuple):
            if len(value_range) == 2:
                self.range = '{} to {}'.format(value_range[0], value_range[1])
            else:
                raise ValueError
        elif isinstance(value_range, str):
            self.range = value_range
        else:
            raise TypeError
        self.got_value = str(param)

    def __repr__(self):
        return 'param {0:s} should take value in {1:s} but got value {2:s}'.format(
            self.name, self.range, self.got_value,
        )


class ParamNoContentError(ValueError):
    def __init__(self, param_name):
        self.name = repr(param_name)

    def __repr__(self):
        return 'param {0:s} gets no content'.format(self.name)


class ParamMissingError(KeyError):
    def __init__(self, param_name: str):
        self.name = param_name

    def __repr__(self):
        return 'param {0:s} missing'.format(self.name)


class ValueTypeError(ValueError):
    def __init__(self, value_container: str, value_target_type, value):
        self.value_container = value_container
        self.got_type = str(type(value))

        if isinstance(value_target_type, str):
            self.target_type = value_target_type
        elif isinstance(value_target_type, (list, tuple, set, frozenset)):
            target_type_list = list()
            for item in value_target_type:
                if isinstance(item, str):
                    target_type_list.append(item)
                elif isinstance(item, type):
                    target_type_list.append(item.__name__)
                else:
                    raise NotImplementedError()
            self.target_type = '/'.join(target_type_list)
        else:
            raise TypeError

    def __repr__(self):
        return 'value in {0:s} expect type {1:s} but got type {2:s}'.format(
            self.value_container, self.target_type, self.got_type,
        )
