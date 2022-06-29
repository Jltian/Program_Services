# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import logging
import pickle
import os
import time

from collections.abc import Iterable, Mapping, Sized


class BasePersist(object):
    __p_type__ = 'None'
    __ignore_prefix__ = ('.', '_', '$')

    def __init__(self, data_path=None, keep_history=False):
        if data_path is None:
            logging.debug('initiating {} into path {}'.format(self.__class__.__name__, os.getcwd()))
            self.__path__ = os.path.join(os.getcwd(), self.__time_index__)
        elif isinstance(data_path, str):
            logging.debug('initiating {} from path {}'.format(self.__class__.__name__, data_path))
            self.__path__ = data_path
        else:
            raise TypeError

        __ptype_path__ = os.path.join(data_path, '__ptype__')
        if os.path.exists(data_path):
            try:
                hist_ptype = pickle.load(open(__ptype_path__, 'rb'))
                if hist_ptype == self.__p_type__:
                    pass
                else:
                    assert keep_history is False, repr(FileExistsError)
            except FileNotFoundError:
                pass
            if keep_history is True:
                pass
            else:
                self.clear()
        else:
            os.makedirs(data_path)
        pickle.dump(self.__p_type__, open(__ptype_path__, 'wb'))

    @classmethod
    def init_from(cls, *args, **kwargs):
        raise NotImplementedError

    def __repr__(self):
        """ Return repr(self). """
        return '{}: ['.format(self.__class__.__name__) + ', '.join(
            [str(self.__read__(file)) for file in self.__file_list__()]
        ) + ']'

    def __contains__(self, value):
        """ Return key in self. """
        for file in self.__file_list__():
            if self.__read__(file) == value:
                return True
        return False

    def __iter__(self):
        """ Implement iter(self). """
        for tag in self.__file_list__():
            yield self.__read__(tag)

    def __len__(self):
        return len(list(self.__file_list__()))

    @property
    def __time_index__(self):
        return str(int(time.time() * 100000000))

    def __pjoin__(self, name: str):
        return os.path.join(self.__path__, name)

    def __fcheck__(self, name: str):
        if len(name) > 0:
            return name[0] not in self.__ignore_prefix__
        else:
            raise ValueError('file name is empty.')

    def __fexists__(self, name: str):
        assert name[0] not in self.__ignore_prefix__
        return os.path.exists(self.__pjoin__(name))

    def __file_list__(self):
        for file in os.listdir(self.__path__):
            if self.__fcheck__(file):
                yield file

    def __read__(self, name: str):
        assert name[0] not in self.__ignore_prefix__, str(ValueError)
        return pickle.load(open(self.__pjoin__(name), 'rb'))

    def __write__(self, name: str, obj):
        assert name[0] not in self.__ignore_prefix__, repr(ValueError)
        pickle.dump(obj, open(self.__pjoin__(name), 'wb'))

    def __rename__(self, from_name: str, to_name: str):
        os.rename(self.__pjoin__(from_name), self.__pjoin__(to_name))

    def __remove__(self, name: str):
        os.remove(self.__pjoin__(name))

    def clear(self):
        """ obj.clear() -> None -- remove all items from obj """
        for file in self.__file_list__():
            if os.path.isfile(self.__pjoin__(file)):
                os.remove(self.__pjoin__(file))
            elif os.path.isdir(self.__pjoin__(file)):
                pass
            else:
                continue

    def clean(self):
        for file in os.listdir(self.__path__):
            os.remove(self.__pjoin__(file))
        os.rmdir(self.__path__)


