#ifndef SAMPLE_MODULE_H
#define SAMPLE_MODULE_H

#include <vector>
#include <string>
#include <map>
#include <stdexcept>

/**
 * @file sample_module.h
 * @brief 样本C++模块头文件，用于测试文档生成器。
 * 
 * 这个头文件包含了各种C++代码结构，包括类、结构体、
 * 模板、命名空间和Doxygen风格注释。
 * 
 * @author Test Author
 * @version 1.0.0
 * @since 1.0.0
 */

namespace sample {

/**
 * @brief 一个简单的计算器类，支持基本的数学运算。
 * 
 * 这个类展示了如何使用C++的类和方法，
 * 以及各种类型的Doxygen标签。
 * 
 * @see MathUtil
 */
class Calculator {
private:
    int precision;      ///< 计算结果的小数位数
    double memory;      ///< 内存存储值

public:
    /**
     * @brief 初始化计算器。
     * 
     * @param precision 计算结果的小数位数，默认为2
     */
    explicit Calculator(int precision = 2);

    /**
     * @brief 两个数相加。
     * 
     * @param a 第一个加数
     * @param b 第二个加数
     * @return 两数之和
     * 
     * @code
     * Calculator calc;
     * double result = calc.add(2, 3); // returns 5.0
     * @endcode
     */
    double add(double a, double b) const;

    /**
     * @brief 两个数相除。
     * 
     * @param a 被除数
     * @param b 除数
     * @return 两数之商
     * @throws std::runtime_error 当除数为0时抛出
     * 
     * @code
     * Calculator calc;
     * double result = calc.divide(10, 2); // returns 5.0
     * @endcode
     */
    double divide(double a, double b) const;

    /**
     * @brief 获取当前内存中的值。
     * @return 内存中的值
     */
    double getMemory() const;

    /**
     * @brief 设置内存中的值。
     * @param value 要存储的值
     */
    void setMemory(double value);
};

/**
 * @brief 数学工具类，提供常用的数学函数。
 */
class MathUtil {
public:
    /**
     * @brief 生成斐波那契数列。
     * 
     * @param n 要生成的数列长度
     * @return 斐波那契数列
     * @throws std::invalid_argument 当n小于0时抛出
     */
    static std::vector<int> fibonacci(int n);
};

/**
 * @brief 用户结构体。
 */
struct User {
    int id;             ///< 用户ID
    std::string name;   ///< 用户名
    std::string email;  ///< 用户邮箱
};

/**
 * @brief 用户角色枚举。
 */
enum class Role {
    USER,   ///< 普通用户
    ADMIN,  ///< 管理员
    GUEST   ///< 访客
};

/**
 * @brief 模板类示例。
 * 
 * @tparam T 元素类型
 */
template<typename T>
class Container {
private:
    std::vector<T> items;

public:
    /**
     * @brief 添加元素到容器。
     * @param item 要添加的元素
     */
    void add(const T& item) {
        items.push_back(item);
    }

    /**
     * @brief 获取容器大小。
     * @return 元素数量
     */
    size_t size() const {
        return items.size();
    }
};

/**
 * @brief 生成问候语。
 * 
 * @param name 要问候的人的名字
 * @param greeting 问候语，默认为"Hello"
 * @return 完整的问候语字符串
 */
std::string greet(const std::string& name, const std::string& greeting = "Hello");

/**
 * @brief 异步获取数据（示例）。
 * 
 * @param url 数据的URL地址
 * @param timeout 超时时间（秒），默认为30
 * @return 解析后的JSON数据映射
 * @throws std::runtime_error 当请求超时时抛出
 */
std::map<std::string, std::string> fetchData(const std::string& url, int timeout = 30);

} // namespace sample

#endif // SAMPLE_MODULE_H
