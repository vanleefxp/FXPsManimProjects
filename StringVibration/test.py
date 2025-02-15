import numpy as np

# 定义函数 f
def f(x):
    if x < 0.5:
        return 2 * x
    else:
        return 2 - 2 * x

# 使用 np.vectorize 转换为 ufunc
vectorized_f = np.vectorize(f)

# 测试用 np.linspace 生成的数组
x_values = np.linspace(0, 1, 100)
result = vectorized_f(x_values)

# 输出结果
print(result)