class Plist(BasePersist, Iterable, Sized):
    __p_type__ = 'plist'

    def __init__(self, data_path=None, keep_history=False):
        BasePersist.__init__(self, data_path, keep_history)

    @classmethod
    def init_from(cls, inst, data_path=None, keep_history=False):
        from collections import Iterable
        if isinstance(inst, Iterable):
            new_cls = cls(data_path, keep_history)
            new_cls.extend(inst)
            return new_cls
        else:
            raise TypeError('inst is not iterable')

    def append(self, p_object):
        """ L.append(object) -> None -- append object to end """
        self.__write__(str(self.__len__()), p_object)

    def copy(self):
        """ L.copy() -> list -- a shallow copy of L """
        return [self.__read__(file) for file in self.__file_list__()]

    def count(self, value):
        """ L.count(value) -> integer -- return number of occurrences of value """
        count = 0
        for file in self.__file_list__():
            if self.__read__(file) == value:
                count += 1
        return count

    def extend(self, iterable):
        """ L.extend(iterable) -> None -- extend list by appending elements from the iterable """
        for item in iterable:
            self.append(item)

    def index(self, value, start=None, stop=None):
        """
        L.index(value, [start, [stop]]) -> integer -- return first index of value.
        Raises ValueError if the value is not present.
        """
        s = start if isinstance(start, int) else 0
        e = stop if isinstance(stop, int) else self.__len__()
        for i in range(s, e):
            if self.__getitem__(i) == value:
                return i
        raise ValueError

    def insert(self, index, p_object):
        """ L.insert(index, object) -- insert object before index """
        for i in range(index, self.__len__(), -1):
            self.__rename__(str(i), str(i+1))
        self.__write__(str(index), p_object)

    def pop(self, index=None):
        """
        L.pop([index]) -> item -- remove and return item at index (default last).
        Raises IndexError if list is empty or index is out of range.
        """
        if index is None:
            r_i = self.__len__() - 1
        elif isinstance(index, int):
            r_i = index
        else:
            raise TypeError
        try:
            value = self.__getitem__(r_i)
            self.__remove__(str(r_i))
            for i in range(r_i, self.__len__()):
                self.__rename__(str(i + 1), str(i))
            return value
        except FileNotFoundError:
            raise IndexError

    def remove(self, value):
        """
        L.remove(value) -> None -- remove first occurrence of value.
        Raises ValueError if the value is not present.
        """
        this_index = self.index(value)
        self.__remove__(str(this_index))
        for i in range(this_index, self.__len__()):
            self.__rename__(str(i+1), str(i))

    def reverse(self):
        """ L.reverse() -- reverse *IN PLACE* """
        raise NotImplementedError

    def sort(self, key=None, reverse=False):
        """ L.sort(key=None, reverse=False) -> None -- stable sort *IN PLACE* """
        rule = key if key is not None else lambda x: x
        if key is None:
            for i in range(self.__len__()):
                for j in range(i, self.__len__()):
                    if reverse is False:
                        if rule.__call__(self.__getitem__(i)) > rule.__call__(self.__getitem__(j)):
                            self.__rename__(str(j), 'temp')
                            self.__rename__(str(i), str(j))
                            self.__rename__('temp', str(i))
                    else:
                        if rule.__call__(self.__getitem__(i)) < rule.__call__(self.__getitem__(j)):
                            self.__rename__(str(j), 'temp')
                            self.__rename__(str(i), str(j))
                            self.__rename__('temp', str(i))

    def get(self, k: int, d=None):
        try:
            return self.__getitem__(k)
        except IndexError:
            return d

    def set(self, k: int, v):
        self.__setitem__(k, v)

    def __adjust_index__(self, index: int):
        if index < 0:
            return self.__adjust_index__(self.__len__()+index)
        elif index >= self.__len__():
            raise KeyError
        else:
            return index

    def __delitem__(self, index: int):
        """ Delete self[key]. """
        self.__remove__(str(index))
        for i in range(index, self.__len__()):
            self.__rename__(str(i + 1), str(i))

    def __eq__(self, value):
        """ Return self==value. """
        if isinstance(value, (list, Plist)):
            if self.__len__() == len(value):
                for i in range(self.__len__()):
                    if self[i] != value[i]:
                        return False
                return True
            else:
                return False
        else:
            return False

    # def __getattribute__(self, *args, **kwargs):
    #     """ Return getattr(self, name). """
    #     pass

    def __getitem__(self, y: int):
        """ x.__getitem__(y) <==> x[y] """
        this_i = self.__adjust_index__(y)
        try:
            return self.__read__(str(this_i))
        except FileNotFoundError:
            raise IndexError

    def __reversed__(self):
        """ L.__reversed__() -- return a reverse iterator over the list """
        for i in range(0, self.__len__(), -1):
            yield self.__getitem__(i)

    def __setitem__(self, key: int, value):
        """ Set self[key] to value. """
        this_i = self.__adjust_index__(key)
        try:
            self.__write__(str(this_i), value)
        except FileNotFoundError:
            raise KeyError


class Pdict(BasePersist, Mapping, Sized):
    __ptype__ = 'pdict'

    def __init__(self, data_path=None, keep_history=True):
        BasePersist.__init__(self, data_path, keep_history)

    @classmethod
    def init_from(cls, inst, data_path=None, keep_history=False):
        from collections import Mapping
        if isinstance(inst, Mapping):
            new_cls = cls(data_path, keep_history)
            for key in inst:
                new_cls.__setitem__(key, inst[key])
            return new_cls
        else:
            raise TypeError('inst is not mapping.')

    def __repr__(self):
        """ Return repr(self). """
        return '{}: {'.format(self.__class__.__name__) + str({
            file: self.__read__(file) for file in self.__file_list__()
        }) + '}'

    def copy(self):
        """ D.copy() -> a shallow copy of D """
        return {file: self.__read__(file) for file in self.__file_list__()}

    def get(self, k: str, d=None):
        """ D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None. """
        try:
            return self.__getitem__(k)
        except KeyError:
            return d

    def set(self, k: str, v):
        self.__setitem__(k, v)

    def items(self):
        """ D.items() -> a set-like object providing a view on D's items """
        for file in self.__file_list__():
            yield file, self.__read__(file)

    def keys(self):
        """ D.keys() -> a set-like object providing a view on D's keys """
        for file in self.__file_list__():
            yield file

    def pop(self, k: str, d=None):
        """
        D.pop(k[,d]) -> v, remove specified key and return the corresponding value.
        If key is not found, d is returned if given, otherwise KeyError is raised
        """
        try:
            value = self.__getitem__(k)
            self.__remove__(k)
            return value
        except FileNotFoundError:
            if d is not None:
                return d
            else:
                raise KeyError

    def update(self, arg=None, **kwargs):
        """
        D.update([E, ]**F) -> None.  Update D from dict/iterable E and F.
        If E is present and has a .keys() method, then does:  for k in E: D[k] = E[k]
        If E is present and lacks a .keys() method, then does:  for k, v in E: D[k] = v
        In either case, this is followed by: for k in F:  D[k] = F[k]
        """
        from collections import Mapping
        if isinstance(arg, Mapping):
            for tag in arg:
                self.__setitem__(tag, arg[tag])
        elif len(kwargs) > 0:
            for tag in kwargs:
                self.__setitem__(tag, kwargs[tag])
        else:
            raise TypeError

    def values(self):
        """ D.values() -> an object providing a view on D's values """
        for file in self.__file_list__():
            yield self.__getitem__(file)

    def __contains__(self, tag: str):
        return self.__fexists__(tag)

    def __delitem__(self, key: str):
        """ Delete self[key]. """
        try:
            self.__remove__(key)
        except FileNotFoundError as e:
            raise KeyError(e.args)

    def __getitem__(self, y: str):
        """ x.__getitem__(y) <==> x[y] """
        try:
            return self.__read__(y)
        except FileNotFoundError:
            raise KeyError

    def __setitem__(self, key: str, value):
        """ Set self[key] to value. """
        self.__write__(key, value)


