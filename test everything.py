from collections import defaultdict

# 数据：(类别, 值)
data = [('水果', '苹果'), ('水果', '香蕉'), ('蔬菜', '胡萝卜'), ('水果', '橙子')]

# 创建默认值为列表的字典
mp = defaultdict(list)
print(mp)

# 直接追加，无需判断键是否存在
for category, item in data:
    mp[category].append(item)
    print(dict(mp))

print(f'[dict(mp)]: {dict(mp)}')
# 输出：{'水果': ['苹果', '香蕉', '橙子'], '蔬菜': ['胡萝卜']}