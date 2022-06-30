# -*- encoding: UTF-8 -*-
import datetime

from core.Environment import Environment
from core.Generator import EntryGenerator

env_inst = Environment()
env_inst.product_range = (  # 非托管的产品范围 手动调整即运行顺序，运行顺序与互相嵌套有关
    '久铭2号',  # jm1
    '久铭3号',  # jm1
    '收益1号',  # wj22
    '稳健2号',
    '稳健3号',
    '稳健5号',
    '稳健7号',#长江两融
    '稳健9号',  # jm1

    '稳健12号',
    '稳健15号',
    '稳健16号',
    '稳健19号',
    '稳健21号',
    '稳利2号',  # wj1
    '双盈1号',
)
# ## '稳健6号', ## '稳健8号', ## '稳健31号', ## '稳健32号', ## '稳健33号', # '全球1号', # '稳健17号',# #'稳健18号',# '稳健10号',
#     '稳健11号', '稳健10号',
#    '稳健11号',

entry_gen = EntryGenerator(datetime.date(2022, 6, 28))
env_inst.deploy_entry_generator(entry_gen)

try:
    for p_str in env_inst.product_range:
        entry_gen.run_product(p_str)
    entry_gen.save_to_db()

finally:
    env_inst.exit()