class Pset(BasePersist, Iterable, Sized):
    __ptype__ = 'pset'

    def __init__(self, data_path=None, keep_history=False):
        BasePersist.__init__(self, data_path, keep_history)

    @classmethod
    def init_from(cls, inst, data_path=None, keep_history=False):
        from collections import Iterable
        if isinstance(inst, Iterable):
            new_cls = cls(data_path, keep_history)
            for item in inst:
                new_cls.add(item)
            return new_cls
        else:
            raise TypeError('inst is not iterable.')

    def add(self, element):
        """
        Add an element to a set.

        This has no effect if the element is already present.
        """
        self.__write__(str(time.time()), element)

    def copy(self):
        """ Return a shallow copy of a set. """
        return set([self.__read__(file) for file in self.__file_list__()])

    def discard(self, element):
        """
        Remove an element from a set if it is a member.

        If the element is not a member, do nothing.
        """
        for file in self.__file_list__():
            if self.__read__(file) == element:
                self.__remove__(file)
                return

    def pop(self, *args, **kwargs):
        """
        Remove and return an arbitrary set element.
        Raises KeyError if the set is empty.
        """
        raise NotImplementedError

    def remove(self, element):
        """
        Remove an element from a set; it must be a member.

        If the element is not a member, raise a KeyError.
        """
        for file in self.__file_list__():
            if self.__read__(file) == element:
                self.__remove__(file)
                return
        raise KeyError

    def __contains__(self, y):
        """ x.__contains__(y) <==> y in x. """
        for file in self.__file_list__():
            if self.__read__(file) == y:
                return True
        return False

    def __iter__(self):
        for file in self.__file_list__():
            yield self.__read__(file)


class PqueueFIFO(BasePersist, Sized):
    """FIFO Queue"""
    __ptype__ = 'deque'

    def __init__(self, data_path=None, keep_history=False, max_length=None):
        BasePersist.__init__(self, data_path, keep_history=keep_history)

        if isinstance(max_length, (type(None), int)):
            self.__max_length__ = max_length
        else:
            raise TypeError

    @classmethod
    def init_from(cls, inst, data_path=None, keep_history=False, max_length=None):
        from collections import Iterable
        assert isinstance(inst, Iterable)
        new_q = cls(data_path, keep_history=keep_history, max_length=max_length)
        for item in inst:
            new_q.put(item)
        return new_q

    def __min_name__(self):
        return str(min([int(var) for var in self.__file_list__()]))

    def __max_name__(self):
        return str(max([int(var) for var in self.__file_list__()]))

    def put(self, value):
        if self.full():
            raise IndexError
        else:
            self.__write__(self.__time_index__, value)

    def top(self):
        return self.__read__(self.__min_name__())

    def bottom(self):
        return self.__read__(self.__max_name__())

    def get(self):
        top_name = self.__min_name__()
        q_value = self.__read__(top_name)
        self.__remove__(top_name)
        return q_value

    def empty(self):
        return self.__len__() == 0

    def full(self):
        if self.__max_length__ is None:
            return False
        else:
            if self.__len__() < self.__max_length__:
                return False
            else:
                return True

    def size(self):
        return self.__len__()


class PqueueLIFO(PqueueFIFO, Sized):

    def top(self):
        return self.__read__(self.__max_name__())

    def bottom(self):
        return self.__read__(self.__min_name__())

    def get(self):
        top_name = self.__max_name__()
        q_value = self.__read__(top_name)
        self.__remove__(top_name)
        return q_value


if __name__ == '__main__':
    pass
