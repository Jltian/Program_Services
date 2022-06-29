# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import h5py
import os


class H5Group(object):

    def __init__(self, bind: h5py.Group):
        self.bind = bind
        print(type(self.bind.file))
        print(type(self.bind))

    def write(self, data):
        from pandas import DataFrame
        if isinstance(data, DataFrame):
            self.__write_dataframe__(data)
        else:
            raise NotImplementedError('{}\n{}'.format(type(data), data))
        self.bind.file.flush()

    def __write_dataframe__(self, data):
        from pandas import DataFrame
        assert isinstance(data, DataFrame), type(data)
        print(data.head())
        print([str(var) for var in data.index])
        self.bind.create_dataset(name='index', dtype='S100', data=[str(var) for var in data.index])
        for tag in data.columns:
            assert tag != 'index', data.head()
            self.bind.create_dataset(tag, data=data[tag].values)
        self.bind.attrs['source_data_type'] = 'DataFrame'

    def read_as_pd(self):
        from pandas import DataFrame
        assert self.bind.attrs['source_data_type'] == 'DataFrame'
        content_dict = dict()
        for key, value in self.bind.items():
            content_dict[key] = value
        index_col = content_dict.pop('index')
        return DataFrame(index=index_col, data=content_dict)


class H5File(object):

    def __init__(self, file_path: str):
        assert file_path.endswith('.h5'), 'Error HDF5 file path: {}'.format(file_path)
        file_folder = os.path.sep.join(file_path.split(os.path.sep)[:-1])
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        self.__file_path__ = file_path
        self.__data__ = h5py.File(file_path, 'a')

    def get(self, name: str):
        return H5Group(self.__data__[name])

    def create_group(self, name: str):
        try:
            new_group = self.__data__.create_group(name)
            self.__data__.flush()
            return H5Group(new_group)
        except ValueError:
            new_group = self.get(name)
            return new_group

    def clear(self):
        self.__data__.clear()
        self.__data__.flush()

    def close(self):
        self.__data__.close()


if __name__ == '__main__':
    from WindPy import w
    w.start()
    file = H5File(r'C:\Users\Administrator\Downloads\test.h5')
    group = file.create_group('2019-10-18')
    group.write(w.wsi("510300.SH", "low,high,open,close,volume,amt", "2019-10-18 00:00:00", "2019-10-18 23:59:59", "Fill=Previous", usedf=True)[1])
    file.close()
