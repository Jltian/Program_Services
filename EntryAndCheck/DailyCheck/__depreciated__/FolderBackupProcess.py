# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import os
import shutil


def back_up_folder(folder_for_back: str, path_store: str, target_folder_name: str = None):
    if target_folder_name is None:
        target_folder_name = folder_for_back.split(os.path.sep)[-1]
    else:
        pass
    target_folder = os.path.join(path_store, target_folder_name)
    os.makedirs(target_folder, exist_ok=True)
    for root, sub_root_list, file_list in os.walk(folder_for_back):
        # print(root.replace(folder_for_back, '').strip('\\'), sub_root_list, file_list)
        sub_folder_name = root.split(os.path.sep)[-1]
        if sub_folder_name.startswith('.'):
            continue
        sub_folder = os.path.join(target_folder, root.replace(folder_for_back, '').strip('\\'))
        os.makedirs(sub_folder, exist_ok=True)
        for file in file_list:
            if file.startswith('.'):
                continue
            now_source_file = os.path.join(root, file)
            now_target_file = os.path.join(sub_folder, file)
            if os.path.exists(now_target_file):
                if os.stat(now_source_file).st_mtime > os.stat(now_target_file).st_mtime:
                    os.remove(now_target_file)
                    shutil.copy(os.path.join(root, file), sub_folder)
                    print('更新 {}'.format(now_target_file))
                else:
                    pass
            else:
                shutil.copy(os.path.join(root, file), sub_folder)
                print('备份 {}'.format(now_target_file))


if __name__ == '__main__':
    back_up_folder(
        folder_for_back=r'W:\\',
        path_store=r'C:\Documents',
        target_folder_name='基金会计数据备份'
    )
