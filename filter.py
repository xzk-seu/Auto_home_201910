import os
import json

"""
删除帖子内容文件中，一个文件贴子数小于60的（完整的应为100）
"""


def delete_file(dir_path, delete_list):
    for f in delete_list:
        f_path = os.path.join(dir_path, f)
        os.remove(f_path)


def run():
    path = os.path.join(os.getcwd(), 'content')
    car_type_list = os.listdir(path)
    for n, c in enumerate(car_type_list):
        print('%d for %s' % (n, c))
    car_type = int(input('input car type: '))
    dir_path = os.path.join(path, car_type_list[car_type])
    file_list = os.listdir(dir_path)
    print(file_list)
    delete_list = list()
    for f in file_list:
        f_path = os.path.join(dir_path, f)
        with open(f_path, 'r', encoding='utf-8') as fr:
            data = json.load(fr)
        if len(data) < 60:
            delete_list.append(f)
    print(delete_list)
    print(len(delete_list))
    delete_file(dir_path, delete_list)


if __name__ == '__main__':
    run()
