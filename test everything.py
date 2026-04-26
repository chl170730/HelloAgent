from collections import defaultdict

# Data: (category, value)
data = [('Fruit', 'Apple'), ('Fruit', 'Banana'), ('Vegetable', 'Carrot'), ('Fruit', 'Orange')]

# Create a dictionary with default value as list
grouped_data = defaultdict(list)

# Append directly without checking if the key exists
for category, item in data:
    grouped_data[category].append(item)

# Convert back to normal dict if necessary
result = dict(grouped_data)

# Output: {'Fruit': ['Apple', 'Banana', 'Orange'], 'Vegetable': ['Carrot']}
print(result)
